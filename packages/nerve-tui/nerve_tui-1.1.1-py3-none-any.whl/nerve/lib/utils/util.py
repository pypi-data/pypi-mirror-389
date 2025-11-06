# SPDX-FileCopyrightText: 2023 CELESTIFYX Team
# SPDX-License-Identifier: GPL-3.0-or-later

from pathlib import Path
from typing import Callable
from os.path import exists

from nerve.lib.translationhandler import tr
from nerve.tui.curses_menu import EditMenu
from nerve.tui.result import (ResultType, Result)
from nerve.tui.types import Alignment
from nerve.lib.models.users import Password

def get_password(text: str, header: str | None = None, allow_skip: bool = False, preset: str | None = None, skip_confirmation: bool = False) -> Password | None:
    failure: str | None = None

    while True:
        user_hdr: str | None = None

        if failure is not None:
            user_hdr = str(header) + '\n' + str(failure) + '\n'
        elif header is not None:
            user_hdr = header

        result: Result[str] = EditMenu(text, header=user_hdr, alignment=Alignment.CENTER, allow_skip=allow_skip, default_text=preset, hide_input=True).input()

        if allow_skip and not result.has_item() or not result.text():
            return None

        password: Password = Password(plaintext=result.text())

        if skip_confirmation:
            return password

        confirmation_header: str = (str(header) + tr("Password") + ': ' + password.hidden() + '\n') if header is not None else (tr("Password") + ': ' + password.hidden() + '\n')
        result: Result[str] = EditMenu(tr('Confirm password'), header=confirmation_header, alignment=Alignment.CENTER, allow_skip=False, hide_input=True).input()

        if password.plaintext == result.text():
            return password

        failure = tr('The confirmation password did not match, please try again')

def prompt_dir(text: str, header: str | None = None, validate: bool = True, must_exist: bool = True, allow_skip: bool = False, preset: str | None = None) -> Path | None:
    def validate_path(path: str | None) -> str | None:
        return None if path and ((Path(path).exists() and Path(path).is_dir()) if must_exist else True) else tr('Not a valid directory')

    validate_func: Callable[[str | None], str | None] | None = validate_path if validate else None
    result: Result[str] = EditMenu(text, header=header, alignment=Alignment.CENTER, allow_skip=allow_skip, validator=validate_func, default_text=preset).input()

    match result.type_:
        case ResultType.Skip:
            return None

        case ResultType.Selection:
            return None if not result.text() else Path(result.text())

    return None

def is_subpath(first: Path, second: Path) -> bool:
    """
    Check if _first_ a subpath of _second_
    """
    try:
        first.relative_to(second)
        return True
    except ValueError:
        return False

def first_existing_path(paths: list[str | Path]) -> Path | None:
    return next((path for path in map(Path, paths) if exists(str(path))), None)

def read_file(path: str) -> str | None:
    try:
        return open(path).read().strip() if exists(path) else None
    except (IOError, PermissionError, FileNotFoundError, OSError):
        pass

    return None
