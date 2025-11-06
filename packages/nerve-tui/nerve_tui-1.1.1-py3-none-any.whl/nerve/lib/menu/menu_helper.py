# SPDX-FileCopyrightText: 2023 CELESTIFYX Team
# SPDX-License-Identifier: GPL-3.0-or-later

from nerve.lib.output import FormattedOutput
from nerve.tui.menu_item import (MenuItem, MenuItemGroup)

class MenuHelper[ValueT]:
    def __init__(self, data: list[ValueT], additional_options: list[str] | None = None) -> None:
        if not additional_options:
            additional_options = []

        self._separator: str = ''
        self._data: list[ValueT] = data
        self._additional_options: list[str] = additional_options

    def create_menu_group(self) -> MenuItemGroup:
        table_data_mapping: dict[str, ValueT | str | None] = self._table_to_data_mapping(self._data)
        items: list[MenuItem] = []

        for (key, value) in table_data_mapping.items():
            item: MenuItem = MenuItem(key, value=value)

            if value is None:
                item.read_only = True

            items.append(item)

        group: MenuItemGroup = MenuItemGroup(items, sort_items=False)
        return group

    def _table_to_data_mapping(self, data: list[ValueT]) -> dict[str, ValueT | str | None]:
        display_data: dict[str, ValueT | str | None] = {}

        if data:
            table: str = FormattedOutput.as_table(data)
            rows: list[str] = table.split('\n')

            # these are the header rows of the table
            display_data = {
                rows[0]: None,
                rows[1]: None
            }

            for (row, entry) in zip(rows[2:], data):
                display_data[row] = entry

        if self._additional_options:
            display_data[self._separator] = None

            for option in self._additional_options:
                display_data[option] = option

        return display_data
