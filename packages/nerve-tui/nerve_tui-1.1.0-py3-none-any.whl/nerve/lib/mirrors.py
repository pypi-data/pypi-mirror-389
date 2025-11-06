# SPDX-FileCopyrightText: 2023 CELESTIFYX Team
# SPDX-License-Identifier: GPL-3.0-or-later

import time
import urllib.parse

from pathlib import Path
from typing import (override, assert_never)

from nerve.tui.curses_menu import (EditMenu, SelectMenu, Tui)
from nerve.tui.menu_item import (MenuItem, MenuItemGroup)
from nerve.tui.result import (ResultType, Result)
from nerve.tui.types import (Alignment, FrameProperties)
from nerve.lib.translationhandler import tr
from nerve.lib.menu.abstract_menu import AbstractSubMenu
from nerve.lib.menu.list_manager import ListManager
from nerve.lib.models.packages import Repository
from nerve.lib.models.mirrors import (CustomRepository, CustomServer, MirrorConfiguration, MirrorRegion, MirrorStatusEntryV3, MirrorStatusListV3, SignCheck, SignOption)
from nerve.lib.networking import fetch_data_from_url
from nerve.lib.output import (FormattedOutput, debug)

class CustomMirrorRepositoriesList(ListManager[CustomRepository]):
    def __init__(self, custom_repositories: list[CustomRepository]) -> None:
        self._actions: list[str] = [
            tr('Add a custom repository'),
            tr('Change custom repository'),
            tr('Delete custom repository')
        ]

        super().__init__(custom_repositories, base_actions=[self._actions[0]], sub_menu_actions=self._actions[1:], prompt='')

    @override
    def selected_action_display(self, selection: CustomRepository) -> str:
        return selection.name

    @override
    def handle_action(self, action: str, entry: CustomRepository | None, data: list[CustomRepository]) -> list[CustomRepository]:
        if action == self._actions[0]:  # add
            new_repo = self._add_custom_repository()

            if new_repo is not None:
                data  = [d for d in data if d.name != new_repo.name]
                data += [new_repo]

        elif (action == self._actions[1]) and entry:  # modify repo
            new_repo = self._add_custom_repository(entry)

            if new_repo is not None:
                data  = [d for d in data if d.name != entry.name]
                data += [new_repo]

        elif (action == self._actions[2]) and entry:  # delete
            data = [d for d in data if d != entry]

        return data

    @staticmethod
    def _add_custom_repository(preset: CustomRepository | None = None) -> CustomRepository | None:
        edit_result: Result[str] = EditMenu(tr('Repository name'), alignment=Alignment.CENTER, allow_skip=True, default_text=preset.name if preset else None).input()

        name: str | None = None
        url: str | None = None

        sign_check: SignCheck | None = None
        sign_opt: SignOption | None = None

        match edit_result.type_:
            case ResultType.Selection:
                name = edit_result.text()

            case ResultType.Skip:
                return preset

            case _:
                raise ValueError('Unhandled return type')

        header: str = tr("Name") + ': ' + name
        edit_result: Result[str] = EditMenu(tr('Url'), header=header, alignment=Alignment.CENTER, allow_skip=True, default_text=preset.url if preset else None).input()

        match edit_result.type_:
            case ResultType.Selection:
                url = edit_result.text()

            case ResultType.Skip:
                return preset

            case _:
                raise ValueError('Unhandled return type')

        header += '\n' + tr("Url") + ': ' + url + '\n'
        prompt: str = header + '\n' + tr('Select signature check')

        sign_chk_items: list[MenuItem] = [MenuItem(s.value, value=s.value) for s in SignCheck]
        group: MenuItemGroup = MenuItemGroup(sign_chk_items, sort_items=False)

        if preset is not None:
            group.set_selected_by_value(preset.sign_check.value)

        result: Result[SignCheck] = SelectMenu[SignCheck](group, header=prompt, alignment=Alignment.CENTER, allow_skip=False).run()

        match result.type_:
            case ResultType.Selection:
                sign_check = SignCheck(result.get_value())

            case _:
                raise ValueError('Unhandled return type')

        header += tr("Signature check") + ': ' + str(sign_check.value) + '\n'
        prompt  = header + '\n' + tr('Select signature option')

        sign_opt_items: list[MenuItem] = [MenuItem(s.value, value=s.value) for s in SignOption]
        group: MenuItemGroup = MenuItemGroup(sign_opt_items, sort_items=False)

        if preset is not None:
            group.set_selected_by_value(preset.sign_option.value)

        result: Result[SignCheck] = SelectMenu[SignCheck](group, header=prompt, alignment=Alignment.CENTER, allow_skip=False).run()

        match result.type_:
            case ResultType.Selection:
                sign_opt = SignOption(result.get_value())

            case _:
                raise ValueError('Unhandled return type')

        return CustomRepository(name, url, sign_check, sign_opt)

