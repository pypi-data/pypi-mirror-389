# SPDX-FileCopyrightText: 2023 CELESTIFYX Team
# SPDX-License-Identifier: GPL-3.0-or-later

from typing import override

from nerve.default_profiles.profile import (GreeterType, ProfileType)
from nerve.default_profiles.xorg import XorgProfile

class GnomeProfile(XorgProfile):
    def __init__(self) -> None:
        super().__init__(name='GNOME', profile_type=ProfileType.DesktopEnv)

    @property
    @override
    def packages(self) -> list[str]:
        from nerve.lib.args import config_handler

        return [
            'gnome',
            'gnome-tweaks'
        ] if not config_handler.args.minimal_packages else [
            'gnome-console',
            'gnome-control-center',
            'gnome-keyring',
            'gnome-menus',
            'gnome-session',
            'gnome-settings-daemon',
            'gnome-shell',
            'gnome-shell-extensions',
            'grilo-plugins',
            'loupe',
            'nautilus',
            'sushi',
            'gnome-desktop',
            'gnome-tweaks'
        ]

    @property
    @override
    def default_greeter_type(self) -> GreeterType:
        return GreeterType.Gdm
