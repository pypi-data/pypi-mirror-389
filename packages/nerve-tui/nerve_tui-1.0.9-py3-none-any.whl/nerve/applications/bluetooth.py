# SPDX-FileCopyrightText: 2023 CELESTIFYX Team
# SPDX-License-Identifier: GPL-3.0-or-later

from typing import TYPE_CHECKING

from nerve.applications import Application
from nerve.lib.output import debug

if TYPE_CHECKING:
    from nerve.lib.installer import Installer

class BluetoothApplication(Application):
    @property
    def packages(self) -> list[str]:
        return [
            'bluez',
            'bluez-utils'
        ]

    @property
    def services(self) -> list[str]:
        return ['bluetooth.service']

    def install(self, install_session: 'Installer') -> None:
        debug('Installing Bluetooth')

        install_session.add_additional_packages(self.packages)
        install_session.enable_service(self.services)
