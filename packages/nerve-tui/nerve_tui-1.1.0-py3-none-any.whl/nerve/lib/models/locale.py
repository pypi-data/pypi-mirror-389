# SPDX-FileCopyrightText: 2023 CELESTIFYX Team
# SPDX-License-Identifier: GPL-3.0-or-later

from dataclasses import dataclass
from typing import Any

from nerve.lib.translationhandler import tr
from nerve.lib.locale.utils import get_kb_layout

@dataclass
class LocaleConfiguration:
    kb_layout: str
    sys_lang:  str
    sys_enc:   str

    @staticmethod
    def default() -> 'LocaleConfiguration':
        layout: str = get_kb_layout() or 'us'
        return LocaleConfiguration(layout, 'en_US.UTF-8', 'UTF-8')

    def json(self) -> dict[str, str]:
        return {
            'kb_layout': self.kb_layout,
            'sys_lang':  self.sys_lang,
            'sys_enc':   self.sys_enc
        }

    def preview(self) -> str:
        output: str = tr('Keyboard layout') + ': ' + self.kb_layout + '\n'
        output += tr('Locale language') + ': ' + self.sys_lang + '\n'
        output += tr('Locale encoding') + ': ' + self.sys_enc

        return output

    @classmethod
    def _load_config(cls, config: 'LocaleConfiguration', args: dict[str, str]) -> 'LocaleConfiguration':
        if 'sys_lang' in args:
            config.sys_lang = args['sys_lang']

        if 'sys_enc' in args:
            config.sys_enc = args['sys_enc']

        if 'kb_layout' in args:
            config.kb_layout = args['kb_layout']

        return config

    @classmethod
    def parse_arg(cls, args: dict[str, Any]) -> 'LocaleConfiguration':
        default: LocaleConfiguration = cls.default()
        default = cls._load_config(default, args['locale_config'] if 'locale_config' in args else args)

        return default
