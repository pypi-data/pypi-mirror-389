# SPDX-FileCopyrightText: 2023 CELESTIFYX Team
# SPDX-License-Identifier: GPL-3.0-or-later

from typing import (override, assert_never)

from nerve.lib.menu.abstract_menu import AbstractSubMenu
from nerve.lib.models.application import (ApplicationConfiguration, Audio, Fonts, AudioConfiguration, BluetoothConfiguration, FontsConfiguration, ShellConfiguration, Shell)
from nerve.lib.translationhandler import tr
from nerve.tui import Result
from nerve.tui.curses_menu import SelectMenu
from nerve.tui.menu_item import (MenuItem, MenuItemGroup)
from nerve.tui.result import ResultType
from nerve.tui.types import (Alignment, Orientation, FrameProperties)

class ApplicationMenu(AbstractSubMenu[ApplicationConfiguration]):
    def __init__(self, preset: ApplicationConfiguration | None = None) -> None:
        self._app_config: ApplicationConfiguration = preset if preset else ApplicationConfiguration()

        menu_options: list[MenuItem] = self._define_menu_options()
        self._item_group: MenuItemGroup = MenuItemGroup(menu_options, checkmarks=True)

        super().__init__(self._item_group, config=self._app_config, allow_reset=True)

    @override
    def run(self, additional_title: str | None = None) -> ApplicationConfiguration:
        super().run(additional_title=additional_title)
        return self._app_config

    def _define_menu_options(self) -> list[MenuItem]:
        return [
            MenuItem(text=tr('Bluetooth'), action=select_bluetooth, value=self._app_config.bluetooth_config, preview_action=self._prev_bluetooth, key='bluetooth_config'),
            MenuItem(text=tr('Audio'), action=select_audio, preview_action=self._prev_audio, key='audio_config'),
            MenuItem(text=tr('Fonts'), action=select_fonts, value=self._app_config.fonts_config, preview_action=self._prev_fonts, key='fonts_config'),
            MenuItem(text=tr('Shell'), action=select_shell, value=self._app_config.shell_config, preview_action=self._prev_shell, key='shell_config')
        ]

    @staticmethod
    def _prev_bluetooth(item: MenuItem) -> str | None:
        if item.value is not None:
            bluetooth_config: BluetoothConfiguration = item.value
            return (tr('Bluetooth') + ': ') + tr('Enabled') if bluetooth_config.enabled else tr('Disabled')

        return None

    @staticmethod
    def _prev_audio(item: MenuItem) -> str | None:
        if item.value is not None:
            config: AudioConfiguration = item.value
            return tr('Audio') + ': ' + str(config.audio.value)

        return None

    @staticmethod
    def _prev_fonts(item: MenuItem) -> str | None:
        if item.value is not None:
            config: FontsConfiguration = item.value
            return (tr('Selected fonts') + ':\n' + '\n'.join(['- ' + font for font in config.selected_fonts])) if config.selected_fonts else tr('No fonts selected')

        return None

    @staticmethod
    def _prev_shell(item: MenuItem) -> str | None:
        if item.value is not None:
            config: ShellConfiguration = item.value
            return tr('Shell') + ': ' + str(config.shell.value)

        return None

def select_bluetooth(preset: BluetoothConfiguration | None) -> BluetoothConfiguration:
    group: MenuItemGroup = MenuItemGroup.yes_no()
    group.focus_item = MenuItem.no()

    if preset is not None:
        group.set_selected_by_value(preset.enabled)

    header: str = tr('Would you like to configure Bluetooth?') + '\n'
    result: Result[bool] = SelectMenu[bool](group, header=header, alignment=Alignment.CENTER, columns=2, orientation=Orientation.HORIZONTAL, allow_skip=True).run()

    match result.type_:
        case ResultType.Selection:
            enabled: bool = result.item() == MenuItem.yes()
            return BluetoothConfiguration(enabled)

        case ResultType.Skip:
            return preset

        case _:
            raise ValueError('Unhandled result type')

def select_audio(preset: AudioConfiguration | None = None) -> AudioConfiguration | None:
    items: list[MenuItem] = [MenuItem(a.value, value=a) for a in Audio]  # type: ignore
    group: MenuItemGroup = MenuItemGroup(items)

    if preset:
        group.set_focus_by_value(preset.audio)

    result: Result[Audio] = SelectMenu[Audio](group, allow_skip=True, alignment=Alignment.CENTER, frame=FrameProperties.min(tr('Audio'))).run()

    match result.type_:
        case ResultType.Skip:
            return preset

        case ResultType.Selection:
            return AudioConfiguration(audio=result.get_value())

        case ResultType.Reset:
            raise ValueError('Unhandled result type')

        case _:
            assert_never(result.type_)

def select_fonts(preset: FontsConfiguration | None = None) -> FontsConfiguration | None:
    items: list[MenuItem] = [MenuItem(f.value, value=f) for f in Fonts]  # type: ignore
    group: MenuItemGroup = MenuItemGroup(items, sort_items=True)

    if preset and preset.selected_fonts:
        group.set_selected_by_value(preset.selected_fonts)

    result: Result[str] = SelectMenu[str](group, allow_skip=True, allow_reset=True, alignment=Alignment.CENTER, frame=FrameProperties.min(tr('Fonts')), multi=True).run()

    match result.type_:
        case ResultType.Skip:
            return preset

        case ResultType.Selection:
            return FontsConfiguration(selected_fonts=result.get_values())

        case ResultType.Reset:
            return FontsConfiguration(selected_fonts=[])

        case _:
            assert_never(result.type_)

def select_shell(preset: ShellConfiguration | None = None) -> ShellConfiguration:
    items: list[MenuItem] = [MenuItem(s.value, value=s) for s in Shell] # type: ignore

    group: MenuItemGroup = MenuItemGroup(items)
    group.set_default_by_value(Shell.BASH)

    if preset and preset.shell:
        group.set_focus_by_value(preset.shell)

    result: Result[Shell] = SelectMenu[Shell](group, allow_skip=True, alignment=Alignment.CENTER, frame=FrameProperties.min(tr('Shell'))).run()

    match result.type_:
        case ResultType.Skip:
            return preset

        case ResultType.Selection:
            return ShellConfiguration(shell=result.get_value())

        case ResultType.Reset:
            raise ValueError('Unhandled result type')

        case _:
            assert_never(result.type_)
