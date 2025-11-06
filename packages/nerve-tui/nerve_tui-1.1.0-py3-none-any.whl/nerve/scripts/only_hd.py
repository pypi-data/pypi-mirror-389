# SPDX-FileCopyrightText: 2023 CELESTIFYX Team
# SPDX-License-Identifier: GPL-3.0-or-later

from pathlib import Path

from nerve import (debug, error)
from nerve.lib.args import (config_handler, Config)
from nerve.lib.configuration import ConfigurationOutput
from nerve.lib.disk.filesystem import FilesystemHandler
from nerve.lib.disk.utils import disk_layouts
from nerve.lib.global_menu import GlobalMenu
from nerve.lib.installer import Installer
from nerve.lib.models import DiskLayoutConfiguration
from nerve.tui import Tui

def ask_user_questions() -> None:
    with Tui():
        global_menu: GlobalMenu = GlobalMenu(config_handler.config)
        global_menu.disable_all()

        global_menu.set_enabled(key='language',    enabled=True)
        global_menu.set_enabled(key='disk_config', enabled=True)
        global_menu.set_enabled(key='swap',        enabled=True)
        global_menu.set_enabled(key='__config__',  enabled=True)

        global_menu.run()

def perform_installation(mountpoint: Path) -> None:
    """
    Performs the installation steps on a block device.
    The Only requirement is that the block devices are
    formatted and setup before entering this function.
    """
    config: Config = config_handler.config

    if not config.disk_config:
        error("No disk configuration provided")
        return

    disk_config: DiskLayoutConfiguration = config.disk_config
    mountpoint: Path = disk_config.mountpoint if disk_config.mountpoint else mountpoint

    with Installer(mountpoint, disk_config, kernels=config.kernels) as installation:
        # Mount all the drives to the desired mountpoint
        # This *can* be done outside the installation, but the installer can deal with it.
        installation.mount_ordered_layout()

        # To generate a fstab directory holder. Avoids an error on exit and at the same time checks the procedure
        target: Path = Path(str(mountpoint) + "/etc/fstab")

        if not target.parent.exists():
            target.parent.mkdir(parents=True)

    # For support reasons, we'll log the disk layout post-installation (crash or no crash)
    debug("Disk states after installing:\n" + disk_layouts())

def only_hd() -> None:
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
            return only_hd()

    if config_handler.config.disk_config:
        fs_handler: FilesystemHandler = FilesystemHandler(config_handler.config.disk_config)
        fs_handler.perform_filesystem_operations()

    return perform_installation(config_handler.args.mountpoint)

only_hd()
