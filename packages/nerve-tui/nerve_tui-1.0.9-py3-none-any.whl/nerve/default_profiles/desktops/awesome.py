# SPDX-FileCopyrightText: 2023 CELESTIFYX Team
# SPDX-License-Identifier: GPL-3.0-or-later

from typing import (TYPE_CHECKING, override)

from nerve.default_profiles.profile import ProfileType
from nerve.default_profiles.xorg import XorgProfile

if TYPE_CHECKING:
    from nerve.lib.installer import Installer

class AwesomeProfile(XorgProfile):
    def __init__(self) -> None:
        super().__init__(name='Awesome', profile_type=ProfileType.WindowMgr)

    @property
    @override
    def packages(self) -> list[str]:
        return [
            'awesome',
            'alacritty',
            'xorg-xinit',
            'xorg-xrandr',
            'xterm',
            'feh',
            'slock',
            'terminus-font',
            'gnu-free-fonts',
            'xsel'
        ]

    @override
    def install(self, install_session: 'Installer') -> None:
        super().install(install_session)

        # TODO: Copy a full configuration to ~/.config/awesome/rc.lua instead.
        with open(file=str(install_session.target) + '/etc/xdg/awesome/rc.lua') as fh:
            awesome_lua: str = fh.read()

        # Replace xterm with alacritty for a smoother experience.
        awesome_lua: str = awesome_lua.replace('"xterm"', '"alacritty"')

        with open(file=str(install_session.target) + '/etc/xdg/awesome/rc.lua', mode='w') as fh:
            fh.write(awesome_lua)

        # TODO: Configure the right-click-menu to contain the above packages that were installed. (as a user config)

        # TODO: check if we selected a greeter,
        # but for now, awesome is intended to run without one.
        with open(str(install_session.target) + '/etc/X11/xinit/xinitrc') as xinitrc:
            xinitrc_data: str = xinitrc.read()

        for line in xinitrc_data.split('\n'):
            if any(keyword in line for keyword in ('twm &', 'xclock', 'xterm')):
                xinitrc_data: str = xinitrc_data.replace(line, '# ' + line)

        xinitrc_data += '\n'
        xinitrc_data += 'exec awesome\n'

        with open(file=str(install_session.target) + '/etc/X11/xinit/xinitrc', mode='w') as xinitrc:
            xinitrc.write(xinitrc_data)
