# SPDX-FileCopyrightText: 2023 CELESTIFYX Team
# SPDX-License-Identifier: GPL-3.0-or-later

import json
import ssl

from typing import Any
from functools import lru_cache
from ssl import SSLContext
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import urlopen
from urllib.response import addinfourl

from nerve.lib.exceptions import (PackageError, SysCallError)
from nerve.lib.models.packages import (AvailablePackage, LocalPackage, PackageSearch, PackageSearchResult, Repository)
from nerve.lib.output import debug
from nerve.lib.pacman import Pacman
from nerve.lib.utils.system_info import SystemInfo

BASE_URL_PKG_SEARCH: str = 'https://archlinux.org/packages/search/json/'
BASE_GROUP_URL:      str = 'https://archlinux.org/groups/search/json/'

def _make_request(url: str, params: dict[str, str]) -> addinfourl:
    ssl_context: SSLContext = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE

    encoded:  str  = urlencode(params)
    full_url: str = url + '?' + encoded

    return urlopen(full_url, context=ssl_context)

def group_search(name: str) -> list[PackageSearchResult]:
    # TODO UPSTREAM: Implement /json/ for the groups search
    try:
        response: addinfourl = _make_request(url=BASE_GROUP_URL, params={'name': name})
    except HTTPError as err:
        return [] if err.code == 404 else err

    # Just to be sure some code didn't slip through the exception
    data: str = response.read().decode()
    return [PackageSearchResult(**package) for package in json.loads(data)['results']]

def package_search(package: str) -> PackageSearch:
    """
    Finds a specific package via the package database.
    It makes a simple web-request, which might be a bit slow.
    """
    # TODO UPSTREAM: Implement bulk search, either support name=X&name=Y or split on space (%20 or ' ')
    # TODO: utilize pacman cache first, upstream second.
    response: addinfourl = _make_request(url=BASE_URL_PKG_SEARCH, params={'name': package})

    if response.code != 200:
        raise PackageError("Could not locate package: [" + str(response.code) + "] " + str(response))

    data: str = response.read().decode()
    json_data: dict[str, Any] = json.loads(data)

    return PackageSearch.from_json(json_data)

def find_package(package: str) -> list[PackageSearchResult]:
    data: PackageSearch = package_search(package)
    results: list[PackageSearchResult] = []

    for result in data.results:
        if result.pkgname == package:
            results.append(result)

    # If we didn't find the package in the search results,
    # odds are it's a group package
    if not results:
        # Check if the package is actually a group
        for result in group_search(package):
            results.append(result)

    return results

def find_packages(*names: str) -> dict[str, PackageSearchResult]:
    """
    Return search results for multiple packages.
    """
    return {package: found for package in names for found in find_package(package)}

def validate_package_list(packages: list[str]) -> tuple[list[str], list[str]]:
    """
    Validates a list of given packages.
    return: Tuple of lists containing valid packavges in the first and invalid
    packages in the second entry
    """
    valid_packages:   set[str] = {package for package in packages if find_package(package)}
    invalid_packages: set[str] = set(packages) - valid_packages

    return list(valid_packages), list(invalid_packages)

def installed_package(package: str) -> LocalPackage | None:
    try:
        package_info: list[str] = []

        for line in Pacman.run('-Q --info ' + package):
            package_info.append(line.decode().strip())

        return _parse_package_output(package_info, LocalPackage)
    except SysCallError:
        pass

    return None

@lru_cache
def check_package_upgrade(package: str) -> str | None:
    try:
        for line in Pacman.run('-Qu ' + package):
            return line.decode().strip()

    except SysCallError:
        debug('Failed to check for package upgrades: ' + package)

    return None

@lru_cache
def list_available_packages(repositories: tuple[Repository, ...]) -> dict[str, AvailablePackage]:
    """
    Returns a list of all available packages in the database
    """
    packages: dict[str, AvailablePackage] = {}
    current_package: list[str] = []
    filtered_repos: list[str] = [name for repo in repositories for name in repo.get_repository_list()]

    try:
        Pacman.run('-Sy')
    except Exception as e:
        debug('Failed to sync ' + SystemInfo().os_name + ' package database: ' + str(e))

    for line in Pacman.run('-S --info'):
        dec_line: str = line.decode().strip()
        current_package.append(dec_line)

        if dec_line.startswith('Validated') and current_package:
            avail_pkg: AvailablePackage = _parse_package_output(current_package, AvailablePackage)

            if avail_pkg.repository in filtered_repos:
                packages[avail_pkg.name] = avail_pkg

            current_package = []

    return packages

@lru_cache(maxsize=128)
def _normalize_key_name(key: str) -> str:
    return key.strip().lower().replace(' ', '_')

def _parse_package_output[PackageType: (
    AvailablePackage,
    LocalPackage
)](package_meta: list[str], cls: type[PackageType]) -> PackageType:
    package: dict[str, str] = {}

    for line in package_meta:
        if ':' in line:
            (key, value) = line.split(sep=':', maxsplit=1)
            key: str = _normalize_key_name(key)

            package[key] = value.strip()

    return cls.model_validate(package)  # type: ignore
