# SPDX-FileCopyrightText: 2023 CELESTIFYX Team
# SPDX-License-Identifier: GPL-3.0-or-later

from typing import override

from nerve.default_profiles.profile import (GreeterType, ProfileType)
from nerve.default_profiles.xorg import XorgProfile

class Xfce4Profile(XorgProfile):
    def __init__(self) -> None:
        super().__init__(name='Xfce4', profile_type=ProfileType.DesktopEnv)

    @property
    @override
    def packages(self) -> list[str]:
        return [
            'xfce4',
            'xfce4-goodies',
            'xarchiver'
        ]

    @property
    @override
    def default_greeter_type(self) -> GreeterType:
        return GreeterType.Lightdm
