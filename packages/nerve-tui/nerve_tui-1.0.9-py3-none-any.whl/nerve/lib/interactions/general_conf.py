# SPDX-FileCopyrightText: 2023 CELESTIFYX Team
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

from enum import Enum
from pathlib import Path
from typing import assert_never

from nerve.lib.translationhandler import tr
from nerve.lib.models.packages import Repository
from nerve.lib.packages.packages import list_available_packages
from nerve.tui.curses_menu import (EditMenu, SelectMenu, Tui)
from nerve.tui.menu_item import (MenuItem, MenuItemGroup)
from nerve.tui.result import (ResultType, Result)
from nerve.tui.types import (Alignment, FrameProperties, Orientation, PreviewStyle)
from nerve.lib.locale.utils import list_timezones
from nerve.lib.models.packages import (AvailablePackage, PackageGroup)
from nerve.lib.translationhandler import Language

class PostInstallationAction(Enum):
    EXIT   = tr('Exit nerve')
    REBOOT = tr('Reboot system')
    CHROOT = tr('chroot into installation for post-installation configurations')

def ask_ntp(preset: bool = True) -> bool:
    header: str = tr('Would you like to use automatic time synchronization (NTP) with the default time servers?\n') + '\n'

    header += tr(
        'Hardware time and other post-configuration steps might be required in order for NTP to work.\n'
        'For more information, please check the Arch wiki'
    ) + '\n'

    preset_val: MenuItem = MenuItem.yes() if preset else MenuItem.no()
    group: MenuItemGroup = MenuItemGroup.yes_no()

    group.focus_item = preset_val
    result: Result[bool] = SelectMenu[bool](group, header=header, allow_skip=True, alignment=Alignment.CENTER, columns=2, orientation=Orientation.HORIZONTAL).run()

    match result.type_:
        case ResultType.Skip:
            return preset

        case ResultType.Selection:
            return result.item() == MenuItem.yes()

        case _:
            raise ValueError('Unhandled return type')

def ask_hostname(preset: str | None = None) -> str | None:
    result: Result[str] = EditMenu(tr('Hostname'), alignment=Alignment.CENTER, allow_skip=True, default_text=preset).input()

    match result.type_:
        case ResultType.Skip:
            return preset

        case ResultType.Selection:
            hostname: str = result.text()
            return None if len(hostname) < 1 else hostname

        case ResultType.Reset:
            raise ValueError('Unhandled result type')

        case _:
            assert_never(result.type_)

def ask_for_a_timezone(preset: str | None = None) -> str:
    from nerve.lib.utils.system_info import SystemInfo

    default: str = SystemInfo().timezone
    timezones: list[str] = list_timezones()

    items: list[MenuItem] = [MenuItem(tz, value=tz) for tz in timezones]
    group: MenuItemGroup = MenuItemGroup(items, sort_items=True)

    group.set_selected_by_value(preset)
    group.set_default_by_value(default)

    result: Result[str] = SelectMenu[str](group, allow_reset=True, allow_skip=True, frame=FrameProperties.min(tr('Timezone')), alignment=Alignment.CENTER).run()

    match result.type_:
        case ResultType.Skip:
            return preset

        case ResultType.Reset:
            return default

        case ResultType.Selection:
            return result.get_value()

        case _:
            assert_never(result.type_)

def select_language(languages: list[Language], preset: Language) -> Language:
    # these are the displayed language names that can either be
    # the English name of a language or, if present, the
    # name of the language in its own language
    items: list[MenuItem] = [MenuItem(lang.display_name, lang) for lang in languages]

    group: MenuItemGroup = MenuItemGroup(items, sort_items=True)
    group.set_focus_by_value(preset)

    title: str = 'NOTE: If a language can not displayed properly, a proper font must be set manually in the console.\n'
    title += 'All available fonts can be found in "/usr/share/kbd/consolefonts"\n'
    title += 'e.g. setfont LatGrkCyr-8x16 (to display latin/greek/cyrillic characters)\n'

    result: Result[Language] = SelectMenu[Language](group, header=title, allow_skip=True, allow_reset=False, alignment=Alignment.CENTER, frame=FrameProperties.min(header=tr('Select language'))).run()

    match result.type_:
        case ResultType.Skip:
            return preset

        case ResultType.Selection:
            return result.get_value()

        case ResultType.Reset:
            raise ValueError('Language selection not handled')

        case _:
            assert_never(result.type_)

