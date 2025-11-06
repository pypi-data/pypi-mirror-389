# SPDX-FileCopyrightText: 2023 CELESTIFYX Team
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

import builtins
import gettext
import json
import os

from dataclasses import dataclass
from pathlib import Path
from typing import override

@dataclass
class Language:
    code: str
    name_en: str
    translation: gettext.NullTranslations

    @property
    def display_name(self) -> str:
        return self.name_en

    def json(self) -> str:
        return self.name_en

class TranslationHandler:
    def __init__(self) -> None:
        self._base_pot:  str = 'base.pot'
        self._languages: str = 'languages.json'

        self._total_messages: int = self._get_total_active_messages()
        self._translated_languages: list[Language] = self._get_translations()

    @property
    def translated_languages(self) -> list[Language]:
        return self._translated_languages

    def _get_translations(self) -> list[Language]:
        """
        Load all translated languages and return a list of such
        """
        mappings: list[dict[str, str]] = self._load_language_mappings()
        defined_languages: list[str] = self._provided_translations()
        languages: list[Language] = []

        for short_form in defined_languages:
            mapping_entry: dict[str, str] = next(filter(lambda x: x['code'] == short_form, mappings))

            code: str = mapping_entry['code']
            lang: str = mapping_entry['name']

            try:
                # get a translation for a specific language
                translation: gettext.GNUTranslations = gettext.translation(domain='base', localedir=self._get_locales_dir(), languages=(code, lang))

                language: Language = Language(code, lang, translation)
                languages.append(language)
            except FileNotFoundError as err:
                raise FileNotFoundError("Could not locate language file for '" + lang + ": " + str(err))

        return languages

    def _load_language_mappings(self) -> list[dict[str, str]]:
        """
        Load the mapping table of all known languages
        """
        locales_dir: Path = self._get_locales_dir()
        languages:   Path = Path.joinpath(locales_dir, self._languages)

        with languages.open() as fp:
            return json.load(fp)

    @staticmethod
    def _get_catalog_size(translation: gettext.NullTranslations) -> int:
        """
        Get the number of translated messages for a translation
        """
        # this is a very naughty way of retrieving the data, but
        # there's no alternative method exposed unfortunately
        catalog  = translation._catalog  # type: ignore[attr-defined]
        messages = {k: v for (k, v) in catalog.items() if k and v}

        return len(messages)

    def _get_total_active_messages(self) -> int:
        """
        Get total messages that could be translated
        """
        locales: Path = self._get_locales_dir()

        with open(str(locales) + '/' + self._base_pot) as fp:
            msgid_lines: list[str] = [line for line in fp.readlines() if 'msgid' in line]

        return len(msgid_lines) - 1  # don't count the first line which contains the metadata

    def get_language_by_name(self, name: str) -> Language:
        """
        Get a language object by its name, e.g., English
        """

        # noinspection PyBroadException
        try:
            return next(filter(lambda x: x.name_en == name, self._translated_languages))
        except Exception:
            raise ValueError('No language with name found: ' + name)

    def get_language_by_code(self, code: str) -> Language:
        """
        Get a language object by its code, e.g., en
        """

        # noinspection PyBroadException
        try:
            return next(filter(lambda x: x.code == code, self._translated_languages))
        except Exception:
            raise ValueError('No language with code "' + code + '" found')

    @staticmethod
    def activate(language: Language) -> None:
        """
        Set the provided language as the current translation
        """
        # The install() call has the side effect of assigning GNUTranslations.gettext to builtins._
        language.translation.install()

    @staticmethod
    def _get_locales_dir() -> Path:
        """
        Get the locale directory path
        """
        cur_path:    Path = Path(__file__).parent.parent
        locales_dir: Path = Path.joinpath(cur_path, 'locales')

        return locales_dir

    def _provided_translations(self) -> list[str]:
        """
        Get a list of all known languages
        """
        locales_dir: Path = self._get_locales_dir()

        filenames:         list[str] = os.listdir(locales_dir)
        translation_files: list[str] = []

        for filename in filenames:
            if (len(filename) == 2) or filename in {'pt_BR', 'zh-CN', 'zh-TW'}:
                translation_files.append(filename)

        return translation_files

class _DeferredTranslation:
    def __init__(self, message: str) -> None:
        self.message: str = message

    @override
    def __str__(self) -> str:
        # builtins._ is changed from _DeferredTranslation to GNUTranslations.gettext after
        # Language.activate() is called
        return self.message if builtins._ is _DeferredTranslation else builtins._(self.message)  # type: ignore[attr-defined]

    def format(self, *args) -> str:
        return self.message.format(*args)

def tr(message: str) -> str:
    return str(_DeferredTranslation(message))

builtins._ = _DeferredTranslation  # type: ignore[attr-defined]
translation_handler: TranslationHandler = TranslationHandler()
