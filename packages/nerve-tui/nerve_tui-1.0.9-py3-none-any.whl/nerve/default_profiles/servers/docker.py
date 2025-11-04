# SPDX-FileCopyrightText: 2023 CELESTIFYX Team
# SPDX-License-Identifier: GPL-3.0-or-later

from typing import (TYPE_CHECKING, override)

from nerve.default_profiles.profile import (Profile, ProfileType)

if TYPE_CHECKING:
    from nerve.lib.installer import Installer

class DockerProfile(Profile):
    def __init__(self) -> None:
        super().__init__(name='Docker', profile_type=ProfileType.ServerType)

    @property
    @override
    def packages(self) -> list[str]:
        return ['docker']

    @property
    @override
    def services(self) -> list[str]:
        return ['docker']

    @override
    def post_install(self, install_session: 'Installer') -> None:
        from nerve.lib.args import config_handler

        if auth_config := config_handler.config.auth_config:
            for user in auth_config.users:
                install_session.arch_chroot('usermod -a -G docker ' + user.username)
