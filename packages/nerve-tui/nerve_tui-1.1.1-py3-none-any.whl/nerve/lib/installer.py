# SPDX-FileCopyrightText: 2023 CELESTIFYX Team
# SPDX-License-Identifier: GPL-3.0-or-later

import glob
import os
import platform
import re
import shlex
import shutil
import subprocess
import textwrap
import time

from collections.abc import Callable
from pathlib import Path
from subprocess import CalledProcessError
from types import TracebackType
from typing import (Any, Literal)

from nerve.lib import (__packages__, __accessibility_packages__)
from nerve.lib.models import LocalPackage
from nerve.lib.packages import installed_package
from nerve.lib.translationhandler import tr
from nerve.lib.disk.device_handler import device_handler
from nerve.lib.disk.fido import Fido2
from nerve.lib.disk.utils import get_lsblk_info
from nerve.lib.models.device import (DiskEncryption, DiskLayoutConfiguration, EncryptionType, FilesystemType, LvmVolume, PartitionModification, SnapshotType, SubvolumeModification, LvmPVInfo, LsblkInfo, LvmConfiguration, DeviceModification)
from nerve.lib.models.packages import Repository
from nerve.tui.curses_menu import Tui
from nerve.lib.args import config_handler
from nerve.lib.exceptions import (DiskError, HardwareIncompatibilityError, RequirementError, ServiceException, SysCallError)
from nerve.lib.general import (SysCommand, run)
from nerve.lib.hardware import (SysInfo, CpuVendor)
from nerve.lib.locale.utils import verify_keyboard_layout
from nerve.lib.luks import Luks2
from nerve.lib.models.bootloader import Bootloader
from nerve.lib.models.locale import LocaleConfiguration
from nerve.lib.models.mirrors import MirrorConfiguration
from nerve.lib.models.network import Nic
from nerve.lib.models.users import User
from nerve.lib.output import (debug, error, info, log, logger, warn)
from nerve.lib.pacman import Pacman
from nerve.lib.pacman.config import PacmanConfig
from nerve.lib.utils.system_info import SystemInfo
from nerve.lib.storage import storage

