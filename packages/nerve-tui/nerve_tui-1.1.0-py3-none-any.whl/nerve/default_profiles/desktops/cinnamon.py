# SPDX-FileCopyrightText: 2023 CELESTIFYX Team
# SPDX-License-Identifier: GPL-3.0-or-later

from typing import override

from nerve.default_profiles.profile import (GreeterType, ProfileType)
from nerve.default_profiles.xorg import XorgProfile

class CinnamonProfile(XorgProfile):
    def __init__(self) -> None:
        super().__init__(name='Cinnamon', profile_type=ProfileType.DesktopEnv)

    @property
    @override
    def packages(self) -> list[str]:
        return [
            'cinnamon',
            'system-config-printer',
            'gnome-keyring',
            'gnome-terminal',
            'engrampa',
            'gnome-screenshot',
            'gvfs-smb',
            'xed',
            'xdg-user-dirs-gtk'
        ]

    @property
    @override
    def default_greeter_type(self) -> GreeterType:
        return GreeterType.Lightdm