class CustomMirrorServersList(ListManager[CustomServer]):
    def __init__(self, custom_servers: list[CustomServer]) -> None:
        self._actions: list[str] = [
            tr('Add a custom server'),
            tr('Change custom server'),
            tr('Delete custom server')
        ]

        super().__init__(entries=custom_servers, base_actions=[self._actions[0]], sub_menu_actions=self._actions[1:], prompt='')

    @override
    def selected_action_display(self, selection: CustomServer) -> str:
        return selection.url

    @override
    def handle_action(self, action: str, entry: CustomServer | None, data: list[CustomServer]) -> list[CustomServer]:
        if action == self._actions[0]:  # add
            new_server = self._add_custom_server()

            if new_server is not None:
                data  = [d for d in data if d.url != new_server.url]
                data += [new_server]

        elif (action == self._actions[1]) and entry:  # modify repo
            new_server = self._add_custom_server(entry)

            if new_server is not None:
                data  = [d for d in data if d.url != entry.url]
                data += [new_server]

        elif (action == self._actions[2]) and entry:  # delete
            data = [d for d in data if d != entry]

        return data

    @staticmethod
    def _add_custom_server(preset: CustomServer | None = None) -> CustomServer | None:
        edit_result: Result[str] = EditMenu(tr('Server url'), alignment=Alignment.CENTER, allow_skip=True, default_text=preset.url if preset else None).input()

        match edit_result.type_:
            case ResultType.Selection:
                uri: str = edit_result.text()
                return CustomServer(uri)

            case ResultType.Skip:
                return preset

        return None

class MirrorMenu(AbstractSubMenu[MirrorConfiguration]):
    def __init__(self, preset: MirrorConfiguration | None = None) -> None:
        self._mirror_config: MirrorConfiguration = preset if preset else MirrorConfiguration()

        menu_options: list[MenuItem] = self._define_menu_options()
        self._item_group: MenuItemGroup = MenuItemGroup(menu_options, checkmarks=True)

        super().__init__(self._item_group, config=self._mirror_config, allow_reset=True)

    def _define_menu_options(self) -> list[MenuItem]:
        return [
            MenuItem(text=tr('Select regions'),        action=select_mirror_regions,        value=self._mirror_config.mirror_regions,      preview_action=self._prev_regions,          key='mirror_regions'),
            MenuItem(text=tr('Add custom servers'),    action=add_custom_mirror_servers,    value=self._mirror_config.custom_servers,      preview_action=self._prev_custom_servers,   key='custom_servers'),
            MenuItem(text=tr('Optional repositories'), action=select_optional_repositories, value=[],                                      preview_action=self._prev_additional_repos, key='optional_repositories'),
            MenuItem(text=tr('Add custom repository'), action=select_custom_mirror,         value=self._mirror_config.custom_repositories, preview_action=self._prev_custom_mirror,    key='custom_repositories')
        ]

    @staticmethod
    def _prev_regions(item: MenuItem) -> str:
        regions: list[MirrorRegion] = item.get_value()
        output: str = ''

        for region in regions:
            output += str(region.name) + '\n'

            for url in region.urls:
                output += ' - ' + str(url) + '\n'

            output += '\n'

        return output

    @staticmethod
    def _prev_additional_repos(item: MenuItem) -> str | None:
        if item.value:
            repositories: list[Repository] = item.value
            repos: str = ', '.join([repo.value for repo in repositories])

            return tr("Additional repositories") + ': ' + repos

        return None

    @staticmethod
    def _prev_custom_mirror(item: MenuItem) -> str | None:
        if not item.value:
            return None

        custom_mirrors: list[CustomRepository] = item.value
        output: str = FormattedOutput.as_table(custom_mirrors)

        return output.strip()

    @staticmethod
    def _prev_custom_servers(item: MenuItem) -> str | None:
        if not item.value:
            return None

        custom_servers: list[CustomServer] = item.value
        output: str = '\n'.join([server.url for server in custom_servers])

        return output.strip()

    @override
    def run(self, additional_title: str | None = None) -> MirrorConfiguration:
        super().run(additional_title=additional_title)
        return self._mirror_config