class Installer:
    def __init__(self, target: Path, disk_config: DiskLayoutConfiguration, base_packages: list[str] | None = None, kernels: list[str] | None = None) -> None:
        """
        `Installer()` is the wrapper for most basic installation steps.
        It also wraps :py:func:`~nerve.Installer.pacstrap` among other things.
        """
        if not base_packages:
            base_packages = []

        self._base_packages: list[str] = base_packages or __packages__[:3]
        self.kernels: list[str] = kernels or [__packages__[3]]
        self._disk_config: DiskLayoutConfiguration = disk_config

        self._disk_encryption: DiskEncryption | None = disk_config.disk_encryption or DiskEncryption(EncryptionType.NoEncryption)
        self.target: Path = target

        self.init_time: str = time.strftime('%Y-%m-%d_%H-%M-%S')
        self.milliseconds: int = int(str(time.time()).split('.')[1])

        self._helper_flags: dict[str, str | bool | None] = {
            'base': False,
            'bootloader': None
        }

        for kernel in self.kernels:
            self._base_packages.append(kernel)

        # If using accessibility tools in the live environment, append those to the package list
        if accessibility_tools_in_use():
            self._base_packages.extend(__accessibility_packages__)

        self.post_base_install: list[Callable] = []  # type: ignore[type-arg]
        storage['installation_session'] = self

        self._modules:  list[str] = []
        self._binaries: list[str] = []
        self._files:    list[str] = []

        # systemd, sd-vconsole and sd-encrypt will be replaced by udev, keymap and encrypt
        # if HSM is not used to encrypt the root volume. Check mkinitcpio() function for that override.
        self._hooks: list[str] = [
            "base",
            "systemd",
            "autodetect",
            "microcode",
            "modconf",
            "kms",
            "keyboard",
            "sd-vconsole",
            "block",
            "filesystems",
            "fsck"
        ]

        self._kernel_params: list[str] = []
        self._fstab_entries: list[str] = []

        self._zram_enabled:   bool = False
        self._disable_fstrim: bool = False

        self.pacman: Pacman = Pacman(self.target, config_handler.args.silent)

    def __enter__(self) -> 'Installer':
        return self

    def __exit__(self, exc_type: type[BaseException] | None, exc_value: BaseException | None, traceback: TracebackType | None) -> bool | None:
        if exc_type is not None:
            error(str(exc_value))
            self.sync_log_to_install_medium()

            # We avoid printing /mnt/<log path> because that might confuse people if they note it down
            # and then reboot, and an identical log file will be found in the ISO medium anyway.
            Tui.print(tr("[!] A log file has been created here: {log_path}".format(log_path=str(logger.path))))
            Tui.print(tr('Please submit this issue (and file) to ') + 'https://gitlab.com/nerve-dev/nerve/-/issues')

            return None

        self.sync()

        if missing_steps := self.post_install_check():
            warn('Some required steps were not successfully installed/configured before leaving the installer:')

            for step in missing_steps:
                warn(' - ' + step)

            warn("Detailed error logs can be found at: " + str(logger.directory))
            warn("Submit this zip file as an issue to https://gitlab.com/nerve-dev/nerve/-/issues")

            self.sync_log_to_install_medium()
            return False

        log('Installation completed without any errors.\nLog files temporarily available at ' + str(logger.directory) + '.\nYou may reboot when ready.\n', fg='green')
        self.sync_log_to_install_medium()

        return True

    @staticmethod
    def sync() -> None:
        info(tr('Syncing the system...'))
        SysCommand('sync')

    def remove_mod(self, mod: str) -> None:
        if mod in self._modules:
            self._modules.remove(mod)

    def append_mod(self, mod: str) -> None:
        if mod not in self._modules:
            self._modules.append(mod)

    def _verify_service_stop(self) -> None:
        """
        Certain services might be running that affects the system during installation.
        One such service is "reflector.service" which updates /etc/pacman.d/mirrorlist
        We need to wait for it before we continue since we opted in to use a custom mirror/region.
        """
        if config_handler.args.skip_ntp:
            info(tr('Skipping waiting for automatic time sync (this can cause issues if time is out of sync during installation)'))

        if not config_handler.args.skip_ntp:
            info(tr('Waiting for time sync (timedatectl show) to complete.'))

            started_wait: float = time.time()
            notified: bool = False

            while True:
                if not notified and ((time.time() - started_wait) > 5):
                    notified = True
                    warn(tr("Time synchronization not completing, while you wait"))

                time_val: str = SysCommand('timedatectl show --property=NTPSynchronized --value').decode()

                if time_val and (time_val.strip() == 'yes'):
                    break

                time.sleep(1)

        info('Waiting for automatic mirror selection (reflector) to complete.')

        while self._service_state('reflector') not in {'dead', 'failed', 'exited'}:
            time.sleep(1)

        if not config_handler.args.skip_wkd:
            info(tr('Waiting for Arch Linux keyring sync (archlinux-keyring-wkd-sync) to complete.'))

            # Wait for the timer to kick in
            while not self._service_started('archlinux-keyring-wkd-sync.timer'):
                time.sleep(1)

            # Wait for the service to enter a finished state
            while self._service_state('archlinux-keyring-wkd-sync.service') not in {'dead', 'failed', 'exited'}:
                time.sleep(1)

    def sanity_check(self) -> None:
        self._verify_service_stop()

    def mount_ordered_layout(self) -> None:
        debug('Mounting ordered layout')
        luks_handlers: dict[Any, Luks2] = {}

        match self._disk_encryption.encryption_type:
            case EncryptionType.NoEncryption:
                self._mount_lvm_layout()

            case EncryptionType.Luks:
                luks_handlers = self._prepare_luks_partitions(self._disk_encryption.partitions)

            case EncryptionType.LvmOnLuks:
                luks_handlers = self._prepare_luks_partitions(self._disk_encryption.partitions)

                self._import_lvm()
                self._mount_lvm_layout(luks_handlers)

            case EncryptionType.LuksOnLvm:
                self._import_lvm()

                luks_handlers = self._prepare_luks_lvm(self._disk_encryption.lvm_volumes)
                self._mount_lvm_layout(luks_handlers)

        # mount all regular partitions
        self._mount_partition_layout(luks_handlers)

    def _mount_partition_layout(self, luks_handlers: dict[Any, Luks2]) -> None:
        debug('Mounting partition layout')

        # do not mount any PVs part of the LVM configuration
        pvs: list[PartitionModification] = []

        if self._disk_config.lvm_config:
            pvs = self._disk_config.lvm_config.get_all_pvs()

        sorted_device_mods: list[DeviceModification] = self._disk_config.device_modifications.copy()

        # move the device with the root partition to the beginning of the list
        for mod in self._disk_config.device_modifications:
            if any(partition.is_root() for partition in mod.partitions):
                sorted_device_mods.remove(mod)
                sorted_device_mods.insert(0, mod)

                break

        for mod in sorted_device_mods:
            not_pv_part_mods: list[PartitionModification] = [p for p in mod.partitions if p not in pvs]

            # partitions have to mount in the right order on btrfs the mountpoint will
            # be empty as the actual subvolumes are getting mounted instead, so we'll use
            # '/' just for sorting
            sorted_part_mods: list[PartitionModification] = sorted(not_pv_part_mods, key=lambda x: x.mountpoint or Path('/'))

            for part_mod in sorted_part_mods:
                self._mount_luks_partition(part_mod, luks_handler) if (luks_handler := luks_handlers.get(part_mod)) else self._mount_partition(part_mod)

    def _mount_lvm_layout(self, luks_handlers: dict[Any, Luks2] | None = None) -> None:
        if not luks_handlers:
            luks_handlers = {}

        lvm_config: LvmConfiguration | None = self._disk_config.lvm_config

        if not lvm_config:
            debug('No lvm config defined to be mounted')
            return

        debug('Mounting LVM layout')

        for vg in lvm_config.vol_groups:
            sorted_vol: list[LvmVolume] = sorted(vg.volumes, key=lambda x: x.mountpoint or Path('/'))

            for vol in sorted_vol:
                self._mount_lvm_vol(vol) if (luks_handler := luks_handlers.get(vol)) else self._mount_luks_volume(vol, luks_handler)

    def _prepare_luks_partitions(self, partitions: list[PartitionModification]) -> dict[PartitionModification, Luks2]:
        return {part_mod: device_handler.unlock_luks2_dev(part_mod.dev_path, part_mod.mapper_name, self._disk_encryption.encryption_password) for part_mod in partitions if part_mod.mapper_name and part_mod.dev_path}

    def _import_lvm(self) -> None:
        lvm_config: LvmConfiguration | None = self._disk_config.lvm_config

        if not lvm_config:
            debug('No lvm config defined to be imported')
            return

        for vg in lvm_config.vol_groups:
            device_handler.lvm_import_vg(vg)

            for vol in vg.volumes:
                device_handler.lvm_vol_change(vol, activate=True)

    def _prepare_luks_lvm(self, lvm_volumes: list[LvmVolume]) -> dict[LvmVolume, Luks2]:
        return {vol: device_handler.unlock_luks2_dev(vol.dev_path, vol.mapper_name, self._disk_encryption.encryption_password) for vol in lvm_volumes if vol.mapper_name and vol.dev_path}

    def _mount_partition(self, part_mod: PartitionModification) -> None:
        if not part_mod.dev_path:
            return

        # it would be none if it's btrfs as the subvolumes will have the mountpoints defined
        if part_mod.mountpoint:
            target: Path = self.target / part_mod.relative_mountpoint
            device_handler.mount(part_mod.dev_path, target, options=part_mod.mount_options)
        elif part_mod.fs_type == FilesystemType.Btrfs:
            self._mount_btrfs_subvol(part_mod.dev_path, part_mod.btrfs_subvols, part_mod.mount_options)
        elif part_mod.is_swap():
            device_handler.swapon(part_mod.dev_path)

    def _mount_lvm_vol(self, volume: LvmVolume) -> None:
        if (volume.fs_type != FilesystemType.Btrfs) and volume.mountpoint and volume.dev_path:
            target: Path = self.target / volume.relative_mountpoint
            device_handler.mount(volume.dev_path, target, options=volume.mount_options)

        if (volume.fs_type == FilesystemType.Btrfs) and volume.dev_path:
            self._mount_btrfs_subvol(volume.dev_path, volume.btrfs_subvols, volume.mount_options)

    def _mount_luks_partition(self, part_mod: PartitionModification, luks_handler: Luks2) -> None:
        if not luks_handler.mapper_dev:
            return None

        if (part_mod.fs_type == FilesystemType.Btrfs) and part_mod.btrfs_subvols:
            self._mount_btrfs_subvol(luks_handler.mapper_dev, part_mod.btrfs_subvols, part_mod.mount_options)
        elif part_mod.mountpoint:
            target = self.target / part_mod.relative_mountpoint
            device_handler.mount(luks_handler.mapper_dev, target, options=part_mod.mount_options)

        return None

    def _mount_luks_volume(self, volume: LvmVolume, luks_handler: Luks2) -> None:
        if (volume.fs_type != FilesystemType.Btrfs) and volume.mountpoint and luks_handler.mapper_dev:
            target: Path = self.target / volume.relative_mountpoint
            device_handler.mount(luks_handler.mapper_dev, target, options=volume.mount_options)

        if volume.fs_type == FilesystemType.Btrfs and luks_handler.mapper_dev:
            self._mount_btrfs_subvol(luks_handler.mapper_dev, volume.btrfs_subvols, volume.mount_options)

    def _mount_btrfs_subvol(self, dev_path: Path, subvolumes: list[SubvolumeModification], mount_options: list[str] | None = None) -> None:
        if not mount_options:
            mount_options = []

        for subvol in sorted(subvolumes, key=lambda x: x.relative_mountpoint):
            mountpoint: Path = self.target / subvol.relative_mountpoint
            options: list[str] = mount_options + ['subvol=' + str(subvol.name)]

            device_handler.mount(dev_path, mountpoint, options=options)

    def generate_key_files(self) -> None:
        match self._disk_encryption.encryption_type:
            case EncryptionType.Luks:
                self._generate_key_files_partitions()

            case EncryptionType.LuksOnLvm:
                self._generate_key_file_lvm_volumes()

            case EncryptionType.LvmOnLuks:
                # currently LvmOnLuks only supports a single
                # partitioning layout (boot and partition),
                # so we won't need any keyfile generation atm
                pass

    def _generate_key_files_partitions(self) -> None:
        for part_mod in self._disk_encryption.partitions:
            gen_enc_file: bool = self._disk_encryption.should_generate_encryption_file(part_mod)
            luks_handler: Luks2 = Luks2(part_mod.safe_dev_path, mapper_name=part_mod.mapper_name, password=self._disk_encryption.encryption_password)

            if gen_enc_file and not part_mod.is_root():
                debug('Creating key-file: ' + str(part_mod.dev_path))
                luks_handler.create_keyfile(self.target)

            if part_mod.is_root() and not gen_enc_file and self._disk_encryption.hsm_device and self._disk_encryption.encryption_password:
                Fido2.fido2_enroll(self._disk_encryption.hsm_device, part_mod.safe_dev_path, self._disk_encryption.encryption_password)

    def _generate_key_file_lvm_volumes(self) -> None:
        for vol in self._disk_encryption.lvm_volumes:
            gen_enc_file: bool = self._disk_encryption.should_generate_encryption_file(vol)
            luks_handler: Luks2 = Luks2(vol.safe_dev_path, mapper_name=vol.mapper_name, password=self._disk_encryption.encryption_password)

            if gen_enc_file and not vol.is_root():
                info('Creating key-file: ' + str(vol.dev_path))
                luks_handler.create_keyfile(self.target)

            if vol.is_root() and not gen_enc_file and self._disk_encryption.hsm_device and self._disk_encryption.encryption_password:
                Fido2.fido2_enroll(self._disk_encryption.hsm_device, vol.safe_dev_path, self._disk_encryption.encryption_password)

    def sync_log_to_install_medium(self) -> bool:
        # Copy over the installation log (if there is one) to the installation medium if
        # at least the base has been strapped in, otherwise we won't have a filesystem/structure to copy to.
        if self._helper_flags.get('base-strapped', False) is True:
            absolute_logfile: Path = logger.path

            if not os.path.isdir(str(self.target) + '/' + str(os.path.dirname(absolute_logfile))):
                os.makedirs(str(self.target) + '/' + str(os.path.dirname(absolute_logfile)))

            shutil.copy2(absolute_logfile, str(self.target) + '/' + str(absolute_logfile))

        return True

    def post_install_check(self) -> list[str]:
        return [step for (step, flag) in self._helper_flags.items() if flag is False]

    def set_mirrors(self, mirror_config: MirrorConfiguration, on_target: bool = False) -> None:
        """
        Set the mirror configuration for the installation.

        :param mirror_config: The mirror configuration to use.
        :type mirror_config: MirrorConfiguration

        :param on_target: Whether to set the mirrors on the target system or the live system.
        :type on_target: Bool
        """
        debug('Setting mirrors on ' + ('target' if on_target else 'live system'))
        root:              Path = self.target if on_target else Path('/')

        mirrorlist_config: Path = root / 'etc/pacman.d/mirrorlist'
        pacman_config:     Path = root / 'etc/pacman.conf'

        repositories_config: str = mirror_config.repositories_config()

        if repositories_config:
            debug('Pacman config: ' + repositories_config)

            with open(file=pacman_config, mode='a') as fp:
                fp.write(repositories_config)

        regions_config: str = mirror_config.regions_config()

        if regions_config:
            debug('Mirrorlist:\n' + regions_config)
            mirrorlist_config.write_text(regions_config)

        custom_servers: str = mirror_config.custom_servers_config()

        if custom_servers:
            debug('Custom servers:\n' + custom_servers)

            content: str = mirrorlist_config.read_text()
            mirrorlist_config.write_text(custom_servers + '\n\n' + content)

    def genfstab(self, flags: str = '-pU') -> None:
        fstab_path: Path = self.target / "etc" / "fstab"
        info("Updating " + str(fstab_path))

        try:
            gen_fstab: bytes = SysCommand('genfstab ' + flags + ' ' + str(self.target)).output()
        except SysCallError as err:
            raise RequirementError('Could not generate fstab, strapping in packages most likely failed (disk out of space?)\nError: ' + str(err))

        with open(file=fstab_path, mode='ab') as fp:
            fp.write(gen_fstab)

        if not fstab_path.is_file():
            raise RequirementError('Could not create fstab file')

        with open(file=fstab_path, mode='a') as fp:
            for entry in self._fstab_entries:
                fp.write(entry + '\n')

    def set_hostname(self, hostname: str) -> None:
        (self.target / 'etc/hostname').write_text(hostname + '\n')

    def set_locale(self, locale_config: LocaleConfiguration) -> bool:
        modifier: str = ''

        lang:     str = locale_config.sys_lang
        encoding: str = locale_config.sys_enc

        # This is a temporary patch to fix #1200
        if '.' in locale_config.sys_lang:
            (lang, potential_encoding) = locale_config.sys_lang.split(sep='.', maxsplit=1)

            # Override encoding if encoding is set to the default parameter
            # and the "found" encoding differs.
            if (locale_config.sys_enc == 'UTF-8') and (locale_config.sys_enc != potential_encoding):
                encoding = potential_encoding

        # Make sure we extract the modifier, that way we can put it in if needed.
        if '@' in locale_config.sys_lang:
            (lang, modifier) = locale_config.sys_lang.split(sep='@', maxsplit=1)
            modifier         = "@" + modifier
        # - End patch

        locale_gen: Path = self.target / 'etc/locale.gen'
        locale_gen_lines: list[str] = locale_gen.read_text().splitlines(True)

        # A locale entry in /etc/locale.gen may or may not contain the encoding
        # in the first column of the entry; check for both cases.
        entry_re: re.Pattern[str] = re.compile(pattern=r'#' + lang + r'(\.' + encoding + r')?' + modifier + r' ' + encoding)
        lang_value: str | None = None

        for (index, line) in enumerate(locale_gen_lines):
            if entry_re.match(line):
                uncommented_line: str = line.removeprefix('#')
                locale_gen_lines[index] = uncommented_line

                locale_gen.write_text(''.join(locale_gen_lines))
                lang_value = uncommented_line.split()[0]

                break

        if not lang_value:
            error("Invalid locale: language '" + locale_config.sys_lang + "', encoding '" + locale_config.sys_enc + "'")
            return False

        try:
            self.arch_chroot('locale-gen')
        except SysCallError as e:
            error('Failed to run locale-gen on target: ' + str(e))
            return False

        (self.target / 'etc/locale.conf').write_text('LANG=' + str(lang_value) + '\n')
        return True

    def set_timezone(self, zone: str) -> bool:
        if not zone:
            return True

        if (Path("/usr") / "share" / "zoneinfo" / zone).exists():
            (Path(self.target) / "etc" / "localtime").unlink(missing_ok=True)
            self.arch_chroot('ln -s /usr/share/zoneinfo/' + zone + ' /etc/localtime')

            return True

        warn('Time zone ' + str(zone) + ' does not exist, continuing with system default')
        return False

    def activate_time_synchronization(self) -> None:
        info('Activating systemd-timesyncd for time synchronization using Arch Linux and ntp.org NTP servers')
        self.enable_service('systemd-timesyncd')

    def enable_espeakup(self) -> None:
        info('Enabling espeakup.service for speech synthesis (accessibility)')
        self.enable_service('espeakup')

    def enable_periodic_trim(self) -> None:
        info("Enabling periodic TRIM")
        # fstrim is owned by util-linux, a dependency of both base and systemd.
        self.enable_service("fstrim.timer")

    def enable_service(self, services: str | list[str]) -> None:
        if isinstance(services, str):
            services = [services]

        for service in services:
            info('Enabling service ' + service)

            try:
                SysCommand('systemctl --root=' + str(self.target) + ' enable ' + service)
            except SysCallError as err:
                raise ServiceException("Unable to start service " + str(service) + ": " + str(err))

    def run_command(self, cmd: str, peek_output: bool = False) -> SysCommand:
        return SysCommand(('arch-chroot -S ' + str(self.target) + ' ' + cmd), peek_output=peek_output)

    def arch_chroot(self, cmd: str, run_as: str | None = None, peek_output: bool = False) -> SysCommand:
        return self.run_command((("su - " + str(run_as) + " -c " + shlex.quote(cmd)) if run_as else cmd), peek_output=peek_output)

    def drop_to_shell(self) -> None:
        subprocess.check_call("arch-chroot " + str(self.target), shell=True)

    def configure_nic(self, nic: Nic) -> None:
        with open(str(self.target) + "/etc/systemd/network/10-" + str(nic.iface) + ".network", "a") as netconf:
            netconf.write(str(nic.as_systemd_config()))

    def copy_iso_network_config(self, enable_services: bool = False) -> bool:
        # Copy (if any) iwd password and config files
        if os.path.isdir('/var/lib/iwd/') and (psk_files := glob.glob('/var/lib/iwd/*.psk')):
            if not os.path.isdir(str(self.target) + "/var/lib/iwd"):
                os.makedirs(str(self.target) + "/var/lib/iwd")

            if enable_services:
                base_flag: bool = self._helper_flags.get('base', False)

                # If we haven't installed the base yet (function called pre-maturely)
                if base_flag:
                    self.pacman.strap('iwd')
                    self.enable_service('iwd')

                # Otherwise, we can go ahead and add the required package
                # and enable it's service:
                if not base_flag:
                    self._base_packages.append('iwd')

                    # This function will be called after minimal_installation()
                    # as a hook for post-installations. This hook is only needed if
                    # the base is not installed yet.
                    def post_install_enable_iwd_service() -> None:
                        self.enable_service('iwd')

                    self.post_base_install.append(post_install_enable_iwd_service)

            for psk in psk_files:
                shutil.copy2(psk, str(self.target) + "/var/lib/iwd/" + str(os.path.basename(psk)))

        # Copy (if any) systemd-networkd config files
        if network_configurations := glob.glob('/etc/systemd/network/*'):
            if not os.path.isdir(str(self.target) + "/etc/systemd/network/"):
                os.makedirs(str(self.target) + "/etc/systemd/network/")

            for netconf_file in network_configurations:
                shutil.copy2(netconf_file, str(self.target) + "/etc/systemd/network/" + str(os.path.basename(netconf_file)))

            if enable_services:
                base_flag: bool = self._helper_flags.get('base', False)

                # If we haven't installed the base yet (function called pre-maturely)
                if base_flag:
                    self.enable_service([
                        'systemd-networkd',
                        'systemd-resolved'
                    ])

                # Otherwise, we can go ahead and enable the services
                if not base_flag:
                    def post_install_enable_networkd_resolved() -> None:
                        self.enable_service([
                            'systemd-networkd',
                            'systemd-resolved'
                        ])

                    self.post_base_install.append(post_install_enable_networkd_resolved)

        return True

    def mkinitcpio(self, flags: list[str]) -> bool:
        with open(str(self.target) + '/etc/mkinitcpio.conf', 'r+') as mkinit:
            content: str = mkinit.read()

            content = re.sub(pattern="\nMODULES=(.*)",  repl="\nMODULES=(" + ' '.join(self._modules) + ")",   string=content)
            content = re.sub(pattern="\nBINARIES=(.*)", repl="\nBINARIES=(" + ' '.join(self._binaries) + ")", string=content)
            content = re.sub(pattern="\nFILES=(.*)",    repl="\nFILES=(" + ' '.join(self._files) + ")",       string=content)

            if not self._disk_encryption.hsm_device:
                # For now, if we don't use HSM, we revert to the old
                # way of setting up encryption hooks for mkinitcpio.
                # This is purely for stability reasons, we're going away from this.
                # * systemd -> udev
                # * sd-vconsole -> keymap
                self._hooks = [hook.replace('systemd', 'udev').replace('sd-vconsole', 'keymap consolefont') for hook in self._hooks]

            content = re.sub(pattern="\nHOOKS=(.*)", repl="\nHOOKS=(" + ' '.join(self._hooks) + ")", string=content)

            mkinit.seek(0)
            mkinit.write(content)

        try:
            self.arch_chroot(('mkinitcpio ' + ' '.join(flags)), peek_output=True)
            return True
        except SysCallError as e:
            if e.worker_log:
                log(e.worker_log.decode())

            return False

    @staticmethod
    def _get_microcode() -> Path | None:
        vendor: CpuVendor | None = SysInfo.cpu_vendor()
        return vendor.get_ucode() if not SysInfo.is_vm() and vendor else None

    def _prepare_fs_type(self, fs_type: FilesystemType, mountpoint: Path | None) -> None:
        if (pkg := fs_type.installation_pkg) is not None:
            self._base_packages.append(pkg)

        if fs_type.fs_type_mount == 'btrfs':
            self._disable_fstrim = True

        if (fs_type.fs_type_mount == 'ntfs3') and (mountpoint == self.target) and 'fsck' in self._hooks:
            self._hooks.remove('fsck')

    def _prepare_encrypt(self, before: str = 'filesystems') -> None:
        hook: str = 'sd-encrypt' if self._disk_encryption.hsm_device else 'encrypt'

        if hook not in self._hooks:
            self._hooks.insert(self._hooks.index(before), hook)

        if hook == 'sd-encrypt':
            self.pacman.strap('libfido2')

    def minimal_installation(self, optional_repositories: list[Repository] | None = None, mkinitcpio: bool = True, hostname: str | None = None, locale_config: LocaleConfiguration | None = LocaleConfiguration.default()) -> None:
        if not optional_repositories:
            optional_repositories = []

        if self._disk_config.lvm_config:
            lvm: str = 'lvm2'

            self.add_additional_packages(lvm)
            self._hooks.insert(self._hooks.index('filesystems') - 1, lvm)

            for vg in self._disk_config.lvm_config.vol_groups:
                for vol in vg.volumes:
                    if vol.fs_type is not None:
                        self._prepare_fs_type(vol.fs_type, vol.mountpoint)

            types: tuple[Literal[EncryptionType.LvmOnLuks], Literal[EncryptionType.LuksOnLvm]] = (EncryptionType.LvmOnLuks, EncryptionType.LuksOnLvm)

            if self._disk_encryption.encryption_type in types:
                self._prepare_encrypt(lvm)

        if not self._disk_config.lvm_config:
            for mod in self._disk_config.device_modifications:
                for part in mod.partitions:
                    if not part.fs_type:
                        continue

                    self._prepare_fs_type(part.fs_type, part.mountpoint)

                    if part in self._disk_encryption.partitions:
                        self._prepare_encrypt()

        if ucode := self._get_microcode():
            (self.target / 'boot' / ucode).unlink(missing_ok=True)
            self._base_packages.append(ucode.stem)

        if not self._get_microcode():
            debug('Nerve will not install any ucode.')

        debug('Optional repositories: ' + str(optional_repositories))

        # Determine whether to enable multilib/testing repositories before running pacstrap if the testing flag is set.
        # This action takes place on the host system as pacstrap copies over package repository lists.
        pacman_conf: PacmanConfig = PacmanConfig(self.target)
        pacman_conf.enable(optional_repositories)

        pacman_conf.apply()
        self.pacman.strap(self._base_packages)

        self._helper_flags['base-strapped'] = True
        pacman_conf.persist()

        # Periodic TRIM may improve the performance and longevity of SSDs whilst
        # having no adverse effect on other devices. Most distributions enable
        # periodic TRIM by default.
        if not self._disable_fstrim:
            self.enable_periodic_trim()

        # TODO: Support locale and timezone
        if hostname:
            self.set_hostname(hostname)

        if locale_config:
            self.set_locale(locale_config)
            self.set_keyboard_language(locale_config.kb_layout.strip())

        # TODO: Use python functions for this
        self.arch_chroot('chmod 700 /root')

        if mkinitcpio and not self.mkinitcpio(['-P']):
            error('Error generating initramfs (continuing anyway)')

        self._helper_flags['base'] = True

        # Run registered post-install hooks
        for function in self.post_base_install:
            info("Running post-installation hook: " + str(function))
            function(self)

    def setup_btrfs_snapshot(self, snapshot_type: SnapshotType, bootloader: Bootloader | None = None) -> None:
        match snapshot_type:
            case SnapshotType.Snapper:
                debug('Setting up Btrfs snapper')
                self.pacman.strap('snapper')

                snapper: dict[str, str] = {
                    'root': '/',
                    'home': '/home'
                }

                for (config_name, mountpoint) in snapper.items():
                    try:
                        self.arch_chroot("snapper --no-dbus -c " + config_name + ' create-config ' + mountpoint, peek_output=True)
                    except SysCallError as err:
                        raise DiskError('Could not setup Btrfs snapper: ' + str(err))

                self.enable_service(['snapper-timeline.timer', 'snapper-cleanup.timer'])

            case SnapshotType.Timeshift:
                debug('Setting up Btrfs timeshift')

                self.pacman.strap(['cronie', 'timeshift'])
                self.enable_service('cronie.service')

                if bootloader and (bootloader == Bootloader.Grub):
                    self.pacman.strap(['grub-btrfs', 'inotify-tools'])
                    self._configure_grub_btrfsd()
                    self.enable_service('grub-btrfsd.service')

    def setup_swap(self) -> None:
        info("Setting up swap on zram")
        self.pacman.strap('zram-generator')

        # We could use the default example below but maybe not the best idea
        with open(file=str(self.target) + "/etc/systemd/zram-generator.conf", mode="w") as zram_conf:
            zram_conf.write("[zram0]\n")

        self.enable_service('systemd-zram-setup@zram0.service')
        self._zram_enabled = True

    def _get_efi_partition(self) -> PartitionModification | None:
        return next((partition for layout in self._disk_config.device_modifications if (partition := layout.get_efi_partition())), None)

    def _get_boot_partition(self) -> PartitionModification | None:
        return next((boot for layout in self._disk_config.device_modifications if (boot := layout.get_boot_partition())), None)

    def _get_root(self) -> PartitionModification | LvmVolume | None:
        return self._disk_config.lvm_config.get_root_volume() if self._disk_config.lvm_config else next((root for mod in self._disk_config.device_modifications if (root := mod.get_root_partition())), None)

    def _configure_grub_btrfsd(self) -> None:
        # See https://github.com/Antynea/grub-btrfs?tab=readme-ov-file#-using-timeshift-with-systemd
        debug('Configuring grub-btrfsd service')

        # https://www.freedesktop.org/software/systemd/man/latest/systemd.unit.html#id-1.14.3
        systemd_dir: Path = self.target / 'etc/systemd/system/grub-btrfsd.service.d'
        systemd_dir.mkdir(parents=True, exist_ok=True)

        override_conf: Path = systemd_dir / 'override.conf'

        config_content: str = textwrap.dedent("""
            [Service]
            ExecStart=
            ExecStart=/usr/bin/grub-btrfsd --syslog --timeshift-auto
        """)

        override_conf.write_text(config_content)
        override_conf.chmod(0o644)

    @staticmethod
    def _get_luks_uuid_from_mapper_dev(mapper_dev_path: Path) -> str:
        lsblk_info: LsblkInfo = get_lsblk_info(mapper_dev_path, reverse=True, full_dev_path=True)

        if not lsblk_info.children or not lsblk_info.children[0].uuid:
            raise ValueError('Unable to determine UUID of luks superblock')

        return lsblk_info.children[0].uuid

    def _get_kernel_params_partition(self, root_partition: PartitionModification, id_root: bool = True, partuuid: bool = True) -> list[str]:
        kernel_parameters: list[str] = []

        if root_partition in self._disk_encryption.partitions:
            # TODO: We need to detect if the encrypted device is a whole disk encryption, or simply a partition encryption. Right now we assume it's a partition (and we always have)
            if self._disk_encryption.hsm_device:
                debug('Root partition is an encrypted device, identifying by UUID: ' + str(root_partition.uuid))

                # Note: UUID must be used, not PARTUUID for sd-encrypt to work
                kernel_parameters.append('rd.luks.name=' + str(root_partition.uuid) + '=root')

                # Note: tpm2-device and fido2-device don't play along very well:
                kernel_parameters.append('rd.luks.options=fido2-device=auto,password-echo=no')
            elif partuuid:
                debug('Root partition is an encrypted device, identifying by PARTUUID: ' + str(root_partition.partuuid))
                kernel_parameters.append('cryptdevice=PARTUUID=' + str(root_partition.partuuid) + ':root')
            else:
                debug('Root partition is an encrypted device, identifying by UUID: ' + str(root_partition.uuid))
                kernel_parameters.append('cryptdevice=UUID=' + str(root_partition.uuid) + ':root')

            if id_root:
                kernel_parameters.append('root=/dev/mapper/root')

        elif id_root:
            if partuuid:
                debug('Identifying root partition by PARTUUID: ' + str(root_partition.partuuid))
                kernel_parameters.append('root=PARTUUID=' + str(root_partition.partuuid))

            if not partuuid:
                debug('Identifying root partition by UUID: ' + str(root_partition.uuid))
                kernel_parameters.append('root=UUID=' + str(root_partition.uuid))

        return kernel_parameters

    def _get_kernel_params_lvm(self, lvm: LvmVolume) -> list[str]:
        kernel_parameters: list[str] = []

        match self._disk_encryption.encryption_type:
            case EncryptionType.LvmOnLuks:
                if not lvm.vg_name:
                    raise ValueError('Unable to determine VG name for ' + lvm.name)

                pv_seg_info: LvmPVInfo | None = device_handler.lvm_pvseg_info(lvm.vg_name, lvm.name)

                if not pv_seg_info:
                    raise ValueError('Unable to determine PV segment info for ' + str(lvm.vg_name) + '/' + lvm.name)

                uuid: str = self._get_luks_uuid_from_mapper_dev(pv_seg_info.pv_name)

                if self._disk_encryption.hsm_device:
                    debug('LvmOnLuks, encrypted root partition, HSM, identifying by UUID: ' + uuid)
                    kernel_parameters.append('rd.luks.name=' + uuid + '=cryptlvm root=' + str(lvm.safe_dev_path))

                if not self._disk_encryption.hsm_device:
                    debug('LvmOnLuks, encrypted root partition, identifying by UUID: ' + uuid)
                    kernel_parameters.append('cryptdevice=UUID=' + uuid + ':cryptlvm root=' + str(lvm.safe_dev_path))

            case EncryptionType.LuksOnLvm:
                uuid: str = self._get_luks_uuid_from_mapper_dev(lvm.mapper_path)

                if self._disk_encryption.hsm_device:
                    debug('LuksOnLvm, encrypted root partition, HSM, identifying by UUID: ' + uuid)
                    kernel_parameters.append('rd.luks.name=' + uuid + '=root root=/dev/mapper/root')

                if not self._disk_encryption.hsm_device:
                    debug('LuksOnLvm, encrypted root partition, identifying by UUID: ' + uuid)
                    kernel_parameters.append('cryptdevice=UUID=' + uuid + ':root root=/dev/mapper/root')

            case EncryptionType.NoEncryption:
                debug('Identifying root lvm by mapper device: ' + str(lvm.dev_path))
                kernel_parameters.append('root=' + str(lvm.safe_dev_path))

        return kernel_parameters

    def _get_kernel_params(self, root: PartitionModification | LvmVolume, id_root: bool = True, partuuid: bool = True) -> list[str]:
        kernel_parameters: list[str] = self._get_kernel_params_lvm(root) if isinstance(root, LvmVolume) else self._get_kernel_params_partition(root, id_root, partuuid)

        # Zswap should be disabled when using zram.
        if self._zram_enabled:
            kernel_parameters.append('zswap.enabled=0')

        if id_root:
            for sub_vol in root.btrfs_subvols:
                if sub_vol.is_root():
                    kernel_parameters.append('rootflags=subvol=' + str(sub_vol.name))
                    break

            kernel_parameters.append('rw')

        kernel_parameters.append('rootfstype=' + str(root.safe_fs_type.fs_type_mount))
        kernel_parameters.extend(self._kernel_params)

        debug('kernel parameters: ' + " ".join(kernel_parameters))
        return kernel_parameters

    def _create_bls_entries(self, boot_partition: PartitionModification, root: PartitionModification | LvmVolume, entry_name: str) -> None:
        # Loader entries are stored in $BOOT/loader:
        # https://uapi-group.org/specifications/specs/boot_loader_specification/#mount-points

        entries_dir: Path = self.target / boot_partition.relative_mountpoint / 'loader/entries'
        # Ensure that the $BOOT/loader/entries/ directory exists before trying to create files in it
        entries_dir.mkdir(parents=True, exist_ok=True)

        entry_template: str = textwrap.dedent("""\
    		# Created by: Nerve
    		# Created on: """ + self.init_time.split(sep='_')[0] + ' ' + self.init_time.split(sep='_')[1].replace('-', ':') + """
    		title   """ + SystemInfo().os_name + """ ({{kernel}}{{variant}})
    		linux   /vmlinuz-{{kernel}}
    		initrd  /initramfs-{{kernel}}{{variant}}.img
    		options 
    	""" + " ".join(self._get_kernel_params(root)))

        for kernel in self.kernels:
            for variant in {'', '-fallback'}:
                # Set up the loader entry
                name: str = entry_name.format(kernel=kernel, variant=variant)
                entry_conf: Path = entries_dir / name

                entry_conf.write_text(entry_template.format(kernel=kernel, variant=variant))

    def _add_systemd_bootloader(self, boot_partition: PartitionModification, root: PartitionModification | LvmVolume, efi_partition: PartitionModification | None, uki_enabled: bool = False) -> None:
        debug('Installing systemd bootloader')
        self.pacman.strap('efibootmgr')

        if not SysInfo.has_uefi():
            raise HardwareIncompatibilityError

        if not efi_partition:
            raise ValueError('Could not detect EFI system partition')
        elif not efi_partition.mountpoint:
            raise ValueError('EFI system partition is not mounted')

        # TODO: Ideally we would want to check if another config
        # points towards the same disk and/or partition.
        # And in which case we should do some clean up.
        bootctl_options: list[str] = []

        if boot_partition != efi_partition:
            bootctl_options.append('--esp-path=' + str(efi_partition.mountpoint))
            bootctl_options.append('--boot-path=' + str(boot_partition.mountpoint))

        # TODO: This is a temporary workaround to deal
        # the systemd_version check can be removed once `--variables=BOOL` is merged into systemd.
        systemd_pkg: LocalPackage | None = installed_package('systemd')
        systemd_version: str = systemd_pkg.version if systemd_pkg else '257'

        try:
            # Force EFI variables since bootctl detects arch-chroot
            # as a container environemnt since v257 and skips them silently.
            # https://github.com/systemd/systemd/issues/36174
            self.arch_chroot(("bootctl --variables=yes " + ' '.join(bootctl_options) + " install") if systemd_version >= '258' else ("bootctl " + " ".join(bootctl_options) + " install"))
        except SysCallError:
            # Fallback, try creating the bootloader without touching the EFI variables
            self.arch_chroot(("bootctl --variables=no " + ' '.join(bootctl_options) + " install") if systemd_version >= '258' else ("bootctl --no-variables " + " ".join(bootctl_options) + " install"))

        # Loader configuration is stored in ESP/loader:
        loader_conf = self.target / efi_partition.relative_mountpoint / 'loader/loader.conf'
        # Ensure that the ESP/loader/ directory exists before trying to create a file in it
        loader_conf.parent.mkdir(parents=True, exist_ok=True)

        default_kernel: str = self.kernels[0]
        default_entry:  str = ''

        if uki_enabled:
            default_entry: str = SystemInfo().os_id + '-' + default_kernel + '.efi'

        if not uki_enabled:
            entry_name:    str = self.init_time + '_{kernel}{variant}.conf'
            default_entry: str = entry_name.format(kernel=default_kernel, variant='')

            self._create_bls_entries(boot_partition, root, entry_name)

        default: str = 'default ' + default_entry

        try:
            loader_data: list[str] = loader_conf.read_text().splitlines()
        except FileNotFoundError:
            loader_data: list[str] = [
                default,
                'timeout 15'
            ]

        for (index, line) in enumerate(loader_data):
            if line.startswith('default'):
                loader_data[index] = default
            elif line.startswith('#timeout'):
                # We add in the default timeout to support dual-boot
                loader_data[index] = line.removeprefix('#')

        loader_conf.write_text('\n'.join(loader_data) + '\n')
        self._helper_flags['bootloader'] = 'systemd'

    def _add_grub_bootloader(self, boot_partition: PartitionModification, root: PartitionModification | LvmVolume, efi_partition: PartitionModification | None) -> None:
        debug('Installing grub bootloader')
        self.pacman.strap('grub')

        grub_default: Path = self.target / 'etc/default/grub'
        config: str = grub_default.read_text()

        kernel_parameters: str = ' '.join(self._get_kernel_params(root, id_root=False, partuuid=False))
        config:            str = re.sub(pattern=r'(GRUB_CMDLINE_LINUX=")("\n)', repl=r'\1' + kernel_parameters + '\2', string=config, count=1)

        grub_default.write_text(config)
        info("GRUB boot partition: " + str(boot_partition.dev_path))

        boot_dir: Path = Path('/boot')

        command: list[str] = [
            'arch-chroot',
            '-S',
            str(self.target),
            'grub-install',
            '--debug'
        ]

        if SysInfo.has_uefi():
            if not efi_partition:
                raise ValueError('Could not detect efi partition')

            info("GRUB EFI partition: " + str(efi_partition.dev_path))

            self.pacman.strap('efibootmgr')  # TODO: Do we need? Yes, but remove from minimal_installation() instead?
            boot_dir_arg: list[str] = []

            if boot_partition.mountpoint and (boot_partition.mountpoint != boot_dir):
                boot_dir_arg.append('--boot-directory=' + str(boot_partition.mountpoint))
                boot_dir: Path = boot_partition.mountpoint

            add_options: list[str] = [
                '--target=' + platform.machine() + '-efi',
                '--efi-directory=' + str(efi_partition.mountpoint),
                *boot_dir_arg,
                '--bootloader-id=GRUB',
                '--removable'
            ]

            command.extend(add_options)

            try:
                SysCommand(command, peek_output=True)
            except SysCallError:
                try:
                    SysCommand(command, peek_output=True)
                except SysCallError as err:
                    raise DiskError("Could not install GRUB to " + str(self.target) + str(efi_partition.mountpoint) + ": " + str(err))

        if not SysInfo.has_uefi():
            info("GRUB boot partition: " + str(boot_partition.dev_path))
            parent_dev_path: Path = device_handler.get_parent_device_path(boot_partition.safe_dev_path)

            add_options: list[str] = [
                '--target=i386-pc',
                '--recheck',
                str(parent_dev_path)
            ]

            try:
                SysCommand(command + add_options, peek_output=True)
            except SysCallError as err:
                raise DiskError("Failed to install GRUB boot on " + str(boot_partition.dev_path) + ": " + str(err))

        try:
            self.arch_chroot('grub-mkconfig -o ' + str(boot_dir) + '/grub/grub.cfg')
        except SysCallError as err:
            raise DiskError("Could not configure GRUB: " + str(err))

        self._helper_flags['bootloader'] = "grub"

    def _add_limine_bootloader(self, boot_partition: PartitionModification, efi_partition: PartitionModification | None, root: PartitionModification | LvmVolume, uki_enabled: bool = False) -> None:
        debug('Installing Limine bootloader')

        self.pacman.strap('limine')
        info("Limine boot partition: " + str(boot_partition.dev_path))

        limine_path: Path = self.target / 'usr' / 'share' / 'limine'
        hook_command: str | None = None
        config_path: Path | None = None

        if SysInfo.has_uefi():
            self.pacman.strap('efibootmgr')

            if not efi_partition:
                raise ValueError('Could not detect efi partition')
            elif not efi_partition.mountpoint:
                raise ValueError('EFI partition is not mounted')

            info("Limine EFI partition: " + str(efi_partition.dev_path))

            parent_dev_path: Path = device_handler.get_parent_device_path(efi_partition.safe_dev_path)
            is_target_usb: bool = SysCommand('udevadm info --no-pager --query=property --property=ID_BUS --value --name=' + str(parent_dev_path)).decode() == 'usb'

            try:
                efi_dir_path:        Path = self.target / efi_partition.mountpoint.relative_to('/') / 'EFI'
                efi_dir_path_target: Path = efi_partition.mountpoint / 'EFI'

                efi_dir_path:        Path = efi_dir_path / 'BOOT' if is_target_usb else efi_dir_path / 'limine'
                efi_dir_path_target: Path = efi_dir_path_target / 'BOOT' if is_target_usb else efi_dir_path_target / 'limine'

                efi_dir_path.mkdir(parents=True, exist_ok=True)

                for file in {'BOOTIA32.EFI', 'BOOTX64.EFI'}:
                    shutil.copy(limine_path / file, efi_dir_path)

            except Exception as err:
                raise DiskError('Failed to install Limine in ' + str(self.target) + str(efi_partition.mountpoint) + ': ' + str(err))

            config_path: Path = efi_dir_path / 'limine.conf'
            hook_command: str = '/usr/bin/cp /usr/share/limine/BOOTIA32.EFI ' + str(efi_dir_path_target) + '/EFI/limine/ && /usr/bin/cp /usr/share/limine/BOOTX64.EFI ' + str(efi_dir_path_target) + '/EFI/limine/'

            if not is_target_usb:
                # Create an EFI boot menu entry for Limine.
                try:
                    with open('/sys/firmware/efi/fw_platform_size') as fw_platform_size:
                        efi_bitness: str = fw_platform_size.read().strip()

                except Exception as err:
                    raise OSError('Could not open or read /sys/firmware/efi/fw_platform_size to determine EFI bitness: ' + str(err))

                loader_path: str | None = {
                    '64': '/EFI/limine/BOOTX64.EFI',
                    '32': '/EFI/limine/BOOTIA32.EFI'
                }.get(efi_bitness)

                if not loader_path:
                    raise ValueError('EFI bitness is neither 32 nor 64 bits. Found "' + efi_bitness + '".')

                try:
                    SysCommand('efibootmgr --create --disk ' + str(parent_dev_path) + ' --part ' + str(efi_partition.partn) + ' --label "' + SystemInfo().os_name + ' Limine Bootloader" --loader ' + str(loader_path) + ' --unicode --verbose')
                except Exception as err:
                    raise ValueError('SysCommand for efibootmgr failed: ' + str(err))

        if not SysInfo.has_uefi():
            boot_limine_path: Path = self.target / 'boot' / 'limine'
            boot_limine_path.mkdir(parents=True, exist_ok=True)

            config_path:     Path = boot_limine_path / 'limine.conf'
            parent_dev_path: Path = device_handler.get_parent_device_path(boot_partition.safe_dev_path)

            if unique_path := device_handler.get_unique_path_for_device(parent_dev_path):
                parent_dev_path = unique_path

            try:
                # The `limine-bios.sys` file contains stage 3 code.
                shutil.copy(limine_path / 'limine-bios.sys', boot_limine_path)

                # `limine bios-install` deploys the stage 1 and 2 to the disk.
                self.arch_chroot('limine bios-install ' + str(parent_dev_path), peek_output=True)
            except Exception as err:
                raise DiskError('Failed to install Limine on ' + str(parent_dev_path) + ': ' + str(err))

            hook_command: str = '/usr/bin/limine bios-install ' + str(parent_dev_path) + ' && /usr/bin/cp /usr/share/limine/limine-bios.sys /boot/limine/'

        hook_contents: str = textwrap.dedent('''\
            [Trigger]
            Operation = Install
            Operation = Upgrade
            Type = Package
            Target = limine

            [Action]
            Description = Deploying Limine after upgrade...
            When = PostTransaction
            Exec = /bin/sh -c "''' + hook_command + '''"
        ''')

        hooks_dir: Path = self.target / 'etc' / 'pacman.d' / 'hooks'
        hooks_dir.mkdir(parents=True, exist_ok=True)

        hook_path: Path = hooks_dir / '99-limine.hook'
        hook_path.write_text(hook_contents)

        kernel_params:   str = ' '.join(self._get_kernel_params(root))
        config_contents: str = 'timeout: 5\n'
        path_root:       str = 'boot()'

        if efi_partition and (boot_partition != efi_partition):
            path_root = 'uuid(' + str(boot_partition.partuuid) + ')'

        for kernel in self.kernels:
            for variant in {'', '-fallback'}:
                entry = [
                    'protocol: efi',
                    'path: ' + path_root + ':/EFI/Linux/' + SystemInfo().os_id + '-' + kernel + '.efi',
                    'cmdline: ' + kernel_params
                ] if uki_enabled else [
                    'protocol: linux',
                    'path: boot():/vmlinuz-' + kernel,
                    'cmdline: ' + kernel_params,
                    'module_path: ' + path_root + ':/initramfs-' + kernel + variant + '.img'
                ]

                config_contents += '\n/' + SystemInfo().os_name + ' (' + kernel + variant + ')\n'
                config_contents += '\n'.join([' ' * 4 + it for it in entry]) + '\n'

        config_path.write_text(config_contents)
        self._helper_flags['bootloader'] = "limine"

    def _add_efistub_bootloader(self, boot_partition: PartitionModification, root: PartitionModification | LvmVolume, uki_enabled: bool = False) -> None:
        debug('Installing efistub bootloader')
        self.pacman.strap('efibootmgr')

        if not SysInfo.has_uefi():
            raise HardwareIncompatibilityError

        # TODO: Ideally we would want to check if another config
        # points towards the same disk and/or partition.
        # And in which case we should do some clean up.
        loader: str = '/vmlinuz-{kernel}' if not uki_enabled else '/EFI/Linux/{id}-{kernel}.efi'
        cmdline: list[str] = [' '.join(('initrd=/initramfs-{kernel}.img', *self._get_kernel_params(root)))] if not uki_enabled else []

        parent_dev_path: Path = device_handler.get_parent_device_path(boot_partition.safe_dev_path)

        cmd_template: tuple[str, ...] = (
            'efibootmgr',
            '--create',
            '--disk', str(parent_dev_path),
            '--part', str(boot_partition.partn),
            '--label', '{system} ({kernel})',
            '--loader', loader,
            '--unicode', *cmdline,
            '--verbose'
        )

        for kernel in self.kernels:
            # Set up the firmware entry
            cmd: list[str] = [arg.format(id=SystemInfo().os_id, system=SystemInfo().os_name, kernel=kernel) for arg in cmd_template]
            SysCommand(cmd)

        self._helper_flags['bootloader'] = "efistub"

    def _config_uki(self, root: PartitionModification | LvmVolume, efi_partition: PartitionModification | None) -> None:
        if not efi_partition or not efi_partition.mountpoint:
            raise ValueError('Could not detect ESP at mountpoint ' + str(self.target))

        # Set up the kernel command line
        with open(self.target / 'etc/kernel/cmdline', 'w') as cmdline:
            kernel_parameters: list[str] = self._get_kernel_params(root)
            cmdline.write(' '.join(kernel_parameters) + '\n')

        diff_mountpoint: str | None = None

        if efi_partition.mountpoint != Path('/efi'):
            diff_mountpoint = str(efi_partition.mountpoint)

        image_re: re.Pattern[str] = re.compile('(.+_image="/([^"]+).+\n)')
        uki_re:   re.Pattern[str] = re.compile('#((.+_uki=")/[^/]+(.+\n))')

        # Modify .preset files
        for kernel in self.kernels:
            preset: Path = self.target / 'etc/mkinitcpio.d' / (kernel + '.preset')
            config: list[str] = preset.read_text().splitlines(True)

            for (index, line) in enumerate(config):
                # Avoid storing a redundant image file
                if m := image_re.match(line):
                    image: Path = self.target / m.group(2)
                    image.unlink(missing_ok=True)

                    config[index] = '#' + m.group(1)
                elif m := uki_re.match(line):
                    config[index] = (m.group(2) + diff_mountpoint + m.group(3)) if diff_mountpoint else m.group(1)
                elif line.startswith('#default_options='):
                    config[index] = line.removeprefix('#')

            preset.write_text(''.join(config))

        # Directory for the UKIs
        uki_dir: Path = self.target / efi_partition.relative_mountpoint / 'EFI/Linux'
        uki_dir.mkdir(parents=True, exist_ok=True)

        # Build the UKIs
        if not self.mkinitcpio(['-P']):
            error('Error generating initramfs (continuing anyway)')

    def add_bootloader(self, bootloader: Bootloader, uki_enabled: bool = False) -> None:
        """
        Adds a bootloader to the installation instance.
        Nerve supports one of three types:
        * systemd-bootctl
        * grub
        * limine (beta)
        * efistub (beta)

        :param bootloader: Type of bootloader to be added to
        :param uki_enabled: Whether UKI support is enabled
        """
        efi_partition:  PartitionModification | None = self._get_efi_partition()
        boot_partition: PartitionModification | None = self._get_boot_partition()

        root: PartitionModification | LvmVolume | None = self._get_root()

        if not boot_partition:
            raise ValueError('Could not detect boot at mountpoint ' + str(self.target))

        if not root:
            raise ValueError('Could not detect root at mountpoint ' + str(self.target))

        info('Adding bootloader ' + str(bootloader.value) + ' to ' + str(boot_partition.dev_path))

        if uki_enabled:
            self._config_uki(root, efi_partition)

        match bootloader:
            case Bootloader.Systemd:
                self._add_systemd_bootloader(boot_partition, root, efi_partition, uki_enabled)

            case Bootloader.Grub:
                self._add_grub_bootloader(boot_partition, root, efi_partition)

            case Bootloader.Efistub:
                self._add_efistub_bootloader(boot_partition, root, uki_enabled)

            case Bootloader.Limine:
                self._add_limine_bootloader(boot_partition, efi_partition, root, uki_enabled)

    def add_additional_packages(self, packages: str | list[str]) -> None:
        return self.pacman.strap(packages)

    def enable_sudo(self, user: User, group: bool = False) -> None:
        info('Enabling sudo permissions for ' + user.username)
        sudoers_dir: Path = self.target / "etc/sudoers.d"

        # Creates a directory if not exists
        if not sudoers_dir.exists():
            sudoers_dir.mkdir(parents=True)

            # Guarantees sudoer confs directory recommended perms
            sudoers_dir.chmod(mode=0o440)

            # Appends a reference to the sudoers file, because if we are here, sudoers.d did not exist yet
            with open(file=self.target / 'etc/sudoers', mode='a') as sudoers:
                sudoers.write('@includedir /etc/sudoers.d\n')

        # We count how many files are there already, so we know which number to prefix the file with
        num_of_rules_already: int = len(os.listdir(sudoers_dir))
        file_num_str: str = "{:02d}".format(num_of_rules_already)  # We want 00_user1, 01_user2, etc

        # Guarantees that username str does not contain invalid characters for a linux file name:
        # \ / : * ? " < > |
        safe_username_file_name: str = re.sub(pattern=r'([\\/:*?"<>|])', repl='', string=user.username)
        rule_file: Path = sudoers_dir / (file_num_str + '_' + safe_username_file_name)

        with rule_file.open(mode='a') as sudoers:
            sudoers.write(("%" if group else "") + user.username + ' ALL=(ALL) ALL\n')

        # Guarantees sudoer conf file recommended perms
        rule_file.chmod(0o440)

    def create_users(self, users: User | list[User]) -> None:
        if not isinstance(users, list):
            users = [users]

        for user in users:
            self._create_user(user)

    def _create_user(self, user: User) -> None:
        info('Creating user ' + user.username)
        cmd: str = 'useradd -m'

        if user.sudo:
            cmd += ' -G wheel'

        cmd += ' ' + user.username

        try:
            self.arch_chroot(cmd)
        except SysCallError as err:
            raise SystemError("Could not create user inside installation: " + str(err))

        self.set_user_password(user)

        for group in user.groups:
            self.arch_chroot('gpasswd -a ' + user.username + ' ' + group)

        if user.sudo:
            self.enable_sudo(user)

    def set_user_password(self, user: User) -> bool:
        info('Setting password for ' + user.username)
        enc_password: str | None = user.password.enc_password

        if not enc_password:
            debug('User password is empty')
            return False

        input_data: bytes = (user.username + ':' + str(enc_password)).encode()
        cmd: list[str] = ['arch-chroot', '-S', str(self.target), 'chpasswd', '--encrypted']

        try:
            run(cmd, input_data=input_data)
            return True
        except CalledProcessError as err:
            debug('Error setting user password: ' + str(err))
            return False

    def set_shell(self, shell: str, users: list['User'] | None = None) -> None:
        if not users:
            return

        for user in users:
            info('Setting shell: ' + shell + ' for user: ' + user.username)

            try:
                self.arch_chroot("usermod -s " + shell + " " + user.username)
            except SysCallError:
                warn("Failed to set shell for " + user.username)

    def chown(self, owner: str, path: str, options: list[str] | None = None) -> bool:
        if not options:
            options = []

        cleaned_path: str = path.replace('\'', '\\\'')

        try:
            self.arch_chroot("sh -c 'chown " + ' '.join(options) + " " + owner + " " + cleaned_path + "'")
            return True
        except SysCallError:
            return False

    def set_keyboard_language(self, language: str) -> bool:
        if not language:
            info("Keyboard language was not changed from default (no language specified)")
            return True

        info("Setting keyboard language to " + language)

        if not verify_keyboard_layout(language):
            error("Invalid keyboard language specified: " + language)
            return False

        from nerve.lib.boot import Boot

        with Boot(self) as session:
            # Setting an empty keymap first allows setting layout for both console and X11.
            os.system('/usr/bin/systemd-run --machine=nerve --pty localectl set-keymap ""')

            try:
                session.SysCommand(["localectl", "set-keymap", language])
            except SysCallError as err:
                raise ServiceException("Unable to set locale '" + language + "' for console: " + str(err))

            info("Keyboard language for this installation is now set to: " + language)

        return True

    @staticmethod
    def _service_started(service_name: str) -> str | None:
        if os.path.splitext(service_name)[1] not in {'.service', '.target', '.timer'}:
            service_name += '.service'  # Just to be safe

        last_execution_time: str = SysCommand("systemctl show --property=ActiveEnterTimestamp --no-pager " + service_name, environment_vars={
            'SYSTEMD_COLORS': '0'
        }).decode().removeprefix('ActiveEnterTimestamp=')

        return None if not last_execution_time else last_execution_time

    @staticmethod
    def _service_state(service_name: str) -> str:
        if os.path.splitext(service_name)[1] not in {'.service', '.target', '.timer'}:
            service_name += '.service'  # Just to be safe

        return SysCommand('systemctl show --no-pager -p SubState --value ' + service_name, environment_vars={
            'SYSTEMD_COLORS': '0'
        }).decode()

def accessibility_tools_in_use() -> bool:
    return os.system('systemctl is-active --quiet espeakup.service') == 0

def run_custom_user_commands(commands: list[str], installation: Installer) -> None:
    for (index, command) in enumerate(commands):
        script_path: str = "/var/tmp/user-command." + str(index) + ".sh"
        chroot_path: str = str(installation.target) + '/' + script_path

        info('Executing custom command "' + command + '" ...')

        with open(file=chroot_path, mode="w") as user_script:
            user_script.write(command)

        installation.arch_chroot("bash " + script_path)
        os.unlink(chroot_path)