def ask_additional_packages_to_install(preset: list[str] | None = None, repositories: set[Repository] | None = None) -> list[str]:
    if not preset:
        preset = []

    if not repositories:
        repositories = set()

    repositories |= {
        Repository.Core,
        Repository.Extra
    }

    repository_text: str = ', '.join([r.value for r in repositories])
    output: str = tr('Repositories: {repositories}'.format(repositories=repository_text)) + '\n'

    output += tr('Loading packages...')
    Tui.print(output, clear_screen=True)

    packages: dict[str, AvailablePackage] = list_available_packages(tuple(repositories))
    package_groups: dict[str, PackageGroup] = PackageGroup.from_available_packages(packages)

    # Additional packages (with some lightweight error handling for invalid package names)
    header: str = tr('Only packages such as base, base-devel, linux, linux-firmware, efibootmgr and optional profile packages are installed.') + '\n'
    header += tr('Pick any packages from the list below that should be installed additionally.') + '\n'

    # there are over 15k packages, so this needs to be quick
    preset_packages: list[AvailablePackage | PackageGroup] = []

    for p in preset:
        if p in packages:
            preset_packages.append(packages[p])
        elif p in package_groups:
            preset_packages.append(package_groups[p])

    items: list[MenuItem] = [MenuItem(name, value=pkg,   preview_action=lambda x: x.value.info()) for (name, pkg)   in packages.items()]
    items += [MenuItem(name, value=group, preview_action=lambda x: x.value.info()) for (name, group) in package_groups.items()]

    menu_group: MenuItemGroup = MenuItemGroup(items, sort_items=True)
    menu_group.set_selected_by_value(preset_packages)

    result: Result[AvailablePackage | PackageGroup] = SelectMenu[AvailablePackage | PackageGroup](menu_group, header=header, alignment=Alignment.LEFT, allow_reset=True, allow_skip=True, multi=True, preview_frame=FrameProperties.max('Package info'), preview_style=PreviewStyle.RIGHT, preview_size='auto').run()

    match result.type_:
        case ResultType.Skip:
            return preset

        case ResultType.Reset:
            return []

        case ResultType.Selection:
            selected_packages: list[AvailablePackage | PackageGroup]  = result.get_values()
            return [pkg.name for pkg in selected_packages]

        case _:
            assert_never(result.type_)

def add_number_of_parallel_downloads(preset: int | None = None) -> int | None:
    header: str = tr('This option enables the number of parallel downloads that can occur during package downloads') + '\n'
    header += tr('Enter the number of parallel downloads to be enabled.\n\nNote:\n')
    header += tr(' - Maximum recommended value: {count} ( Allows 5 parallel downloads at a time )') + '\n'
    header += tr(' - Disable/Default : 0 ( Disables parallel downloading, allows only 1 download at a time )\n')

    def validator(s: str | None) -> str | None:
        if s is not None:
            # noinspection PyBroadException
            try:
                value = int(s)

                if value >= 0:
                    return None

            except Exception:
                pass

        return tr('Invalid download number')

    result: Result[str] = EditMenu(tr('Number downloads'), header=header, allow_skip=True, allow_reset=True, validator=validator, default_text=str(preset) if preset is not None else None).input()
    downloads: int | None = None

    match result.type_:
        case ResultType.Skip:
            return preset

        case ResultType.Reset:
            return 0

        case ResultType.Selection:
            downloads = int(result.text())

        case _:
            assert_never(result.type_)

    pacman_conf_path: Path = Path("/etc/pacman.conf")

    with pacman_conf_path.open() as f:
        pacman_conf: list[str] = f.read().split("\n")

    with pacman_conf_path.open(mode='w') as fwrite:
        for line in pacman_conf:
            fwrite.write("ParallelDownloads = " + str(downloads) + "\n" if "ParallelDownloads" in line else line + "\n")

    return downloads

def ask_post_installation() -> PostInstallationAction:
    header: str = tr('Installation completed') + '\n\n'
    header += tr('What would you like to do next?') + '\n'

    items: list[MenuItem] = [MenuItem(action.value, value=action) for action in PostInstallationAction]
    group: MenuItemGroup = MenuItemGroup(items)

    result: Result[PostInstallationAction] = SelectMenu[PostInstallationAction](group, header=header, allow_skip=False, alignment=Alignment.CENTER).run()

    match result.type_:
        case ResultType.Selection:
            return result.get_value()

        case _:
            raise ValueError('Post installation action not handled')

def ask_abort() -> None:
    prompt: str = tr('Do you really want to abort?') + '\n'

    group: MenuItemGroup = MenuItemGroup.yes_no()
    result: Result[bool] = SelectMenu[bool](group, header=prompt, allow_skip=False, alignment=Alignment.CENTER, columns=2, orientation=Orientation.HORIZONTAL).run()

    if result.item() == MenuItem.yes():
        import sys
        sys.exit(0)
