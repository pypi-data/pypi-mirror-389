# SPDX-FileCopyrightText: 2023 CELESTIFYX Team
# SPDX-License-Identifier: GPL-3.0-or-later

from typing import override

from nerve.default_profiles.desktops import SeatAccess
from nerve.default_profiles.profile import (GreeterType, ProfileType)
from nerve.default_profiles.xorg import XorgProfile
from nerve.lib.translationhandler import tr
from nerve.tui.curses_menu import SelectMenu
from nerve.tui.menu_item import (MenuItem, MenuItemGroup)
from nerve.tui.result import (ResultType, Result)
from nerve.tui.types import (Alignment, FrameProperties)

class HyprlandProfile(XorgProfile):
    def __init__(self) -> None:
        super().__init__(name='Hyprland', profile_type=ProfileType.DesktopEnv)
        self.custom_settings: dict[str, str | None] = {'seat_access': None}

    @property
    @override
    def packages(self) -> list[str]:
        return [
            'hyprland',
            'dunst',
            'kitty',
            'uwsm',
            'dolphin',
            'wofi',
            'xdg-desktop-portal-hyprland',
            'qt5-wayland',
            'qt6-wayland',
            'polkit-kde-agent',
            'grim',
            'slurp'
        ]

    @property
    @override
    def default_greeter_type(self) -> GreeterType:
        return GreeterType.Sddm

    @property
    @override
    def services(self) -> list[str]:
        return [pref] if (pref := self.custom_settings.get('seat_access', None)) else []

    def _ask_seat_access(self) -> None:
        # need to activate seat service and add to a seat group
        header: str = tr('Hyprland needs access to your seat (collection of hardware devices i.e. keyboard, mouse, etc)') + '\n'
        header += tr('Choose an option to give Hyprland access to your hardware') + '\n'

        items: list[MenuItem] = [MenuItem(s.value, value=s) for s in SeatAccess]
        group: MenuItemGroup = MenuItemGroup(items, sort_items=True)

        default: str | None = self.custom_settings.get('seat_access', None)
        group.set_default_by_value(default)

        result: Result[SeatAccess] = SelectMenu[SeatAccess](group, header=header, allow_skip=False, frame=FrameProperties.min(tr('Seat access')), alignment=Alignment.CENTER).run()

        if result.type_ == ResultType.Selection:
            self.custom_settings['seat_access'] = result.get_value().value

    @override
    def do_on_select(self) -> None:
        self._ask_seat_access()
        return None
