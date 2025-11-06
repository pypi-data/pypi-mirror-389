# SPDX-FileCopyrightText: 2023 CELESTIFYX Team
# SPDX-License-Identifier: GPL-3.0-or-later

from typing import override

from nerve.default_profiles.profile import (GreeterType, ProfileType)
from nerve.default_profiles.xorg import XorgProfile

class XmonadProfile(XorgProfile):
    def __init__(self) -> None:
        super().__init__(name='Xmonad', profile_type=ProfileType.WindowMgr)

    @property
    @override
    def packages(self) -> list[str]:
        return [
            'xmonad',
            'xmonad-contrib',
            'xmonad-extras',
            'xterm',
            'dmenu'
        ]

    @property
    @override
    def default_greeter_type(self) -> GreeterType:
        return GreeterType.Lightdm
