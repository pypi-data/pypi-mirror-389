# SPDX-FileCopyrightText: 2023 CELESTIFYX Team
# SPDX-License-Identifier: GPL-3.0-or-later

import argparse
import json
import os
import sys
import urllib.error
import urllib.parse

from argparse import (ArgumentParser, Namespace)
from dataclasses import (dataclass, field)
from pathlib import Path
from typing import Any
from urllib.request import (Request, urlopen)
from pydantic.dataclasses import dataclass as p_dataclass

from nerve.lib import __packages__
from nerve.lib.translationhandler import tr
from nerve.lib.crypt import decrypt
from nerve.lib.models.application import ApplicationConfiguration
from nerve.lib.models.authentication import AuthenticationConfiguration
from nerve.lib.models.bootloader import Bootloader
from nerve.lib.models.device import (DiskEncryption, DiskLayoutConfiguration)
from nerve.lib.models.locale import LocaleConfiguration
from nerve.lib.models.mirrors import MirrorConfiguration
from nerve.lib.models.network import NetworkConfiguration
from nerve.lib.models.packages import Repository
from nerve.lib.models.profile import ProfileConfiguration
from nerve.lib.models.users import (Password, User, UserSerialization)
from nerve.lib.output import (debug, error, logger, warn)
from nerve.lib.translationhandler import (Language, translation_handler)
from nerve.lib.utils.util import get_password
from nerve.lib.utils.system_info import SystemInfo

@p_dataclass
class Arguments:
    config: Path | None = None
    config_url: str | None = None
    creds: Path | None = None
    creds_url: str | None = None
    creds_decryption_key: str | None = None
    silent: bool = False
    dry_run: bool = False
    script: str | None = None
    mountpoint: Path = Path('/mnt')
    skip_ntp: bool = False
    skip_wkd: bool = False
    skip_boot: bool = False
    debug: bool = False
    offline: bool = False
    no_pkg_lookups: bool = False
    skip_version_check: bool = False
    skip_wifi_check: bool = False
    advanced: bool = False
    verbose: bool = False
    minimal_packages: bool = False

