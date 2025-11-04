# SPDX-FileCopyrightText: 2023 CELESTIFYX Team
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations
from typing import (Any, Self)
from types import TracebackType

from nerve.lib.translationhandler import tr
from nerve.tui.curses_menu import (SelectMenu, Tui)
from nerve.tui.menu_item import (MenuItem, MenuItemGroup)
from nerve.tui.result import (ResultType, Result)
from nerve.tui.types import (Chars, FrameProperties, FrameStyle, PreviewStyle)
from nerve.lib.output import error

CONFIG_KEY: str = '__config__'

class AbstractMenu[ValueT]:
    def __init__(self, item_group: MenuItemGroup, config: Any, auto_cursor: bool = True, allow_reset: bool = False, reset_warning: str | None = None) -> None:
        self._menu_item_group: MenuItemGroup = item_group
        self._config: Any = config
        self.auto_cursor: bool = auto_cursor
        self._allow_reset: bool = allow_reset
        self._reset_warning: str | None = reset_warning

        self.is_context_mgr: bool = False
        self._sync_from_config()

    def __enter__(self, *_: Any) -> Self:
        self.is_context_mgr = True
        return self

    def __exit__(self, exc_type: type[BaseException] | None, exc_value: BaseException | None, _: TracebackType | None) -> None:
        # TODO: https://stackoverflow.com/questions/28157929/how-to-safely-handle-an-exception-inside-a-context-manager
        # TODO: skip processing when it comes from a planified exit
        if exc_type is not None:
            error(str(exc_value))
            Tui.print("Please submit this issue (and file) to https://gitlab.com/nerve-dev/nerve/-/issues")

            # Return None to propagate the exception
            return None

        self.sync_all_to_config()
        return None

    def _sync_from_config(self) -> None:
        for item in self._menu_item_group.menu_items:
            if item.key is not None and not item.key.startswith(CONFIG_KEY):
                config_value: Any = getattr(self._config, item.key)

                if config_value is not None:
                    item.value = config_value

    def sync_all_to_config(self) -> None:
        for item in self._menu_item_group.menu_items:
            if item.key:
                setattr(self._config, item.key, item.value)

    def set_enabled(self, key: str, enabled: bool) -> None:
        # the __config__ is associated with multiple items
        found:         bool = False
        is_config_key: bool = key == CONFIG_KEY

        for item in self._menu_item_group.items:
            if item.key and (item.key == key) or (is_config_key and item.key.startswith(CONFIG_KEY)):
                item.enabled = enabled
                found = True

        if not found:
            raise ValueError('No selector found: ' + key)

    def disable_all(self) -> None:
        for item in self._menu_item_group.items:
            item.enabled = False

    def _is_config_valid(self) -> bool:
        return True

    def run(self, additional_title: str | None = None) -> ValueT | None:
        self._sync_from_config()

        while True:
            result: Result[ValueT] = SelectMenu[ValueT](self._menu_item_group, allow_skip=False, allow_reset=self._allow_reset, reset_warning_msg=self._reset_warning, preview_style=PreviewStyle.RIGHT, preview_size='auto', preview_frame=FrameProperties('Info', FrameStyle.MAX), additional_title=additional_title).run()

            match result.type_:
                case ResultType.Selection:
                    item: MenuItem = result.item()

                    if item.action is None:
                        if not self._is_config_valid():
                            continue

                        break

                case ResultType.Reset:
                    return None

        self.sync_all_to_config()
        return None

class AbstractSubMenu[ValueT](AbstractMenu[ValueT]):
    def __init__(self, item_group: MenuItemGroup, config: Any, auto_cursor: bool = True, allow_reset: bool = False) -> None:
        back_text: str = str(Chars.RIGHT_ARROW.value) + ' ' + tr('Back')
        item_group.add_item(MenuItem(text=back_text))

        super().__init__(item_group, config=config, auto_cursor=auto_cursor, allow_reset=allow_reset)
