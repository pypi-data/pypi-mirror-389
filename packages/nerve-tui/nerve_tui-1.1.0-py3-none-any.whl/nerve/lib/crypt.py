# SPDX-FileCopyrightText: 2023 CELESTIFYX Team
# SPDX-License-Identifier: GPL-3.0-or-later

import base64
import ctypes
import os

from pathlib import Path
from cryptography.fernet import (Fernet, InvalidToken)
from cryptography.hazmat.primitives.kdf.argon2 import Argon2id

from nerve.lib.output import debug

libcrypt: ctypes.CDLL = ctypes.CDLL('libcrypt.so')

libcrypt.crypt.argtypes = [ctypes.c_char_p, ctypes.c_char_p]
libcrypt.crypt.restype  = ctypes.c_char_p

libcrypt.crypt_gensalt.argtypes = [ctypes.c_char_p, ctypes.c_ulong, ctypes.c_char_p, ctypes.c_int]
libcrypt.crypt_gensalt.restype  = ctypes.c_char_p

LOGIN_DEFS: Path = Path('/etc/login.defs')

def _search_login_defs(key: str) -> str | None:
    defs: str = LOGIN_DEFS.read_text()

    for line in defs.split(sep='\n'):
        line: str = line.strip()

        if line.startswith('#'):
            continue

        if line.startswith(key):
            value: str = line.split(' ')[1]
            return value

    return None

def crypt_gen_salt(prefix: str | bytes, rounds: int) -> bytes:
    if isinstance(prefix, str):
        prefix = prefix.encode()

    setting: bytes | None = libcrypt.crypt_gensalt(prefix, rounds, None, 0)

    if not setting:
        raise ValueError('crypt_gensalt() returned NULL for prefix ' + repr(prefix) + ' and rounds ' + str(rounds))

    return setting

def crypt_yescrypt(plaintext: str) -> str:
    """
    By default, chpasswd in Arch uses PAM to hash the password with crypt_yescrypt
    the PAM code https://github.com/linux-pam/linux-pam/blob/master/modules/pam_unix/support.c
    shows that the hashing rounds are determined from YESCRYPT_COST_FACTOR in /etc/login.defs
    If no value was specified (or commented out) a default of 5 is choosen
    """
    value: str | None = _search_login_defs(key='YESCRYPT_COST_FACTOR')

    rounds: int = int(value) if value is not None else 5
    rounds = max(3, min(rounds, 11))

    debug('Creating yescrypt hash with rounds ' + str(rounds))

    enc_plaintext: bytes = plaintext.encode()
    salt:          bytes = crypt_gen_salt(prefix='$y$', rounds=rounds)
    crypt_hash:    bytes | None = libcrypt.crypt(enc_plaintext, salt)

    if not crypt_hash:
        raise ValueError('crypt() returned NULL')

    return crypt_hash.decode()

def _get_fernet(salt: bytes, password: str) -> Fernet:
    # https://cryptography.io/en/latest/hazmat/primitives/key-derivation-functions/#argon2id
    kdf: Argon2id = Argon2id(salt=salt, length=32, iterations=1, lanes=4, memory_cost=64 * 1024, ad=None, secret=None)
    key: bytes = base64.urlsafe_b64encode(kdf.derive(password.encode()))

    return Fernet(key)

def encrypt(password: str, data: str) -> str:
    salt: bytes  = os.urandom(16)
    f: Fernet = _get_fernet(salt, password)
    token: bytes = f.encrypt(data.encode())
 
    encoded_token: str = base64.urlsafe_b64encode(token).decode()
    encoded_salt:  str = base64.urlsafe_b64encode(salt).decode()
 
    return '$argon2id$' + encoded_salt + '$' + encoded_token

def decrypt(data: str, password: str) -> str:
    (_, algo, encoded_salt, encoded_token) = data.split('$')

    salt:  bytes = base64.urlsafe_b64decode(encoded_salt)
    token: bytes = base64.urlsafe_b64decode(encoded_token)
 
    if algo != 'argon2id':
        raise ValueError('Unsupported algorithm ' + repr(algo))
 
    f: Fernet = _get_fernet(salt, password)

    try:
        decrypted: bytes = f.decrypt(token)
    except InvalidToken:
        raise ValueError('Invalid password')
 
    return decrypted.decode()
