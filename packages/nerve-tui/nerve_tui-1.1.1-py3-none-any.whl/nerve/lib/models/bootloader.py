# SPDX-FileCopyrightText: 2023 CELESTIFYX Team
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

import sys

from enum import Enum

from nerve.lib.hardware import SysInfo
from nerve.lib.output import warn

class Bootloader(Enum):
    NO_BOOTLOADER = 'No bootloader'
    Systemd       = 'Systemd-boot'
    Grub          = 'Grub'
    Efistub       = 'Efistub'
    Limine        = 'Limine'

    def has_uki_support(self) -> bool:
        match self:
            case Bootloader.Efistub | Bootloader.Limine | Bootloader.Systemd:
                return True

            case _:
                return False

    def json(self) -> str:
        return self.value

    @classmethod
    def get_default(cls) -> Bootloader:
        from nerve.lib.args import config_handler
        return Bootloader.NO_BOOTLOADER if config_handler.args.skip_boot else (Bootloader.Systemd if SysInfo.has_uefi() else Bootloader.Grub)

    @classmethod
    def from_arg(cls, bootloader: str, skip_boot: bool) -> Bootloader:
        # to support old configuration files
        bootloader: str = bootloader.capitalize()
        bootloader_options: list[str] = [e.value for e in Bootloader if (e != Bootloader.NO_BOOTLOADER) or skip_boot]  # type: ignore

        if bootloader not in bootloader_options:
            values: str = ', '.join(bootloader_options)
            warn('Invalid bootloader value "' + str(bootloader) + '". Allowed values: ' + values)

            sys.exit(1)

        return Bootloader(bootloader)