def select_mirror_regions(preset: list[MirrorRegion]) -> list[MirrorRegion]:
    Tui.print(tr('Loading mirror regions...'), clear_screen=True)

    mirror_list_handler.load_mirrors()
    available_regions: list[MirrorRegion] = mirror_list_handler.get_mirror_regions()

    if not available_regions:
        return []

    preset_regions: list[MirrorRegion] = [region for region in available_regions if region in preset]

    items: list[MenuItem] = [MenuItem(region.name, value=region) for region in available_regions]
    group: MenuItemGroup = MenuItemGroup(items, sort_items=True)

    group.set_selected_by_value(preset_regions)
    result: Result[MirrorRegion] = SelectMenu[MirrorRegion](group, alignment=Alignment.CENTER, frame=FrameProperties.min(tr('Mirror regions')), allow_reset=True, allow_skip=True, multi=True).run()

    match result.type_:
        case ResultType.Skip:
            return preset_regions

        case ResultType.Reset:
            return []

        case ResultType.Selection:
            return result.get_values()

        case _:
            assert_never(result.type_)

def add_custom_mirror_servers(preset: list[CustomServer] | None = None) -> list[CustomServer]:
    if not preset:
        preset = []

    custom_mirrors: list[CustomServer] = CustomMirrorServersList(preset).run()
    return custom_mirrors

def select_custom_mirror(preset: list[CustomRepository] | None = None) -> list[CustomRepository]:
    if not preset:
        preset = []

    custom_mirrors: list[CustomRepository] = CustomMirrorRepositoriesList(preset).run()
    return custom_mirrors

def select_optional_repositories(preset: list[Repository]) -> list[Repository]:
    """
    Allows the user to select additional repositories (multilib and testing) if desired.

    :return: The string as a selected repository :rtype: Repository
    """
    repositories: list[Repository] = [Repository.Multilib, Repository.Testing]
    items:        list[MenuItem]   = [MenuItem(r.value, value=r) for r in repositories]

    group: MenuItemGroup = MenuItemGroup(items, sort_items=True)
    group.set_selected_by_value(preset)

    result: Result[Repository] = SelectMenu[Repository](group, alignment=Alignment.CENTER, frame=FrameProperties.min('Additional repositories'), allow_reset=True, allow_skip=True, multi=True).run()

    match result.type_:
        case ResultType.Skip:
            return preset

        case ResultType.Reset:
            return []

        case ResultType.Selection:
            return result.get_values()

        case _:
            assert_never(result.type_)

