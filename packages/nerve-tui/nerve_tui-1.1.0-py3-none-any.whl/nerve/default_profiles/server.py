# SPDX-FileCopyrightText: 2023 CELESTIFYX Team
# SPDX-License-Identifier: GPL-3.0-or-later

from typing import (TYPE_CHECKING, override, assert_never)

from nerve.default_profiles.profile import (Profile, ProfileType, SelectResult)
from nerve.lib.output import info
from nerve.lib.profile.profiles_handler import profile_handler
from nerve.tui.curses_menu import SelectMenu
from nerve.tui.menu_item import (MenuItem, MenuItemGroup)
from nerve.tui.result import (ResultType, Result)
from nerve.tui.types import (FrameProperties, PreviewStyle)

if TYPE_CHECKING:
    from nerve.lib.installer import Installer

class ServerProfile(Profile):
    def __init__(self, current_value: list[Profile] | None = None) -> None:
        if not current_value:
            current_value = []

        super().__init__(name='Server', profile_type=ProfileType.Server, current_selection=current_value)

    @override
    def do_on_select(self) -> SelectResult:
        items: list[MenuItem] = [MenuItem(p.name, value=p, preview_action=lambda x: x.value.preview_text()) for p in profile_handler.get_server_profiles()]
        group: MenuItemGroup = MenuItemGroup(items, sort_items=True)

        group.set_selected_by_value(self.current_selection)
        result: Result[Profile] = SelectMenu[Profile](group, allow_reset=True, allow_skip=True, preview_style=PreviewStyle.RIGHT, preview_size='auto', preview_frame=FrameProperties.max('Info'), multi=True).run()

        match result.type_:
            case ResultType.Selection:
                selections: list[Profile] = result.get_values()
                self.current_selection = selections

                return SelectResult.NewSelection

            case ResultType.Skip:
                return SelectResult.SameSelection

            case ResultType.Reset:
                return SelectResult.ResetCurrent

            case _:
                assert_never(result.type_)

    @override
    def post_install(self, install_session: 'Installer') -> None:
        for profile in self.current_selection:
            profile.post_install(install_session)

    @override
    def install(self, install_session: 'Installer') -> None:
        server_info: list[str] = self.current_selection_names()
        details: str = ', '.join(server_info)

        info('Now installing the selected servers: ' + details)

        for server in self.current_selection:
            info('Installing ' + server.name + '...')

            install_session.add_additional_packages(server.packages)
            install_session.enable_service(server.services)

            server.install(install_session)

        info('If your selections included multiple servers with the same port, you may have to reconfigure them.')
