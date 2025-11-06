# SPDX-FileCopyrightText: 2023 CELESTIFYX Team
# SPDX-License-Identifier: GPL-3.0-or-later

from dataclasses import (dataclass, field)
from typing import (NotRequired, TypedDict, override)

from nerve.lib.crypt import crypt_yescrypt

UserSerialization = TypedDict('UserSerialization', {
    'username': str,
    '!password': NotRequired[str],
    'sudo': bool,
    'groups': list[str],
    'enc_password': str | None
})

class Password:
    def __init__(self, plaintext: str = '', enc_password: str | None = None) -> None:
        if plaintext:
            enc_password = crypt_yescrypt(plaintext)

        if not plaintext and not enc_password:
            raise ValueError('Either plaintext or enc_password must be provided')

        self._plaintext: str = plaintext
        self.enc_password: str | None = enc_password

    @property
    def plaintext(self) -> str:
        return self._plaintext

    @plaintext.setter
    def plaintext(self, value: str) -> None:
        self._plaintext   = value
        self.enc_password = crypt_yescrypt(value)

    @override
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Password):
            return NotImplemented

        return (self._plaintext == other._plaintext) if self._plaintext and other._plaintext else (self.enc_password == other.enc_password)

    def hidden(self) -> str:
        return ('*' * len(self._plaintext)) if self._plaintext else ('*' * 8)

@dataclass
class User:
    username: str
    password: Password
    sudo: bool
    groups: list[str] = field(default_factory=list)

    @override
    def __str__(self) -> str:
        # safety overwrite to make sure the password is not leaked
        return 'User(self.username=' + repr(self.username) + ', self.sudo=' + str(self.sudo) + ', self.groups=' + str(self.groups) + ')'

    def table_data(self) -> dict[str, str | bool | list[str]]:
        return {
            'username': self.username,
            'password': self.password.hidden(),
            'sudo':     self.sudo,
            'groups':   self.groups
        }

    def json(self) -> UserSerialization:
        return {
            'username':     self.username,
            'enc_password': self.password.enc_password,
            'sudo':         self.sudo,
            'groups':       self.groups
        }

    @classmethod
    def parse_arguments(cls, args: list[UserSerialization]) -> list['User']:
        users: list[User] = []

        for entry in args:
            username: str | None = entry.get('username')
            password: Password | None = None
            groups: list[str] = entry.get('groups', [])
            plaintext: str | None = entry.get('!password')
            enc_password: str | None = entry.get('enc_password')

            # DEPRECATED: backwards compatibility
            if plaintext:
                password = Password(plaintext=plaintext)
            elif enc_password:
                password = Password(enc_password=enc_password)

            if not username or not password:
                continue

            user: User = User(username=username, password=password, sudo=entry.get('sudo', False), groups=groups)
            users.append(user)

        return users
