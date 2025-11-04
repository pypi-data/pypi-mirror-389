# SPDX-FileCopyrightText: 2023 CELESTIFYX Team
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

import shlex

from typing import Any
from dataclasses import dataclass
from pathlib import Path
from subprocess import (CalledProcessError, CompletedProcess)

from nerve.lib.disk.utils import (get_lsblk_info, umount)
from nerve.lib.models import LsblkInfo
from nerve.lib.models.device import DEFAULT_ITER_TIME
from nerve.lib.exceptions import (DiskError, SysCallError)
from nerve.lib.general import (SysCommand, SysCommandWorker, generate_password, run)
from nerve.lib.models.users import Password
from nerve.lib.output import (debug, info)

@dataclass
class Luks2:
    luks_dev_path: Path
    mapper_name: str | None = None
    password: Password | None = None
    key_file: Path | None = None
    auto_unmount: bool = False

    @property
    def mapper_dev(self) -> Path | None:
        return Path('/dev/mapper/' + str(self.mapper_name)) if self.mapper_name else None

    def is_luks_device(self) -> bool:
        try:
            SysCommand('cryptsetup isLuks ' + str(self.luks_dev_path))
            return True
        except SysCallError:
            return False

    def erase(self) -> None:
        debug('Erasing luks partition: ' + str(self.luks_dev_path))

        worker: SysCommandWorker = SysCommandWorker('cryptsetup erase ' + str(self.luks_dev_path))
        worker.poll()
        worker.write(data=b'YES\n', line_ending=False)

    def __enter__(self) -> None:
        self.unlock(self.key_file)

    def __exit__(self, *_: Any) -> None:
        if self.auto_unmount:
            self.lock()

    def _password_bytes(self) -> bytes:
        if not self.password:
            raise ValueError('Password for luks2 device was not specified')

        return self.password if isinstance(self.password, bytes) else bytes(self.password.plaintext, 'UTF-8')

    def _get_passphrase_args(self, key_file: Path | None = None) -> tuple[list[str], bytes | None]:
        key_file: Path | None = key_file or self.key_file
        return (['--key-file', str(key_file)], None) if key_file else [], self._password_bytes()

    def encrypt(self, key_size: int = 512, hash_type: str = 'sha512', iter_time: int = DEFAULT_ITER_TIME, key_file: Path | None = None) -> Path | None:
        debug('Luks2 encrypting: ' + str(self.luks_dev_path))
        (key_file_arg, passphrase) = self._get_passphrase_args(key_file)

        cmd: list[str] = [
            'cryptsetup',
            '--batch-mode',
            '--verbose',
            '--type', 'luks2',
            '--pbkdf', 'argon2id',
            '--hash', hash_type,
            '--key-size', str(key_size),
            '--iter-time', str(iter_time),
            *key_file_arg,
            '--use-urandom',
            'luksFormat', str(self.luks_dev_path)
        ]

        debug('cryptsetup format: ' + shlex.join(cmd))

        try:
            result: CompletedProcess[bytes] = run(cmd, input_data=passphrase)
        except CalledProcessError as err:
            output: str = err.stdout.decode().rstrip()
            raise DiskError('Could not encrypt volume "' + str(self.luks_dev_path) + '": ' + output)

        debug('cryptsetup luksFormat output: ' + str(result.stdout.decode().rstrip()))
        self.key_file = key_file

        return key_file

    def _get_luks_uuid(self) -> str:
        command: str = 'cryptsetup luksUUID ' + str(self.luks_dev_path)

        try:
            return SysCommand(command).decode()
        except SysCallError as err:
            info('Unable to get UUID for Luks device: ' + str(self.luks_dev_path))
            raise err

    def is_unlocked(self) -> bool:
        return (mapper_dev := self.mapper_dev) is not None and mapper_dev.is_symlink()

    def unlock(self, key_file: Path | None = None) -> None:
        """
        Unlocks the luks device, an optional key file location for unlocking can be specified,
        otherwise a default location for the key file will be used.

        :param key_file: An alternative key file
        :type key_file: Path
        """
        debug('Unlocking luks2 device: ' + str(self.luks_dev_path))

        if not self.mapper_name:
            raise ValueError('mapper name missing')

        (key_file_arg, passphrase) = self._get_passphrase_args(key_file)

        cmd: list[str] = [
            'cryptsetup', 'open',
            str(self.luks_dev_path),
            str(self.mapper_name),
            *key_file_arg,
            '--type', 'luks2'
        ]

        result: CompletedProcess[bytes] = run(cmd, input_data=passphrase)
        debug('cryptsetup open output: ' + str(result.stdout.decode().rstrip()))

        if not self.is_unlocked():
            raise DiskError('Failed to open luks2 device: ' + str(self.luks_dev_path))

    def lock(self) -> None:
        umount(self.luks_dev_path)

        # Get crypt-information about the device by doing a reverse lookup starting with the partition path
        # For instance: /dev/sda
        lsblk_info: LsblkInfo = get_lsblk_info(self.luks_dev_path)

        # For each child (subpartition/sub-device)
        for child in lsblk_info.children:
            # Unmount the child location
            for mountpoint in child.mountpoints:
                debug('Unmounting ' + str(mountpoint))
                umount(mountpoint, recursive=True)

            # And close it if possible.
            debug("Closing crypt device " + child.name)
            SysCommand("cryptsetup close " + child.name)

    def create_keyfile(self, target_path: Path, override: bool = False) -> None:
        """
        Routine to create keyfiles, so it can be moved elsewhere
        """
        if not self.mapper_name:
            raise ValueError('Mapper name must be provided')

        # Once we store the key as ./xyzloop.key systemd-cryptsetup can
        # automatically load this key if we name the device to "xyzloop"
        kf_path:       Path = Path('/etc/cryptsetup-keys.d/' + str(self.mapper_name) + '.key')
        key_file:      Path = target_path / kf_path.relative_to(kf_path.root)
        crypttab_path: Path = target_path / 'etc/crypttab'

        if key_file.exists():
            if not override:
                info('Key file ' + str(key_file) + ' already exists, keeping existing')
                return

            info('Key file ' + str(key_file) + ' already exists, overriding')

        key_file.parent.mkdir(parents=True, exist_ok=True)
        pwd: str = generate_password(length=512)

        key_file.write_text(pwd)
        key_file.chmod(0o400)

        self._add_key(key_file)
        self._crypttab(crypttab_path, kf_path, options=["luks", "key-slot=1"])

    def _add_key(self, key_file: Path) -> None:
        debug('Adding additional key-file ' + str(key_file))

        worker: SysCommandWorker = SysCommandWorker('cryptsetup -q -v luksAddKey ' + str(self.luks_dev_path) + ' ' + str(key_file))
        pw_injected: bool = False

        while worker.is_alive():
            if b'Enter any existing passphrase' in worker and not pw_injected:
                worker.write(self._password_bytes())
                pw_injected = True

        if worker.exit_code != 0:
            raise DiskError('Could not add encryption key ' + str(key_file) + ' to ' + str(self.luks_dev_path) + ': ' + worker.decode())

    def _crypttab(self, crypttab_path: Path, key_file: Path, options: list[str]) -> None:
        debug('Adding crypttab entry for key ' + str(key_file))

        with open(crypttab_path, 'a') as crypttab:
            opt:  str = ','.join(options)
            uuid: str = self._get_luks_uuid()
            row:  str = str(self.mapper_name) + " UUID=" + uuid + " " + str(key_file) + " " + opt + "\n"

            crypttab.write(row)
