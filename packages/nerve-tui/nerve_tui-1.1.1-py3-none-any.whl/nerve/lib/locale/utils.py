# SPDX-FileCopyrightText: 2023 CELESTIFYX Team
# SPDX-License-Identifier: GPL-3.0-or-later

from nerve.lib.exceptions import (ServiceException, SysCallError)
from nerve.lib.general import SysCommand
from nerve.lib.output import error

def list_keyboard_languages() -> list[str]:
    return SysCommand(cmd="localectl --no-pager list-keymaps", environment_vars={
        'SYSTEMD_COLORS': '0'
    }).decode().splitlines()

def list_locales() -> list[str]:
    locales: list[str] = []

    with open('/usr/share/i18n/SUPPORTED') as file:
        for line in file:
            if line != 'C.UTF-8 UTF-8\n':
                locales.append(line.rstrip())

    return locales

def verify_keyboard_layout(layout: str) -> bool:
    for language in list_keyboard_languages():
        if layout.lower() == language.lower():
            return True

    return False

def get_kb_layout() -> str:
    # noinspection PyBroadException
    try:
        lines: list[str] = SysCommand(cmd="localectl --no-pager status", environment_vars={
            'SYSTEMD_COLORS': '0'
        }).decode().splitlines()
    except Exception:
        return ""

    vcline: str = ""

    for line in lines:
        if "VC Keymap: " in line:
            vcline = line

    if vcline == "":
        return ""

    layout: str = vcline.split(": ")[1]
    return "" if not verify_keyboard_layout(layout) else layout

def set_kb_layout(locale: str) -> bool:
    if len(locale.strip()):
        if not verify_keyboard_layout(locale):
            error("Invalid keyboard locale specified: " + locale)
            return False

        try:
            SysCommand('localectl set-keymap ' + locale)
        except SysCallError as err:
            raise ServiceException("Unable to set locale '" + locale + "' for console: " + str(err))

        return True

    return False

def list_timezones() -> list[str]:
    return SysCommand(cmd="timedatectl --no-pager list-timezones", environment_vars={
        'SYSTEMD_COLORS': '0'
    }).decode().splitlines()
