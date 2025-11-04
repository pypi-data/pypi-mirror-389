# SPDX-FileCopyrightText: 2023 CELESTIFYX Team
# SPDX-License-Identifier: GPL-3.0-or-later

import copy

from typing import cast

from nerve.lib.translationhandler import tr
from nerve.lib.menu.menu_helper import MenuHelper
from nerve.tui.curses_menu import SelectMenu
from nerve.tui.menu_item import (MenuItem, MenuItemGroup)
from nerve.tui.result import (ResultType, Result)
from nerve.tui.types import Alignment

class ListManager[ValueT]:
    def __init__(self, entries: list[ValueT], base_actions: list[str], sub_menu_actions: list[str], prompt: str | None = None) -> None:
        """
        :param prompt:  Text which will appear at the header
		type param: string

        :param entries: list/dict of an option to be shown / manipulated
        type param: list

        :param base_actions: list of actions that are displayed in the main list manager,
        usually global actions such as 'Add...'
        type param: list

        :param sub_menu_actions: list of actions available for a chosen entry
        type param: list
        """
        self._original_data: list[ValueT] = copy.deepcopy(entries)
        self._data:          list[ValueT] = copy.deepcopy(entries)

        self._prompt: str | None = prompt

        self._separator:      str = ''
        self._confirm_action: str = tr('Confirm and exit')
        self._cancel_action:  str = tr('Cancel')

        self._terminate_actions: list[str] = [self._confirm_action, self._cancel_action]
        self._base_actions: list[str] = base_actions
        self._sub_menu_actions: list[str] = sub_menu_actions

        self._last_choice: ValueT | str | None = None

    def is_last_choice_cancel(self) -> bool:
        return (self._last_choice == self._cancel_action) if self._last_choice is not None else False

    def run(self) -> list[ValueT]:
        additional_options: list[str] = self._base_actions + self._terminate_actions
        value: ValueT | str | None = None

        while True:
            group: MenuItemGroup = MenuHelper(data=self._data, additional_options=additional_options).create_menu_group()
            result: Result[ValueT | str] = SelectMenu[ValueT | str](group, search_enabled=False, allow_skip=False, alignment=Alignment.CENTER).run()

            match result.type_:
                case ResultType.Selection:
                    value = result.get_value()

                case _:
                    raise ValueError('Unhandled return type')

            if value in self._base_actions:
                value = cast(str, value)
                self._data = self.handle_action(value, None, self._data)
            elif value in self._terminate_actions:
                break
            else:  # an entry of the existing selection was chosen
                selected_entry: ValueT | str = result.get_value()
                selected_entry: ValueT = cast(ValueT, selected_entry)

                self._run_actions_on_entry(selected_entry)

        self._last_choice = value
        return self._original_data if result.get_value() == self._cancel_action else self._data

    def _run_actions_on_entry(self, entry: ValueT) -> None:
        options: list[str] = self.filter_options(entry, self._sub_menu_actions) + [self._cancel_action]
        value: str | None = None

        items: list[MenuItem] = [MenuItem(o, value=o) for o in options]
        group: MenuItemGroup = MenuItemGroup(items, sort_items=False)

        header: str = self.selected_action_display(entry) + '\n'
        result: Result[str] = SelectMenu[str](group, header=header, search_enabled=False, allow_skip=False, alignment=Alignment.CENTER).run()

        match result.type_:
            case ResultType.Selection:
                value = result.get_value()

            case _:
                raise ValueError('Unhandled return type')

        if value != self._cancel_action:
            self._data = self.handle_action(value, entry, self._data)

    def selected_action_display(self, selection: ValueT) -> str:
        """
        this will return the value to be displayed in the
        'Select an action for '{}'' string
        """
        raise NotImplementedError('Please implement me in the child class')

    def handle_action(self, action: str, entry: ValueT | None, data: list[ValueT]) -> list[ValueT]:
        """
        this function is called when a base action or
        a specific action for an entry is triggered
        """
        raise NotImplementedError('Please implement me in the child class')

    def filter_options(self, selection: ValueT, options: list[str]) -> list[str]:
        """
        filter which actions to show for a specific selection
        """
        return options
