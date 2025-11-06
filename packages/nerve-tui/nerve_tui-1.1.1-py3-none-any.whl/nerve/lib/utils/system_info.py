# SPDX-FileCopyrightText: 2023 CELESTIFYX Team
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

import sys
import requests

from xml.etree.ElementTree import (fromstring, Element)
from pathlib import Path

from nerve.lib.output import info
from nerve.lib.utils.singleton import Singleton
from nerve.lib.utils.util import (first_existing_path, read_file)

class SystemInfo(Singleton):
    def __init__(self) -> None:
        if not hasattr(self, '_initialized'):
            self._initialized: bool = True

            self._timezone: str = self._get_timezone_from_geoip()
            self._os_info: tuple[str, str] = self._parse_os_release()

    @staticmethod
    def _get_timezone_from_geoip() -> str:
        if '--offline' in sys.argv:
            return 'UTC'

        info("Fetching timezone from GeoIP service...")

        # noinspection PyBroadException
        try:
            response: requests.Response = requests.get(url='https://geoip.kde.org/v1/ubiquity', headers={'User-Agent': 'Nerve'})
            response.raise_for_status()

            root: Element = fromstring(text=response.content) if response.content else None
            return root.findtext(path='TimeZone') if root is not None else 'UTC'
        except Exception:
            return 'UTC'

    @staticmethod
    def _parse_os_release() -> tuple[str, str]:
        release_file: Path | None = first_existing_path([
            '/etc/os-release',
            '/etc/lsb-release',
            '/usr/lib/os-release'
        ])

        os_name: str = 'Unknown OS'
        os_id:   str = 'unknown'

        if release_file and (content := read_file(str(release_file))):
            for line in content.splitlines():
                if '=' not in line:
                    continue

                (key, value) = line.split(sep='=', maxsplit=1)
                value: str = value.strip('"')

                match key:
                    case 'PRETTY_NAME' | 'DISTRIB_DESCRIPTION':
                        os_name = value

                    case 'ID' | 'DISTRIB_ID':
                        os_id = value

        return os_name, os_id

    @property
    def timezone(self) -> str:
        return self._timezone

    @property
    def os_name(self) -> str:
        return self._os_info[0]

    @property
    def os_id(self) -> str:
        return self._os_info[1]
