# SPDX-FileCopyrightText: 2023 CELESTIFYX Team
# SPDX-License-Identifier: GPL-3.0-or-later

from typing import TYPE_CHECKING

from nerve.applications.bluetooth import BluetoothApplication
from nerve.applications.audio import AudioApplication
from nerve.applications.fonts import FontsApplication
from nerve.applications.shell import ShellApplication
from nerve.lib.models import Audio
from nerve.lib.models.application import ApplicationConfiguration
from nerve.lib.models.users import User

if TYPE_CHECKING:
    from nerve.lib.installer import Installer

class ApplicationHandler:
    def __init__(self) -> None:
        pass

    @staticmethod
    def install_applications(install_session: 'Installer', app_config: ApplicationConfiguration, users: list['User'] | None = None) -> None:
        if app_config.bluetooth_config and app_config.bluetooth_config.enabled:
            BluetoothApplication().install(install_session)

        if app_config.audio_config and (app_config.audio_config.audio != Audio.NO_AUDIO):
            AudioApplication().install(install_session, app_config.audio_config)

        if app_config.fonts_config and app_config.fonts_config.selected_fonts:
            FontsApplication().install(install_session, app_config.fonts_config.selected_fonts)

        if app_config.shell_config and app_config.shell_config.shell:
            ShellApplication().install(install_session, app_config.shell_config.shell, users)

application_handler: ApplicationHandler = ApplicationHandler()
