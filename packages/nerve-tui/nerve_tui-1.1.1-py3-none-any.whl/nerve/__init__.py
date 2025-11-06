# SPDX-FileCopyrightText: 2023 CELESTIFYX Team
# SPDX-License-Identifier: GPL-3.0-or-later

import importlib
import os
import sys
import traceback
import time

from nerve.lib.args import config_handler
from nerve.lib.disk.utils import disk_layouts
from nerve.lib.network.wifi_handler import wifi_handler
from nerve.lib.packages.packages import check_package_upgrade
from nerve.lib.networking import ping
from nerve.lib.hardware import SysInfo
from nerve.lib.output import (FormattedOutput, debug, error, info, log, warn)
from nerve.lib.pacman import Pacman
from nerve.lib.translationhandler import (Language, tr, translation_handler)
from nerve.tui.curses_menu import Tui
from nerve.tui.ui.components import tui as ttui

def _log_hardware_info() -> None:
    # Log various information about hardware before starting the installation. This might help in troubleshooting
    debug("Hardware model detected: " + SysInfo.sys_vendor() + " " + SysInfo.product_name() + "; UEFI mode: " + str(SysInfo.has_uefi()))
    debug("Processor model detected: " + str(SysInfo.cpu_model()))
    debug("Memory statistics: " + str(SysInfo.mem_available()) + " available out of " + str(SysInfo.mem_total()) + " total installed")
    debug("Virtualization detected: " + str(SysInfo.virtualization()) + "; is VM: " + str(SysInfo.is_vm()))
    debug("Graphics devices detected: " + str(SysInfo.graphics_devices().keys()))

    # For support reasons, we'll log the disk layout pre-installation to match against the post-installation layout
    debug("Disk states before installing:\n" + disk_layouts())

def _check_permissions() -> None:
    if {'--help', '-h'} & set(sys.argv):
        config_handler.print_help()
        sys.exit(0)

    if os.getuid() != 0:
        print(tr("Nerve requires root privileges to run. See --help for more."))
        sys.exit(1)

def _check_online() -> None:
    try:
        ping('1.1.1.1')
    except OSError as ex:
        if 'Network is unreachable' in str(ex) and not config_handler.args.skip_wifi_check and not wifi_handler.setup():
            exit(0)

def _fetch_package_db() -> None:
    """Fetch and sync the package database."""
    from nerve.lib.utils.system_info import SystemInfo

    os_name: str = SystemInfo().os_name
    info("Fetching " + os_name + " package database...")

    try:
        Pacman.run("-Sy")
    except Exception as e:
        message: str = 'Failed to sync ' + os_name + ' package database'
        error(message + '.')

        if 'could not resolve host' in str(e).lower():
            error('Most likely due to a missing network connection or DNS issue.')

        error('Run nerve --debug and check /var/log/nerve/install.log for details.')
        debug(message + ': ' + str(e))

        sys.exit(1)

def check_version_upgrade() -> str | None:
    info('Checking version...')
    upgrade: str | None = check_package_upgrade('nerve')

    if upgrade is None:
        debug('No nerve upgrades found')
        return None

    return tr('New version available') + ': ' + str(upgrade)

def main() -> None:
    _check_permissions()
    _log_hardware_info()

    """
    This can either be run as the compiled and installed application: python setup.py install
    OR straight as a module: python -m nerve
    In any case we will be attempting to load the provided script to be run from the scripts/ folder
    """
    ttui.global_header = 'Nerve'

    if not config_handler.args.offline:
        _check_online()
        _fetch_package_db()

        if not config_handler.args.skip_version_check and (new_version := check_version_upgrade()):
            ttui.global_header = str(ttui.global_header) + ' ' + str(new_version)
            info(new_version)

            time.sleep(3)

    script: str = config_handler.get_script()
    importlib.import_module('nerve.scripts.' + script)  # by loading the module, we'll automatically run the script

def run() -> None:
    exc: Exception | None = None

    try:
        main()
    except Exception as e:
        exc = e
    finally:
        # restore the terminal to the original state
        Tui.shutdown()

        if exc:
            error(''.join(traceback.format_exception(exc)))

            warn((
                'Nerve experienced the above error. If you think this is a bug, please report it to\n' +
                'https://gitlab.com/nerve-dev/nerve and include the log file "/var/log/nerve/install.log".\n\n' +
                'Hint: To extract the log from a live ISO\ncurl -F\'file=@/var/log/nerve/install.log\' https://0x0.st\n'
            ))

        sys.exit(1)

__all__: list[str] = [
    'FormattedOutput',
    'Language',
    'Pacman',
    'SysInfo',
    'Tui',
    'debug',
    'disk_layouts',
    'error',
    'info',
    'log',
    'translation_handler',
    'warn',
    'run'
]
