# SPDX-FileCopyrightText: 2023 CELESTIFYX Team
# SPDX-License-Identifier: GPL-3.0-or-later

from typing import override

from nerve.default_profiles.profile import (Profile, ProfileType)
from nerve.lib.translationhandler import tr

class XorgProfile(Profile):
    def __init__(self, name: str = 'Xorg', profile_type: ProfileType = ProfileType.Xorg, advanced: bool = False) -> None:
        super().__init__(name=name, profile_type=profile_type, support_gfx_driver=True, advanced=advanced)

    @override
    def preview_text(self) -> str:
        text: str = tr('Environment type: {env_type}'.format(env_type=str(self.profile_type.value)))

        if packages := self.packages_text():
            text += '\n' + packages

        return text

    @property
    @override
    def packages(self) -> list[str]:
        return ['xorg-server']
