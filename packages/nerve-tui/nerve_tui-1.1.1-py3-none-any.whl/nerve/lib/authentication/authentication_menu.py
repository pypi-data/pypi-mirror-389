# SPDX-FileCopyrightText: 2023 CELESTIFYX Team
# SPDX-License-Identifier: GPL-3.0-or-later

from typing import override

from nerve.lib.disk.fido import Fido2
from nerve.lib.interactions.manage_users_conf import ask_for_additional_users
from nerve.lib.menu.abstract_menu import AbstractSubMenu
from nerve.lib.models import Fido2Device
from nerve.lib.models.authentication import (AuthenticationConfiguration, U2FLoginConfiguration, U2FLoginMethod)
from nerve.lib.models.users import (Password, User)
from nerve.lib.output import FormattedOutput
from nerve.lib.translationhandler import tr
from nerve.lib.utils.util import get_password
from nerve.tui.curses_menu import SelectMenu
from nerve.tui.menu_item import (MenuItem, MenuItemGroup)
from nerve.tui.result import (Result, ResultType)
from nerve.tui.types import (Alignment, FrameProperties, Orientation)

class AuthenticationMenu(AbstractSubMenu[AuthenticationConfiguration]):
    def __init__(self, preset: AuthenticationConfiguration | None = None) -> None:
        self._auth_config: AuthenticationConfiguration = preset if preset else AuthenticationConfiguration()

        menu_options: list[MenuItem] = self._define_menu_options()
        self._item_group: MenuItemGroup = MenuItemGroup(menu_options, checkmarks=True)

        super().__init__(self._item_group, config=self._auth_config, allow_reset=True)

    @override
    def run(self, additional_title: str | None = None) -> AuthenticationConfiguration:
        super().run(additional_title=additional_title)
        return self._auth_config

    def _define_menu_options(self) -> list[MenuItem]:
        return [
            MenuItem(text=tr('Root password'), action=select_root_password, preview_action=self._prev_root_pwd, key='root_enc_password'),
            MenuItem(text=tr('User account'), action=self._create_user_account, preview_action=self._prev_users, key='users'),
            MenuItem(text=tr('U2F login setup'), action=select_u2f_login, value=self._auth_config.u2f_config, preview_action=self._prev_u2f_login, key='u2f_config')
        ]

    @staticmethod
    def _create_user_account(preset: list[User] | None = None) -> list[User]:
        preset: list[User] = [] if not preset else preset
        users:  list[User] = ask_for_additional_users(defined_users=preset)

        return users

    @staticmethod
    def _prev_users(item: MenuItem) -> str | None:
        users: list[User] | None = item.value
        return FormattedOutput.as_table(users) if users else None

    @staticmethod
    def _prev_root_pwd(item: MenuItem) -> str | None:
        if item.value is not None:
            password: Password = item.value
            return tr("Root password") + ': ' + password.hidden()

        return None

    @staticmethod
    def _prev_u2f_login(item: MenuItem) -> str | None:
        if item.value is not None:
            u2f_config: U2FLoginConfiguration = item.value

            login_method: str = u2f_config.u2f_login_method.display_value()
            output:       str = tr('U2F login method: ') + login_method

            output += '\n'
            output += tr('Passwordless sudo: ') + (tr('Enabled') if u2f_config.passwordless_sudo else tr('Disabled'))

            return output

        devices: list[Fido2Device] = Fido2.get_fido2_devices()
        return tr('No U2F devices found') if not devices else None

def select_root_password(_: str | None = None) -> Password | None:
    password: Password | None = get_password(text=tr('Root password'), allow_skip=True)
    return password

def select_u2f_login(preset: U2FLoginConfiguration) -> U2FLoginConfiguration | None:
    devices: list[Fido2Device] = Fido2.get_fido2_devices()

    if not devices:
        return None

    items: list[MenuItem] = []

    for method in U2FLoginMethod:
        items.append(MenuItem(method.display_value(), value=method))

    group: MenuItemGroup = MenuItemGroup(items)

    if preset is not None:
        group.set_selected_by_value(preset.u2f_login_method)

    result: Result[U2FLoginMethod] = SelectMenu[U2FLoginMethod](group, alignment=Alignment.CENTER, frame=FrameProperties.min(tr('U2F Login Method')), allow_skip=True, allow_reset=True).run()

    match result.type_:
        case ResultType.Selection:
            u2f_method: U2FLoginMethod = result.get_value()

            group: MenuItemGroup = MenuItemGroup.yes_no()
            group.focus_item = MenuItem.no()

            result_sudo: Result[bool] = SelectMenu[bool](group, header=tr('Enable passwordless sudo?'), alignment=Alignment.CENTER, columns=2, orientation=Orientation.HORIZONTAL, allow_skip=True).run()
            passwordless_sudo: bool = result_sudo.item() == MenuItem.yes()

            return U2FLoginConfiguration(u2f_login_method=u2f_method, passwordless_sudo=passwordless_sudo)

        case ResultType.Skip:
            return preset

        case ResultType.Reset:
            return None

        case _:
            raise ValueError('Unhandled result type')
