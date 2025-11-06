# SPDX-FileCopyrightText: 2023 CELESTIFYX Team
# SPDX-License-Identifier: GPL-3.0-or-later

from typing import (TYPE_CHECKING, NamedTuple)

from nerve.applications import Application
from nerve.lib.output import debug
from nerve.lib.models.application import Shell
from nerve.lib.models.users import User

if TYPE_CHECKING:
    from nerve.lib.installer import Installer

class ShellPackage(NamedTuple):
    package: str | list[str]
    binary:  str

class ShellApplication(Application):
    _shell_packages: dict[Shell, ShellPackage] = {
        Shell.BASH:    ShellPackage('bash', '/usr/bin/bash'),
        Shell.DASH:    ShellPackage('dash', '/usr/bin/dash'),
        Shell.FISH:    ShellPackage('fish', '/usr/bin/fish'),
        Shell.ZSH:     ShellPackage('zsh', '/usr/bin/zsh'),
        Shell.NUSHELL: ShellPackage('nushell', '/usr/bin/nu'),
        Shell.TCSH:    ShellPackage('tcsh', '/usr/bin/tcsh'),
        Shell.KSH:     ShellPackage('ksh', '/usr/bin/ksh'),
        Shell.XONSH:   ShellPackage('xonsh', '/usr/bin/xonsh'),
        Shell.ELVISH:  ShellPackage('elvish', '/usr/bin/elvish')
    }

    def install(self, install_session: 'Installer', selected_shell: Shell, users: list['User'] | None = None) -> None:
        shell_info: ShellPackage | None = self._shell_packages.get(selected_shell)

        if not shell_info:
            return

        debug('Installation shell: ' + shell_info.package)

        install_session.add_additional_packages(shell_info.package)
        install_session.set_shell(shell_info.binary, users)
