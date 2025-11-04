# SPDX-FileCopyrightText: 2023 CELESTIFYX Team
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

import re

from typing import override

from nerve.lib.translationhandler import tr
from nerve.tui.curses_menu import (EditMenu, SelectMenu)
from nerve.tui.menu_item import (MenuItem, MenuItemGroup)
from nerve.tui.result import (ResultType, Result)
from nerve.tui.types import (Alignment, Orientation)
from nerve.lib.menu.list_manager import ListManager
from nerve.lib.models.users import (User, Password)
from nerve.lib.utils.util import get_password

class UserList(ListManager[User]):
    def __init__(self, prompt: str, users: list[User]) -> None:
        self._actions: list[str] = [
            tr('Add a user'),
            tr('Change password'),
            tr('Promote/Demote user'),
            tr('Delete User')
        ]

        super().__init__(entries=users, base_actions=[self._actions[0]], sub_menu_actions=self._actions[1:], prompt=prompt)

    @override
    def selected_action_display(self, selection: User) -> str:
        return selection.username

    @override
    def handle_action(self, action: str, entry: User | None, data: list[User]) -> list[User]:
        if action == self._actions[0]:  # add
            new_user: User | None = self._add_user()

            if new_user:
                # in case a user with the same username as an existing user
                # was created, we'll replace the existing one
                data: list[User] = [d for d in data if d.username != new_user.username]
                data += [new_user]

        elif action == self._actions[1] and entry:  # change password
            header: str = tr("User") + ': ' + entry.username + '\n'
            new_password: Password | None = get_password(tr('Password'), header=header)

            if new_password:
                user: User = next(filter(lambda x: x == entry, data))
                user.password = new_password

        elif action == self._actions[2] and entry:  # promote/demote
            user: User = next(filter(lambda x: x == entry, data))
            user.sudo = False if user.sudo else True
        elif action == self._actions[3] and entry:  # delete
            data = [d for d in data if d != entry]

        return data

    @staticmethod
    def _check_for_correct_username(username: str | None) -> str | None:
        return None if username and re.match(pattern=r'^[a-z_][a-z0-9_-]*\$?$', string=username) and (len(username) <= 32) else tr('The username you entered is invalid')

    def _add_user(self) -> User | None:
        edit_result: Result[str] = EditMenu(tr('Username'), allow_skip=True, validator=self._check_for_correct_username).input()

        match edit_result.type_:
            case ResultType.Skip:
                return None

            case ResultType.Selection:
                username = edit_result.text()

            case _:
                raise ValueError('Unhandled result type')

        if not username:
            return None

        header: str = tr("Username") + ': ' + username + '\n'
        password: Password | None = get_password(tr('Password'), header=header, allow_skip=True)

        if not password:
            return None

        header += tr("Password") + ': ' + password.hidden() + '\n\n'
        header += tr('Should "{username}" be a superuser (sudo)?\n'.format(username=username))

        group: MenuItemGroup = MenuItemGroup.yes_no()
        group.focus_item = MenuItem.yes()

        result: Result[bool] = SelectMenu[bool](group, header=header, alignment=Alignment.CENTER, columns=2, orientation=Orientation.HORIZONTAL, search_enabled=False, allow_skip=False).run()

        match result.type_:
            case ResultType.Selection:
                sudo: bool = result.item() == MenuItem.yes()

            case _:
                raise ValueError('Unhandled result type')

        return User(username, password, sudo)

def ask_for_additional_users(prompt: str = '', defined_users: list[User] | None = None) -> list[User]:
    if not defined_users:
        defined_users = []

    users: list[User] = UserList(prompt, defined_users).run()
    return users