class MirrorListHandler:
    def __init__(self, local_mirrorlist: Path = Path('/etc/pacman.d/mirrorlist')) -> None:
        self._local_mirrorlist = local_mirrorlist
        self._status_mappings: dict[str, list[MirrorStatusEntryV3]] | None = None

    def _mappings(self) -> dict[str, list[MirrorStatusEntryV3]]:
        if not self._status_mappings:
            self.load_mirrors()

        assert self._status_mappings is not None
        return self._status_mappings

    def get_mirror_regions(self) -> list[MirrorRegion]:
        available_mirrors: list[MirrorRegion] = []
        mappings: dict[str, list[MirrorStatusEntryV3]] = self._mappings()

        for region_name, status_entry in mappings.items():
            urls: list[str] = [entry.server_url for entry in status_entry]
            region: MirrorRegion = MirrorRegion(region_name, urls)

            available_mirrors.append(region)

        return available_mirrors

    def load_mirrors(self) -> None:
        from nerve.lib.args import config_handler

        if not config_handler.args.offline:
            if not self.load_remote_mirrors():
                self.load_local_mirrors()

            return

        self.load_local_mirrors()

    def load_remote_mirrors(self) -> bool:
        url: str = "https://archlinux.org/mirrors/status/json/"
        attempts: int = 3

        for attempt_nr in range(attempts):
            try:
                mirrorlist: str = fetch_data_from_url(url)
                self._status_mappings = self._parse_remote_mirror_list(mirrorlist)

                return True
            except Exception as e:
                debug('Error while fetching mirror list: ' + str(e))
                time.sleep(attempt_nr + 1)

        debug('Unable to fetch mirror list remotely, falling back to local mirror list')
        return False

    def load_local_mirrors(self) -> None:
        with self._local_mirrorlist.open() as fp:
            self._status_mappings = self._parse_locale_mirrors(fp.read())

    def get_status_by_region(self, region: str) -> list[MirrorStatusEntryV3]:
        mappings: dict[str, list[MirrorStatusEntryV3]] = self._mappings()
        region_list: list[MirrorStatusEntryV3] = mappings[region]

        return sorted(region_list, key=lambda mirror: (mirror.score, mirror.speed))

    @staticmethod
    def _parse_remote_mirror_list(mirrorlist: str) -> dict[str, list[MirrorStatusEntryV3]]:
        mirror_status: MirrorStatusListV3 = MirrorStatusListV3.model_validate_json(mirrorlist)
        sorting_placeholder: dict[str, list[MirrorStatusEntryV3]] = {}

        for mirror in mirror_status.urls:
            # We filter out mirrors that have bad criteria values
            if any([
                not mirror.active,  # Disabled by mirror-list admins
                not mirror.last_sync,  # Has not synced recently
                # mirror.score (error rate) over time reported from backend:
                # https://github.com/archlinux/archweb/blob/31333d3516c91db9a2f2d12260bd61656c011fd1/mirrors/utils.py#L111C22-L111C66
                (not mirror.score or (mirror.score >= 100))
            ]):
                continue

            if mirror.country == "":
                # TODO: This should be removed once RFC!29 is merged and completed
                # Until then, there are mirrors which lacks data in the backend
                # and there is no way of knowing where they're located.
                # So we have to assume world-wide
                mirror.country = "Worldwide"

            if mirror.url.startswith('http'):
                sorting_placeholder.setdefault(mirror.country, []).append(mirror)

        sorted_by_regions: dict[str, list[MirrorStatusEntryV3]] = dict({region: unsorted_mirrors for (region, unsorted_mirrors) in sorted(sorting_placeholder.items(), key=lambda item: item[0])})
        return sorted_by_regions

    @staticmethod
    def _parse_locale_mirrors(mirrorlist: str) -> dict[str, list[MirrorStatusEntryV3]]:
        mirror_list: dict[str, list[MirrorStatusEntryV3]] = {}
        current_region: str = ''

        for line in mirrorlist.splitlines():
            line: str = line.strip()

            if line.startswith('## '):
                current_region = line.replace('## ', '').strip()
                mirror_list.setdefault(current_region, [])

            if line.startswith('Server = '):
                if not current_region:
                    current_region = 'Local'
                    mirror_list.setdefault(current_region, [])

                url: str = line.removeprefix('Server = ')
                mirror_entry: MirrorStatusEntryV3 = MirrorStatusEntryV3(url=url.removesuffix('$repo/os/$arch'), protocol=urllib.parse.urlparse(url).scheme, active=True, country=current_region or 'Worldwide', country_code='WW', isos=True, ipv4=True, ipv6=True, details='Locally defined mirror')

                mirror_list[current_region].append(mirror_entry)

        return mirror_list

mirror_list_handler: MirrorListHandler = MirrorListHandler()
