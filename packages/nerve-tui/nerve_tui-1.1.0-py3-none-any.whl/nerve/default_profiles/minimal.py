# SPDX-FileCopyrightText: 2023 CELESTIFYX Team
# SPDX-License-Identifier: GPL-3.0-or-later

from nerve.default_profiles.profile import (Profile, ProfileType)

class MinimalProfile(Profile):
    def __init__(self) -> None:
        super().__init__(name='Minimal', profile_type=ProfileType.Minimal)