@dataclass
class Config:
    script: str | None = None
    locale_config: LocaleConfiguration | None = None
    language: Language = field(default_factory=lambda: translation_handler.get_language_by_code('en'))
    disk_config: DiskLayoutConfiguration | None = None
    profile_config: ProfileConfiguration | None = None
    mirror_config: MirrorConfiguration | None = None
    network_config: NetworkConfiguration | None = None
    bootloader: Bootloader | None = None
    uki: bool = False
    app_config: ApplicationConfiguration | None = None
    auth_config: AuthenticationConfiguration | None = None
    hostname: str = SystemInfo().os_id
    kernels: list[str] = field(default_factory=lambda: [__packages__[3]])
    ntp: bool = True
    packages: list[str] = field(default_factory=list)
    parallel_downloads: int = 0
    swap: bool = True
    timezone: str = SystemInfo().timezone
    services: list[str] = field(default_factory=list)
    custom_commands: list[str] = field(default_factory=list)

    def unsafe_json(self) -> dict[str, Any]:
        config: dict[str, list[UserSerialization] | str | None] = {}

        if self.auth_config:
            if self.auth_config.users:
                config['users'] = [user.json() for user in self.auth_config.users]

            if self.auth_config.root_enc_password:
                config['root_enc_password'] = self.auth_config.root_enc_password.enc_password

        if self.disk_config:
            disk_encryption: DiskEncryption | None = self.disk_config.disk_encryption

            if disk_encryption and disk_encryption.encryption_password:
                config['encryption_password'] = disk_encryption.encryption_password.plaintext

        return config

    def safe_json(self) -> dict[str, Any]:
        config: dict[str, Any] = {
            'script':             self.script,
            'language':           self.language.json(),
            'hostname':           self.hostname,
            'kernels':            self.kernels,
            'uki':                self.uki,
            'ntp':                self.ntp,
            'packages':           self.packages,
            'parallel_downloads': self.parallel_downloads,
            'swap':               self.swap,
            'timezone':           self.timezone,
            'services':           self.services,
            'custom_commands':    self.custom_commands,
            'bootloader':         self.bootloader.json() if self.bootloader else None,
            'app_config':         self.app_config.json() if self.app_config else None,
            'auth_config':        self.auth_config.json() if self.auth_config else None
        }

        if self.locale_config:
            config['locale_config'] = self.locale_config.json()

        if self.disk_config:
            config['disk_config'] = self.disk_config.json()

        if self.profile_config:
            config['profile_config'] = self.profile_config.json()

        if self.mirror_config:
            config['mirror_config'] = self.mirror_config.json()

        if self.network_config:
            config['network_config'] = self.network_config.json()

        return config

    @classmethod
    def from_config(cls, args_config: dict[str, Any], args: Arguments) -> 'Config':
        config: Config = Config()

        if script := args_config.get('script', None):
            config.script = script

        config.locale_config = LocaleConfiguration.parse_arg(args_config)

        if language := args_config.get('language', None):
            config.language = translation_handler.get_language_by_name(language)

        if disk_config := args_config.get('disk_config', {}):
            enc_password: str = args_config.get('encryption_password', '')
            password: Password | None = Password(plaintext=enc_password) if enc_password else None
            config.disk_config = DiskLayoutConfiguration.parse_arg(disk_config, password)

            # DEPRECATED: backwards compatibility for main level disk_encryption entry
            if args_config.get('disk_encryption', None) is not None and config.disk_config is not None:
                disk_encryption: DiskEncryption | None = DiskEncryption.parse_arg(config.disk_config, args_config['disk_encryption'], Password(plaintext=args_config.get('encryption_password', '')))

                if disk_encryption:
                    config.disk_config.disk_encryption = disk_encryption

        if profile_config := args_config.get('profile_config', None):
            config.profile_config = ProfileConfiguration.parse_arg(profile_config)

        if mirror_config := args_config.get('mirror_config', None):
            backwards_compatible_repo: list[Repository] = []

            if additional_repositories := args_config.get('additional-repositories', []):
                backwards_compatible_repo = [Repository(r) for r in additional_repositories]

            config.mirror_config = MirrorConfiguration.parse_args(mirror_config, backwards_compatible_repo)

        if net_config := args_config.get('network_config', None):
            config.network_config = NetworkConfiguration.parse_arg(net_config)

        if bootloader_config := args_config.get('bootloader', None):
            config.bootloader = Bootloader.from_arg(bootloader_config, args.skip_boot)

        config.uki = args_config.get('uki', False)

        if args_config.get('uki') and (not config.bootloader or not config.bootloader.has_uki_support()):
            config.uki = False

        app_config_args: dict[str, Any] | None = args_config.get('app_config', None)

        if app_config_args is not None:
            config.app_config = ApplicationConfiguration.parse_arg(app_config_args)

        if auth_config_args := args_config.get('auth_config', None):
            config.auth_config = AuthenticationConfiguration.parse_arg(auth_config_args)

        if hostname := args_config.get('hostname', ''):
            config.hostname = hostname

        if kernels := args_config.get('kernels', []):
            config.kernels = kernels

        config.ntp = args_config.get('ntp', True)

        if packages := args_config.get('packages', []):
            config.packages = packages

        if parallel_downloads := args_config.get('parallel_downloads', 0):
            config.parallel_downloads = parallel_downloads

        config.swap = args_config.get('swap', True)

        if timezone := args_config.get('timezone', cls.timezone):
            config.timezone = timezone

        if services := args_config.get('services', []):
            config.services = services

        # DEPRECATED: backwards compatibility
        root_password: Password | None = None

        if _root_password := args_config.get('!root-password', None):
            root_password = Password(plaintext=_root_password)

        if enc_password := args_config.get('root_enc_password', None):
            root_password = Password(enc_password=enc_password)

        if root_password:
            if not config.auth_config:
                config.auth_config = AuthenticationConfiguration()

            config.auth_config.root_enc_password = root_password

        # DEPRECATED: backwards copatibility
        users: list[User] = []

        if args_users := args_config.get('!users', None):
            users = User.parse_arguments(args_users)

        if args_users := args_config.get('users', None):
            users = User.parse_arguments(args_users)

        if users:
            if not config.auth_config:
                config.auth_config = AuthenticationConfiguration()

            config.auth_config.users = users

        if custom_commands := args_config.get('custom_commands', []):
            config.custom_commands = custom_commands

        return config

