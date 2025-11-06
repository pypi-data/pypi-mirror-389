# SPDX-FileCopyrightText: 2023 CELESTIFYX Team
# SPDX-License-Identifier: GPL-3.0-or-later

import os

from pathlib import Path

from nerve import SysInfo
from nerve.lib.args import (config_handler, Config)
from nerve.lib.configuration import ConfigurationOutput
from nerve.lib.applications.application_handler import application_handler
from nerve.lib.authentication.authentication_handler import auth_handler
from nerve.lib.disk.filesystem import FilesystemHandler
from nerve.lib.disk.utils import disk_layouts
from nerve.lib.global_menu import GlobalMenu
from nerve.lib.installer import (Installer, accessibility_tools_in_use, run_custom_user_commands)
from nerve.lib.interactions.general_conf import (PostInstallationAction, ask_post_installation)
from nerve.lib.models import (Bootloader, LocaleConfiguration, Repository, NetworkConfiguration)
from nerve.lib.models.device import (DiskLayoutType, EncryptionType, BtrfsOptions, SnapshotConfig, SnapshotType, DiskLayoutConfiguration)
from nerve.lib.models.users import User
from nerve.lib.output import (debug, error, info)
from nerve.lib.profile.profiles_handler import profile_handler
from nerve.tui import Tui

def ask_user_questions() -> None:
    """
    First, we'll ask the user for a bunch of user inputs.
    Not until we're satisfied with what we want to install,
    will we continue with the actual installation steps.
    """
    with Tui():
        global_menu: GlobalMenu = GlobalMenu(config_handler.config)

        if not config_handler.args.advanced:
            global_menu.set_enabled(key='parallel_downloads', enabled=False)

        global_menu.run()

def perform_installation(mountpoint: Path) -> None:
    """
    Performs the installation steps on a block device.
    The Only requirement is that the block devices are
    formatted and setup before entering this function.
    """
    info('Starting installation...')
    config: Config = config_handler.config

    if not config.disk_config:
        error("No disk configuration provided")
        return

    disk_config: DiskLayoutConfiguration = config.disk_config
    run_mkinitcpio: bool = not config.uki
    locale_config: LocaleConfiguration | None = config.locale_config
    optional_repositories: list[Repository] = config.mirror_config.optional_repositories if config.mirror_config else []
    mountpoint: Path = disk_config.mountpoint if disk_config.mountpoint else mountpoint

    with Installer(mountpoint, disk_config, kernels=config.kernels) as installation:
        # Mount all the drives to the desired mountpoint
        if disk_config.config_type != DiskLayoutType.Pre_mount:
            installation.mount_ordered_layout()

        installation.sanity_check()

        if (disk_config.config_type != DiskLayoutType.Pre_mount) and disk_config.disk_encryption and (disk_config.disk_encryption.encryption_type != EncryptionType.NoEncryption):
            # generate encryption key files for the mounted luks devices
            installation.generate_key_files()

        if mirror_config := config.mirror_config:
            installation.set_mirrors(mirror_config, on_target=False)

        installation.minimal_installation(optional_repositories=optional_repositories, mkinitcpio=run_mkinitcpio, hostname=config_handler.config.hostname, locale_config=locale_config)

        if mirror_config := config.mirror_config:
            installation.set_mirrors(mirror_config, on_target=True)

        if config.swap:
            installation.setup_swap()

        if config.bootloader and (config.bootloader != Bootloader.NO_BOOTLOADER):
            if (config.bootloader == Bootloader.Grub) and SysInfo.has_uefi():
                installation.add_additional_packages('grub')

            installation.add_bootloader(config.bootloader, config.uki)

        # If the user selected to copy the current ISO network configuration,
        # Perform a copy of the config
        network_config: NetworkConfiguration | None = config.network_config

        if network_config:
            network_config.install_network_config(installation, config.profile_config)

        if config.auth_config and config.auth_config.users:
            installation.create_users(config.auth_config.users)
            auth_handler.setup_auth(installation, config.auth_config, config.hostname)

        if app_config := config.app_config:
            application_handler.install_applications(installation, app_config, config.auth_config.users if config.auth_config else None)

        if profile_config := config.profile_config:
            profile_handler.install_profile_config(installation, profile_config)

        if config.packages and (config.packages[0] != ''):
            installation.add_additional_packages(config.packages)

        if timezone := config.timezone:
            installation.set_timezone(timezone)

        if config.ntp:
            installation.activate_time_synchronization()

        if accessibility_tools_in_use():
            installation.enable_espeakup()

        if config.auth_config and config.auth_config.root_enc_password:
            root_user: User = User('root', config.auth_config.root_enc_password, False)
            installation.set_user_password(root_user)

        if (profile_config := config.profile_config) and profile_config.profile:
            profile_config.profile.post_install(installation)

        # If the user provided a list of services to be enabled, pass the list to the enable_service function.
        # Note that while it's called enable_service, it can actually take a list of services and iterate it.
        if services := config.services:
            installation.enable_service(services)

        if disk_config.has_default_btrfs_vols():
            btrfs_options: BtrfsOptions | None = disk_config.btrfs_options
            snapshot_config: SnapshotConfig | None = btrfs_options.snapshot_config if btrfs_options else None
            snapshot_type: SnapshotType | None = snapshot_config.snapshot_type if snapshot_config else None

            if snapshot_type:
                installation.setup_btrfs_snapshot(snapshot_type, config.bootloader)

        # If the user provided custom commands to be run post-installation, execute them now.
        if cc := config.custom_commands:
            run_custom_user_commands(cc, installation)

        installation.genfstab()
        debug("Disk states after installing:\n" + disk_layouts())

        if not config_handler.args.silent:
            with Tui():
                action: PostInstallationAction = ask_post_installation()

            match action:
                case PostInstallationAction.EXIT:
                    pass

                case PostInstallationAction.REBOOT:
                    os.system('reboot')

                case PostInstallationAction.CHROOT:
                    # noinspection PyBroadException
                    try:
                        installation.drop_to_shell()
                    except Exception:
                        pass

    debug("Disk states after installing:\n" + disk_layouts())

def guided() -> None:
    if not config_handler.args.silent:
        ask_user_questions()

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
            return guided()

    if config_handler.config.disk_config:
        fs_handler: FilesystemHandler = FilesystemHandler(config_handler.config.disk_config)
        fs_handler.perform_filesystem_operations()

    return perform_installation(config_handler.args.mountpoint)

guided()
