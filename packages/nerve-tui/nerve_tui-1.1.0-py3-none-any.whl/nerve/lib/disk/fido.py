# SPDX-FileCopyrightText: 2023 CELESTIFYX Team
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

import getpass

from pathlib import Path
from typing import ClassVar

from nerve.lib.models.device import Fido2Device
from nerve.lib.exceptions import SysCallError
from nerve.lib.general import (SysCommand, SysCommandWorker, clear_vt100_escape_codes_from_str)
from nerve.lib.models.users import Password
from nerve.lib.output import (error, info)

class Fido2:
    _loaded_cryptsetup: bool = False
    _loaded_u2f: bool = False
    _cryptenroll_devices: ClassVar[list[Fido2Device]] = []
    _u2f_devices: ClassVar[list[Fido2Device]] = []

    @classmethod
    def get_fido2_devices(cls) -> list[Fido2Device]:
        """
        fido2-tool output example:

        /dev/hidraw4: vendor=0x1050, product=0x0407 (Yubico YubiKey OTP+FIDO+CCID)
        """
        if not cls._loaded_u2f:
            cls._loaded_u2f = True

            try:
                ret: str = SysCommand('fido2-token -L').decode()
            except Exception as e:
                error('failed to read fido2 devices: ' + str(e))
                return []

            fido_devices: str = clear_vt100_escape_codes_from_str(ret)

            if not fido_devices:
                return []

            for line in fido_devices.splitlines():
                (path, details) = line.replace(',', '').split(sep=':', maxsplit=1)
                (_, product, manufacturer) = details.strip().split(sep=' ', maxsplit=2)

                cls._u2f_devices.append(Fido2Device(Path(path.strip()), manufacturer.strip(), product.strip().split('=')[1]))

        return cls._u2f_devices

    @classmethod
    def get_cryptenroll_devices(cls, reload: bool = False) -> list[Fido2Device]:
        """
        Uses systemd-cryptenroll to list the FIDO2 devices
        connected that supports FIDO2.
        Some devices might show up in udevadm as FIDO2 compliant
        when they are, in fact not.

        The drawback of systemd-cryptenroll is that it uses a human-readable format.
        That means we get this unique table like a structure that is of no use.

        So we'll look for `MANUFACTURER` and `PRODUCT`, we take their index,
        and we split each line based on those positions.

        Output example:

        PATH         MANUFACTURER PRODUCT
        /dev/hidraw1 Yubico       YubiKey OTP+FIDO+CCID
        """

        # to prevent continuous reloading which will slow
        # down moving the cursor in the menu
        if not cls._loaded_cryptsetup or reload:
            try:
                ret: str = SysCommand('systemd-cryptenroll --fido2-device=list').decode()
            except SysCallError:
                error('fido2 support is most likely not installed')
                raise ValueError('HSM devices can not be detected, is libfido2 installed?')

            fido_devices: str = clear_vt100_escape_codes_from_str(ret)
            devices: list[Fido2Device] = []

            manufacturer_pos: int = 0
            product_pos:      int = 0

            for line in fido_devices.split('\r\n'):
                if '/dev' not in line:
                    manufacturer_pos = line.find('MANUFACTURER')
                    product_pos      = line.find('PRODUCT')

                    continue

                path:         str = line[:manufacturer_pos].rstrip()
                manufacturer: str = line[manufacturer_pos:product_pos].rstrip()
                product:      str = line[product_pos:]

                devices.append(Fido2Device(Path(path), manufacturer, product))

            cls._loaded_cryptsetup   = True
            cls._cryptenroll_devices = devices

        return cls._cryptenroll_devices

    @classmethod
    def fido2_enroll(cls, hsm_device: Fido2Device, dev_path: Path, password: Password) -> None:
        worker: SysCommandWorker = SysCommandWorker(cmd='systemd-cryptenroll --fido2-device=' + str(hsm_device.path) + ' ' + str(dev_path), peek_output=True)

        pw_inputted:  bool = False
        pin_inputted: bool = False

        while worker.is_alive():
            if not pw_inputted and bytes('please enter current passphrase for disk ' + str(dev_path), 'UTF-8') in worker._trace_log.lower():
                worker.write(bytes(password.plaintext, 'UTF-8'))
                pw_inputted = True
            elif not pin_inputted:
                if bytes('please enter security token pin', 'UTF-8') in worker._trace_log.lower():
                    worker.write(bytes(getpass.getpass(' '), 'UTF-8'))
                    pin_inputted = True

                info('You might need to touch the FIDO2 device to unlock it if no prompt comes up after 3 seconds')
