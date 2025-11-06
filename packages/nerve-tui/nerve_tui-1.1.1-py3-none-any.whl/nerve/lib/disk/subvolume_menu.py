# SPDX-FileCopyrightText: 2023 CELESTIFYX Team
# SPDX-License-Identifier: GPL-3.0-or-later

from pathlib import Path
from typing import (override, assert_never)

from nerve.lib.models.device import SubvolumeModification
from nerve.lib.translationhandler import tr
from nerve.tui.curses_menu import EditMenu
from nerve.tui.result import (ResultType, Result)
from nerve.tui.types import Alignment
from nerve.lib.menu.list_manager import ListManager
from nerve.lib.utils.util import prompt_dir

class SubvolumeMenu(ListManager[SubvolumeModification]):
    def __init__(self, btrfs_subvols: list[SubvolumeModification], prompt: str | None = None) -> None:
        self._actions: list[str] = [
            tr('Add subvolume'),
            tr('Edit subvolume'),
            tr('Delete subvolume')
        ]

        super().__init__(entries=btrfs_subvols, base_actions=[self._actions[0]], sub_menu_actions=self._actions[1:], prompt=prompt)

    @override
    def selected_action_display(self, selection: SubvolumeModification) -> str:
        return str(selection.name)

    @staticmethod
    def _add_subvolume(preset: SubvolumeModification | None = None) -> SubvolumeModification:
        def validate(_value: str | None) -> str | None:
            return None if _value else tr('Value cannot be empty')

        result: Result[str] = EditMenu(tr('Subvolume name'), alignment=Alignment.CENTER, allow_skip=True, default_text=str(preset.name) if preset else None, validator=validate).input()
        name: str | None = None

        match result.type_:
            case ResultType.Skip:
                return preset

            case ResultType.Selection:
                name = result.text()

            case ResultType.Reset:
                raise ValueError('Unhandled result type')

            case _:
                assert_never(result.type_)

        header: str = tr('Subvolume name') + ": " + str(name) + "\n"
        path: Path | None = prompt_dir(tr("Subvolume mountpoint"), header=header, allow_skip=True, validate=True, must_exist=False)

        return preset if not path else SubvolumeModification(Path(name), path)

    @override
    def handle_action(self, action: str, entry: SubvolumeModification | None, data: list[SubvolumeModification]) -> list[SubvolumeModification]:
        data: list[SubvolumeModification]

        if action == self._actions[0]:  # add
            new_subvolume: SubvolumeModification = self._add_subvolume()

            if new_subvolume is not None:
                # in case a user with the same username as an existing user
                # was created, we'll replace the existing one
                data = [d for d in data if d.name != new_subvolume.name]
                data += [new_subvolume]

        elif entry is not None:  # edit
            if action == self._actions[1]:  # edit subvolume
                new_subvolume = self._add_subvolume(entry)

                if new_subvolume is not None:
                    # we'll remove the original subvolume and add the modified version
                    data = [d for d in data if d.name != entry.name and d.name != new_subvolume.name]
                    data += [new_subvolume]

            elif action == self._actions[2]:  # delete
                data = [d for d in data if d != entry]

        return data
