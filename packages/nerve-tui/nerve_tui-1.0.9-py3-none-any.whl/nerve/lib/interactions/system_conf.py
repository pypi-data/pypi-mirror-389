# SPDX-FileCopyrightText: 2023 CELESTIFYX Team
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations
from typing import assert_never

from nerve.lib.translationhandler import tr
from nerve.tui.curses_menu import SelectMenu
from nerve.tui.menu_item import (MenuItem, MenuItemGroup)
from nerve.tui.result import (ResultType, Result)
from nerve.tui.types import (Alignment, FrameProperties, FrameStyle, Orientation, PreviewStyle)
from nerve.lib.hardware import (GfxDriver, SysInfo)
from nerve.lib.models.bootloader import Bootloader

def select_kernel(preset: list[str] | None = None) -> list[str]:
    """
    Asks the user to select a kernel for a system.

    :return: The string as a selected kernel
    :rtype: string
    """
    from nerve.lib import __packages__

    if not preset:
        preset = []

    kernels: list[str] = __packages__[3:]
    default_kernel: str = kernels[0]

    items: list[MenuItem] = [MenuItem(k, value=k) for k in kernels]
    group: MenuItemGroup = MenuItemGroup(items, sort_items=True)

    group.set_default_by_value(default_kernel)
    group.set_focus_by_value(default_kernel)
    group.set_selected_by_value(preset)

    result: Result[str] = SelectMenu[str](group, allow_skip=True, allow_reset=True, alignment=Alignment.CENTER, frame=FrameProperties.min(tr('Kernel')), multi=True).run()

    match result.type_:
        case ResultType.Skip:
            return preset

        case ResultType.Reset:
            return []

        case ResultType.Selection:
            return result.get_values()

        case _:
            assert_never(result.type_)

def ask_for_bootloader(preset: Bootloader | None) -> Bootloader | None:
    from nerve.lib.args import config_handler

    is_skip: bool = config_handler.args.skip_boot
    is_uefi: bool = SysInfo.has_uefi()

    hidden_options: list[Bootloader] = [Bootloader.NO_BOOTLOADER] if not is_skip else []
    options: list[Bootloader] = [Bootloader.Grub, Bootloader.Limine] if not is_uefi else [b for b in Bootloader if b not in hidden_options]
    default: Bootloader = Bootloader.NO_BOOTLOADER if is_skip else (Bootloader.Systemd if is_uefi else Bootloader.Grub)

    header: str | None = tr('UEFI is not detected and some options are disabled') if not is_uefi else None

    items: list[MenuItem] = [MenuItem(o.value, value=o) for o in options]
    group: MenuItemGroup = MenuItemGroup(items)

    group.set_default_by_value(default)
    group.set_focus_by_value(preset)

    result: Result[Bootloader] = SelectMenu[Bootloader](group, header=header, alignment=Alignment.CENTER, frame=FrameProperties.min(tr('Bootloader')), allow_skip=True).run()

    match result.type_:
        case ResultType.Skip:
            return preset

        case ResultType.Selection:
            return result.get_value()

        case ResultType.Reset:
            raise ValueError('Unhandled result type')

        case _:
            assert_never(result.type_)

def ask_for_uki(preset: bool = True) -> bool:
    prompt: str = tr('Would you like to use unified kernel images?') + '\n'
    group: MenuItemGroup = MenuItemGroup.yes_no()

    group.set_focus_by_value(preset)
    result: Result[bool] = SelectMenu[bool](group, header=prompt, columns=2, orientation=Orientation.HORIZONTAL, alignment=Alignment.CENTER, allow_skip=True).run()

    match result.type_:
        case ResultType.Skip:
            return preset

        case ResultType.Selection:
            return result.item() == MenuItem.yes()

        case ResultType.Reset:
            raise ValueError('Unhandled result type')

        case _:
            assert_never(result.type_)

def select_driver(options: list[GfxDriver] | None = None, preset: GfxDriver | None = None) -> GfxDriver | None:
    """
    Somewhat convoluted function, whose job is straightforward.
    Select a graphics driver from a pre-defined set of popular options.

    (The template xorg is for beginner users, not advanced, and should
    therefore appeal to the public first and edge cases later)
    """
    if not options:
        options = [driver for driver in GfxDriver]

    items: list[MenuItem] = [MenuItem(o.value, value=o, preview_action=lambda x: x.value.packages_text()) for o in options]
    group: MenuItemGroup = MenuItemGroup(items, sort_items=True)
    group.set_default_by_value(GfxDriver.AllOpenSource)

    if preset is not None:
        group.set_focus_by_value(preset)

    header: str = ''

    if SysInfo.has_amd_graphics():
        header += tr('For the best compatibility with your AMD hardware, you may want to use either the all open-source or AMD / ATI options.') + '\n'

    if SysInfo.has_intel_graphics():
        header += tr('For the best compatibility with your Intel hardware, you may want to use either the all open-source or Intel options.\n')

    if SysInfo.has_nvidia_graphics():
        header += tr('For the best compatibility with your Nvidia hardware, you may want to use the Nvidia proprietary driver.\n')

    result: Result[GfxDriver] = SelectMenu[GfxDriver](group, header=header, allow_skip=True, allow_reset=True, preview_size='auto', preview_style=PreviewStyle.BOTTOM, preview_frame=FrameProperties(tr('Info'), h_frame_style=FrameStyle.MIN)).run()

    match result.type_:
        case ResultType.Skip:
            return preset

        case ResultType.Reset:
            return None

        case ResultType.Selection:
            return result.get_value()

        case _:
            assert_never(result.type_)

def ask_for_swap(preset: bool = True) -> bool:
    default_item: MenuItem = MenuItem.yes() if preset else MenuItem.no()

    prompt: str = tr('Would you like to use swap on zram?') + '\n'
    group: MenuItemGroup = MenuItemGroup.yes_no()

    group.set_focus_by_value(default_item)
    result: Result[bool] = SelectMenu[bool](group, header=prompt, columns=2, orientation=Orientation.HORIZONTAL, alignment=Alignment.CENTER, allow_skip=True).run()

    match result.type_:
        case ResultType.Skip:
            return preset

        case ResultType.Selection:
            return result.item() == MenuItem.yes()

        case ResultType.Reset:
            raise ValueError('Unhandled result type')

        case _:
            assert_never(result.type_)
