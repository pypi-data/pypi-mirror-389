# SPDX-FileCopyrightText: 2023 CELESTIFYX Team
# SPDX-License-Identifier: GPL-3.0-or-later

from typing import (TYPE_CHECKING, override)

from nerve.default_profiles.profile import (Profile, ProfileType)

if TYPE_CHECKING:
    from nerve.lib.installer import Installer

class MariadbProfile(Profile):
    def __init__(self) -> None:
        super().__init__(name='Mariadb', profile_type=ProfileType.ServerType)

    @property
    @override
    def packages(self) -> list[str]:
        return ['mariadb']

    @property
    @override
    def services(self) -> list[str]:
        return ['mariadb']

    @override
    def post_install(self, install_session: 'Installer') -> None:
        install_session.arch_chroot('mariadb-install-db --user=mysql --basedir=/usr --datadir=/var/lib/mysql')