class ConfigHandler:
    def __init__(self) -> None:
        self._parser: ArgumentParser = self._define_arguments()
        self._args: Arguments = self._parse_args()

        config: dict[str, Any] = self._parse_config()

        try:
            self._config: Config = Config.from_config(config, self._args)
        except ValueError as e:
            warn(str(e))
            sys.exit(1)

    @property
    def config(self) -> Config:
        return self._config

    @property
    def args(self) -> Arguments:
        return self._args

    def get_script(self) -> str:
        return self.args.script or self.config.script or 'guided'

    def print_help(self) -> None:
        self._parser.print_help()

    @staticmethod
    def _define_arguments() -> ArgumentParser:
        parser: ArgumentParser = ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)

        parser.add_argument("--config", type=Path, nargs="?", default=None, help="JSON configuration file")
        parser.add_argument("--config-url", type=str, nargs="?", default=None, help="Url to a JSON configuration file")
        parser.add_argument("--creds", type=Path, nargs="?", default=None, help="JSON credentials configuration file")
        parser.add_argument("--creds-url", type=str, nargs="?", default=None, help="Url to a JSON credentials configuration file")
        parser.add_argument("--creds-decryption-key", type=str, nargs="?", default=None, help="Decryption key for credentials file")
        parser.add_argument("--silent", action="store_true", default=False, help="WARNING: Disables all prompts for input and confirmation. If no configuration is provided, this is ignored")
        parser.add_argument("--dry-run", "--dry_run", action="store_true", default=False, help="Generates a configuration file and then exits instead of performing an installation")
        parser.add_argument("--script", nargs="?", help="Script to run for installation", type=str)
        parser.add_argument("--mountpoint", type=Path, nargs="?", default=Path('/mnt'), help="Define an alternate mount point for installation")
        parser.add_argument("--skip-ntp", action="store_true", help="Disables NTP checks during installation", default=False)
        parser.add_argument("--skip-wkd", action="store_true", help="Disables checking if archlinux keyring wkd sync is complete.", default=False)
        parser.add_argument('--skip-boot', action='store_true', help='Disables installation of a boot loader (note: only use this when problems arise with the boot loader step).', default=False)
        parser.add_argument("--debug", action="store_true", default=False, help="Adds debug info into the log")
        parser.add_argument("--offline", action="store_true", default=False, help="Disabled online upstream services such as package search and key-ring auto update.")
        parser.add_argument("--no-pkg-lookups", action="store_true", default=False, help="Disabled package validation specifically prior to starting installation.")
        parser.add_argument("--skip-version-check", action="store_true", default=False, help="Skip the version check when running Nerve")
        parser.add_argument("--skip-wifi-check", action="store_true", default=False, help="Skip wifi check when running Nerve")
        parser.add_argument("--advanced", action="store_true", default=False, help="Enabled advanced options")
        parser.add_argument("--verbose", action="store_true", default=False, help="Enabled verbose options")
        parser.add_argument("--minimal-packages", action="store_true", default=False, help="Only install the bare minimum packages required for a working system")

        return parser

    def _parse_args(self) -> Arguments:
        argparse_args: dict[str, Any] = vars(self._parser.parse_args())
        args: Arguments = Arguments(**argparse_args)

        # amend the parameters (check internal consistency)
        # Installation can't be silent if config is not passed
        if not args.config and not args.config_url:
            args.silent = False

        if args.debug:
            warn("Warning: --debug mode will write certain credentials to " + str(logger.path) + "!")

        if not args.creds_decryption_key and os.environ.get('NERVE_CREDS_DECRYPTION_KEY'):
            args.creds_decryption_key = os.environ.get('NERVE_CREDS_DECRYPTION_KEY')

        return args

    def _parse_config(self) -> dict[str, Any]:
        config: dict[str, Any] = {}
        config_data: str | None = None
        creds_data: str | None = None

        if self._args.config is not None:
            config_data = self._read_file(self._args.config)
        elif self._args.config_url is not None:
            config_data = self._fetch_from_url(self._args.config_url)

        if config_data is not None:
            config.update(json.loads(config_data))

        if self._args.creds is not None:
            creds_data = self._read_file(self._args.creds)
        elif self._args.creds_url is not None:
            creds_data = self._fetch_from_url(self._args.creds_url)

        if creds_data is not None:
            json_data: dict[str, Any] = self._process_creds_data(creds_data)

            if json_data is not None:
                config.update(json_data)

        config = self._cleanup_config(config)
        return config
    
    def _process_creds_data(self, creds_data: str) -> dict[str, Any] | None:
        if not creds_data.startswith('$'):
            return json.loads(creds_data)

        (key, incorrect_password) = (self._args.creds_decryption_key, False)

        while True:
            try:
                creds_data = decrypt(creds_data, key) if key else decrypt(creds_data, get_password(text=tr('Credentials file decryption password'), header=tr('Incorrect password') if incorrect_password else None, allow_skip=False, skip_confirmation=True).plaintext)
                return json.loads(creds_data)
            except ValueError as err:
                if 'Invalid password' in str(err):
                    if key:
                        error(tr('Incorrect credentials file decryption password'))
                        sys.exit(1)

                    incorrect_password = True

                if not 'Invalid password' in str(err):
                    debug('Error decrypting credentials file: ' + str(err))
                    raise err from err

    @staticmethod
    def _fetch_from_url(url: str) -> str:
        if not urllib.parse.urlparse(url=url).scheme:
            error('Not a valid url')
            sys.exit(1)

        try:
            req: Request = Request(url=url, headers={'User-Agent': 'Nerve'})

            with urlopen(url=req) as resp:
                return resp.read().decode()

        except urllib.error.HTTPError as err:
            error("Could not fetch JSON from " + url + ": " + str(err))
            sys.exit(1)

    @staticmethod
    def _read_file(path: Path) -> str:
        if not path.exists():
            error("Could not find file " + str(path))
            sys.exit(1)

        return path.read_text()

    def _cleanup_config(self, config: Namespace | dict[str, Any]) -> dict[str, Any]:
        clean_args: dict[str, Any] = {}

        for (key, val) in config.items():
            if isinstance(val, dict):
                val = self._cleanup_config(val)

            if val is not None:
                clean_args[key] = val

        return clean_args

config_handler: ConfigHandler = ConfigHandler()
