# SPDX-FileCopyrightText: 2023 CELESTIFYX Team
# SPDX-License-Identifier: GPL-3.0-or-later

from typing import (TYPE_CHECKING, NamedTuple)

from nerve.applications import Application
from nerve.lib.output import debug
from nerve.lib.models.application import Fonts

if TYPE_CHECKING:
    from nerve.lib.installer import Installer

class FontPackage(NamedTuple):
    packages: list[str]

class FontsApplication(Application):
    _font_packages: dict[Fonts, FontPackage] = {
        Fonts.NOTO: FontPackage([
            'noto-fonts',
            'noto-fonts-cjk',
            'noto-fonts-emoji',
            'noto-fonts-extra'
        ]),

        Fonts.JETBRAINS_MONO: FontPackage([
            'ttf-jetbrains-mono',
            'ttf-jetbrains-mono-nerd'
        ]),

        Fonts.LIBERATION: FontPackage([
            'ttf-liberation',
            'ttf-liberation-mono-nerd'
        ]),

        Fonts.DEJAVU: FontPackage([
            'ttf-dejavu',
            'ttf-dejavu-nerd'
        ]),

        Fonts.FIRA: FontPackage([
            'ttf-fira-code',
            'ttf-fira-mono',
            'ttf-fira-sans'
        ]),

        Fonts.ADOBE_SOURCE: FontPackage([
            'adobe-source-code-pro-fonts',
            'adobe-source-sans-fonts',
            'adobe-source-serif-fonts'
        ]),

        Fonts.UBUNTU_FAMILY: FontPackage(['ttf-ubuntu-font-family']),
        Fonts.UBUNTU_NERD: FontPackage(['ttf-ubuntu-nerd']),
        Fonts.IOSEVKA_NERD: FontPackage(['ttf-iosevka-nerd']),
        Fonts.HACK: FontPackage(['ttf-hack']),
        Fonts.HACK_NERD: FontPackage(['ttf-hack-nerd'])
    }

    @classmethod
    def _fonts_packages(cls, font_name: Fonts) -> list[str]:
        return cls._font_packages.get(font_name, FontPackage([])).packages

    def install(self, install_session: 'Installer', selected_fonts: list[str]) -> None:
        if not (selected_fonts := [Fonts(f) for f in selected_fonts if f in Fonts._value2member_map_]):
            return

        debug('Installing fonts: ' + ', '.join(f.value for f in selected_fonts))  # type: ignore

        if packages := [pkg for font in selected_fonts for pkg in self._fonts_packages(font)]:
            install_session.add_additional_packages(packages)
