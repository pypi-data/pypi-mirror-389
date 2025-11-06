# SPDX-FileCopyrightText: 2023 CELESTIFYX Team
# SPDX-License-Identifier: GPL-3.0-or-later

from typing import override

from nerve.default_profiles.profile import (GreeterType, ProfileType)
from nerve.default_profiles.xorg import XorgProfile

class I3wmProfile(XorgProfile):
    def __init__(self) -> None:
        super().__init__(name='i3-wm', profile_type=ProfileType.WindowMgr)

    @property
    @override
    def packages(self) -> list[str]:
        return [
            'i3-wm',
            'i3lock',
            'i3status',
            'i3blocks',
            'xss-lock',
            'xterm',
            'lightdm-gtk-greeter',
            'lightdm',
            'dmenu'
        ]

    @property
    @override
    def default_greeter_type(self) -> GreeterType:
        return GreeterType.Lightdm
