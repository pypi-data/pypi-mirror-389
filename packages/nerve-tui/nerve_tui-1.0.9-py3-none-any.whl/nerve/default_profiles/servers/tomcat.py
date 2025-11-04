# SPDX-FileCopyrightText: 2023 CELESTIFYX Team
# SPDX-License-Identifier: GPL-3.0-or-later

from typing import override

from nerve.default_profiles.profile import (Profile, ProfileType)

class TomcatProfile(Profile):
    def __init__(self) -> None:
        super().__init__(name='Tomcat', profile_type=ProfileType.ServerType)

    @property
    @override
    def packages(self) -> list[str]:
        return ['tomcat10']

    @property
    @override
    def services(self) -> list[str]:
        return ['tomcat10']
