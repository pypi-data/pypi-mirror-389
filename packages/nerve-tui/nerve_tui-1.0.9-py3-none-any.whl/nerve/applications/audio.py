# SPDX-FileCopyrightText: 2023 CELESTIFYX Team
# SPDX-License-Identifier: GPL-3.0-or-later

from typing import TYPE_CHECKING
from pathlib import Path

from nerve.applications import Application
from nerve.lib.hardware import SysInfo
from nerve.lib.models.application import (Audio, AudioConfiguration)
from nerve.lib.models.users import User
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

    @staticmethod
    def _enable_pipewire(install_session: 'Installer', users: list['User'] | None = None) -> None:
        if not users:
            return

        for user in users:
            # Create the full path for enabling the pipewire systemd items
            service_dir: Path = install_session.target / 'home' / user.username / '.config' / 'systemd' / 'user' / 'default.target.wants'
            service_dir.mkdir(parents=True, exist_ok=True)

            # Set ownership of the entire user catalogue
            install_session.arch_chroot('chown -R {username}:{username} /home/{username}'.format(username=user.username))

            # symlink in the correct pipewire systemd items
            install_session.arch_chroot(cmd='ln -sf /usr/lib/systemd/user/pipewire-pulse.service /home/' + user.username + '/.config/systemd/user/default.target.wants/pipewire-pulse.service', run_as=user.username)
            install_session.arch_chroot(cmd='ln -sf /usr/lib/systemd/user/pipewire-pulse.socket /home/' + user.username + '/.config/systemd/user/default.target.wants/pipewire-pulse.socket',   run_as=user.username)

    def install(self, install_session: 'Installer', audio_config: AudioConfiguration, users: list[User] | None = None) -> None:
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
                self._enable_pipewire(install_session, users)

            case Audio.PULSEAUDIO:
                install_session.add_additional_packages(self.pulseaudio_packages)
