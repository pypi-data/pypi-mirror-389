# SPDX-FileCopyrightText: 2023 CELESTIFYX Team
# SPDX-License-Identifier: GPL-3.0-or-later

import getpass

from pathlib import Path
from typing import TYPE_CHECKING

from nerve.lib.general import SysCommandWorker
from nerve.lib.models.authentication import (AuthenticationConfiguration, U2FLoginConfiguration, U2FLoginMethod)
from nerve.lib.models.users import User
from nerve.lib.output import debug
from nerve.lib.translationhandler import tr
from nerve.tui.curses_menu import Tui

if TYPE_CHECKING:
    from nerve.lib.installer import Installer

class AuthenticationHandler:
    def setup_auth(self, install_session: 'Installer', auth_config: AuthenticationConfiguration, hostname: str) -> None:
        if auth_config.u2f_config and auth_config.users is not None:
            self._setup_u2f_login(install_session, auth_config.u2f_config, auth_config.users, hostname)

    def _setup_u2f_login(self, install_session: 'Installer', u2f_config: U2FLoginConfiguration, users: list[User], hostname: str) -> None:
        self._configure_u2f_mapping(install_session, u2f_config, users, hostname)
        self._update_pam_config(install_session, u2f_config)

    def _update_pam_config(self, install_session: 'Installer', u2f_config: U2FLoginConfiguration) -> None:
        entry_type: str | None = None

        match u2f_config.u2f_login_method:
            case U2FLoginMethod.Passwordless:
                entry_type = 'sufficient'

            case U2FLoginMethod.SecondFactor:
                entry_type = 'required'

            case _:
                raise ValueError('Unknown U2F login method: ' + str(u2f_config.u2f_login_method))

        config_entry: str = 'auth ' + entry_type + ' pam_u2f.so authfile=/etc/u2f_mappings cue'

        debug('U2F PAM configuration: ' + config_entry)
        debug('Passwordless sudo enabled: ' + str(u2f_config.passwordless_sudo))

        sudo_config: Path = install_session.target / 'etc/pam.d/sudo'
        sys_login:   Path = install_session.target / 'etc/pam.d/system-login'

        if u2f_config.passwordless_sudo:
            self._add_u2f_entry(sudo_config, config_entry)

        self._add_u2f_entry(sys_login, config_entry)

    @staticmethod
    def _add_u2f_entry(file: Path, entry: str) -> None:
        if not file.exists():
            debug('File does not exist: ' + str(file))
            return None

        content: list[str] = file.read_text().splitlines()

        # remove any existing u2f auth entry
        content = [line for line in content if 'pam_u2f.so' not in line]

        # add the u2f auth entry as the first one after comments
        inserted: bool = False

        for (i, line) in enumerate(content):
            if not line.startswith('#'):
                content.insert(i, entry)
                inserted = True

                break

        if not inserted:
            content.append(entry)

        file.write_text('\n'.join(content) + '\n')
        return None

    @staticmethod
    def _configure_u2f_mapping(install_session: 'Installer', u2f_config: U2FLoginConfiguration, users: list[User], hostname: str) -> None:
        debug('Setting up U2F login: ' + str(u2f_config.u2f_login_method.value))
        install_session.pacman.strap('pam-u2f')

        Tui.print(tr('Setting up U2F login: ' + str(u2f_config.u2f_login_method.value)))

        # https://developers.yubico.com/pam-u2f/
        u2f_auth_file: Path = install_session.target / 'etc/u2f_mappings'
        u2f_auth_file.touch()

        existing_keys: str = u2f_auth_file.read_text()
        registered_keys: list[str] = []

        for user in users:
            Tui.print('')
            Tui.print(tr('Setting up U2F device for user: {user}').format(user=user.username))
            Tui.print(tr('You may need to enter the PIN and then touch your U2F device to register it'))

            cmd: str = ' '.join(['arch-chroot', '-S', str(install_session.target), 'pamu2fcfg', '-u', user.username, '-o', 'pam://' + hostname, '-i', 'pam://' + hostname])
            debug('Enrolling U2F device: ' + cmd)

            worker: SysCommandWorker = SysCommandWorker(cmd, peek_output=True)
            pin_inputted: bool = False

            while worker.is_alive():
                if not pin_inputted and bytes('enter pin for', 'UTF-8') in worker._trace_log.lower():
                    worker.write(bytes(getpass.getpass(''), 'UTF-8'))
                    pin_inputted = True

            output: list[str] = worker.decode().strip().splitlines()
            debug('Output from pamu2fcfg: ' + str(output))

            key: str = output[-1].strip()
            registered_keys.append(key)

        all_keys:      str = '\n'.join(registered_keys)
        existing_keys: str = ('\n' + all_keys) if existing_keys else all_keys

        u2f_auth_file.write_text(existing_keys)

auth_handler: AuthenticationHandler = AuthenticationHandler()
