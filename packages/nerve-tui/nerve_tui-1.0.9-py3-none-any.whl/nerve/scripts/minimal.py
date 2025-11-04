# SPDX-FileCopyrightText: 2023 CELESTIFYX Team
# SPDX-License-Identifier: GPL-3.0-or-later

from pathlib import Path

from nerve.default_profiles.minimal import MinimalProfile
from nerve.lib.args import (config_handler, Config)
from nerve.lib.configuration import ConfigurationOutput
from nerve.lib.disk.disk_menu import DiskLayoutConfigurationMenu
from nerve.lib.disk.filesystem import FilesystemHandler
from nerve.lib.installer import Installer
from nerve.lib.models import (Bootloader, DiskLayoutConfiguration, NetworkConfiguration)
from nerve.lib.models.profile import ProfileConfiguration
from nerve.lib.models.users import (Password, User)
from nerve.lib.output import (debug, error, info)
from nerve.lib.profile.profiles_handler import profile_handler
from nerve.tui import Tui
from nerve.lib.utils.system_info import SystemInfo

def perform_installation(mountpoint: Path) -> None:
    config: Config = config_handler.config

    if not config.disk_config:
        error("No disk configuration provided")
        return

    disk_config: DiskLayoutConfiguration = config.disk_config
    mountpoint: Path = disk_config.mountpoint if disk_config.mountpoint else mountpoint

    with Installer(mountpoint, disk_config, kernels=config.kernels) as installation:
        # Strap in the base system, add a bootloader and configure
        # some other minor details as specified by this profile and user.
        installation.mount_ordered_layout()
        installation.minimal_installation()
        installation.set_hostname('minimal-' + SystemInfo().os_id)
        installation.add_bootloader(Bootloader.Systemd)

        network_config: NetworkConfiguration | None = config.network_config

        if network_config:
            network_config.install_network_config(installation, config.profile_config)

        installation.add_additional_packages(['nano'])

        profile_config: ProfileConfiguration = ProfileConfiguration(MinimalProfile())
        profile_handler.install_profile_config(installation, profile_config)

        user: User = User('devel', Password(plaintext='devel'), False)
        installation.create_users(user)

    # Once this is done, we output some useful information to the user
    # And the installation is complete.
    info("There are two new accounts in your installation after reboot:")
    info(" * root (password: airoot)")
    info(" * devel (password: devel)")

def minimal() -> None:
    with Tui():
        disk_config: DiskLayoutConfiguration | None = DiskLayoutConfigurationMenu(disk_layout_config=None).run()
        config_handler.config.disk_config = disk_config

    config: ConfigurationOutput = ConfigurationOutput(config_handler.config)
    config.write_debug()
    config.save()

    if config_handler.args.dry_run:
        import sys
        sys.exit(0)

    if not config_handler.args.silent:
        aborted: bool = False

        with Tui():
            if not config.confirm_config():
                debug('Installation aborted')
                aborted = True

        if aborted:
            return minimal()

    if config_handler.config.disk_config:
        fs_handler: FilesystemHandler = FilesystemHandler(config_handler.config.disk_config)
        fs_handler.perform_filesystem_operations()

    return perform_installation(config_handler.args.mountpoint)

minimal()
