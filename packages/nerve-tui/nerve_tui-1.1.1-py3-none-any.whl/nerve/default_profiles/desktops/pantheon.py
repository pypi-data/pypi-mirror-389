# SPDX-FileCopyrightText: 2023 CELESTIFYX Team
# SPDX-License-Identifier: GPL-3.0-or-later

from typing import override

from nerve.default_profiles.profile import (GreeterType, ProfileType)
from nerve.default_profiles.xorg import XorgProfile

class PantheonProfile(XorgProfile):
    def __init__(self) -> None:
        super().__init__(name='Pantheon', profile_type=ProfileType.DesktopEnv, advanced=True)

    @property
    @override
    def packages(self) -> list[str]:
        return [
            'pantheon-session',
            'pantheon-polkit-agent',
            'pantheon-print',
            'pantheon-settings-daemon',
            'sound-theme-elementary',
            'switchboard',
            'switchboard-plug-desktop',
            'elementary-icon-theme',
            'wingpanel-indicator-session',
            'wingpanel-indicator-datetime',
            'pantheon-applications-menu',
            'gnome-settings-daemon',
            'pantheon-default-settings'
        ]

    @property
    @override
    def default_greeter_type(self) -> GreeterType:
        return GreeterType.LightdmSlick
