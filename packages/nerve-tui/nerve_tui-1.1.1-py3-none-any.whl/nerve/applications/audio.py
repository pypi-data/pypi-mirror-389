# SPDX-FileCopyrightText: 2023 CELESTIFYX Team
# SPDX-License-Identifier: GPL-3.0-or-later

from typing import TYPE_CHECKING
from pathlib import Path

from nerve.applications import Application
from nerve.lib.hardware import SysInfo
from nerve.lib.models.application import (Audio, AudioConfiguration)
from nerve.lib.output import debug

if TYPE_CHECKING:
    from nerve.lib.installer import Installer

class AudioApplication(Application):
    @property
    def pulseaudio_packages(self) -> list[str]:
        return ['pulseaudio']

    @property
    def pipewire_packages(self) -> list[str]:
        return [
            'pipewire',
            'pipewire-alsa',
            'pipewire-jack',
            'pipewire-pulse',
            'gst-plugin-pipewire',
            'libpulse',
            'wireplumber'
        ]

    def install(self, install_session: 'Installer', audio_config: AudioConfiguration) -> None:
        debug('Installing audio server: ' + str(audio_config.audio.value))

        if audio_config.audio == Audio.NO_AUDIO:
            debug('No audio server selected, skipping installation.')
            return

        if SysInfo.requires_sof_fw():
            install_session.add_additional_packages('sof-firmware')

        if SysInfo.requires_alsa_fw():
            install_session.add_additional_packages('alsa-firmware')

        match audio_config.audio:
            case Audio.PIPEWIRE:
                install_session.add_additional_packages(self.pipewire_packages)

            case Audio.PULSEAUDIO:
                install_session.add_additional_packages(self.pulseaudio_packages)
