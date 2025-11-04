# SPDX-FileCopyrightText: 2023 CELESTIFYX Team
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

import json
import os
import time

from collections.abc import Iterable
from pathlib import Path
from typing import (Literal, overload, Generator)
from parted import (Device, Disk, DiskException, FileSystem, Geometry, IOException, Partition, PartitionException, freshDisk, getAllDevices, getDevice, newDisk)

from nerve.lib.exceptions import (DiskError, SysCallError, UnknownFilesystemFormat)
from nerve.lib.general import (SysCommand, SysCommandWorker)
from nerve.lib.luks import Luks2
from nerve.lib.models.device import (DEFAULT_ITER_TIME, BDevice, BtrfsMountOption, DeviceModification, DiskEncryption, FilesystemType, LsblkInfo, LvmGroupInfo, LvmPVInfo, LvmVolume, LvmVolumeGroup, LvmVolumeInfo, ModificationStatus, PartitionFlag, PartitionGUID, PartitionModification, PartitionTable, SectorSize, Size, SubvolumeModification, Unit, BtrfsSubvolumeInfo, DeviceInfo, PartitionInfo)
from nerve.lib.models.users import Password
from nerve.lib.output import (debug, error, info)
from nerve.lib.utils.util import is_subpath
from nerve.lib.disk.utils import (find_lsblk_info, get_all_lsblk_info, get_lsblk_info, umount)

class DeviceHandler:
    _TMP_BTRFS_MOUNT: Path = Path('/mnt/nerve_btrfs')

    def __init__(self) -> None:
        self._devices: dict[Path, BDevice] = {}
        self._partition_table: PartitionTable = PartitionTable.default()

        self.load_devices()

    @property
    def devices(self) -> list[BDevice]:
        return list(self._devices.values())

    @property
    def partition_table(self) -> PartitionTable:
        return self._partition_table

    def load_devices(self) -> None:
        block_devices: dict[Path, BDevice] = {}
        self.udev_sync()

        all_lsblk_info: list[LsblkInfo] = get_all_lsblk_info()

        devices: list[Device] = getAllDevices()
        devices.extend(self.get_loop_devices())

        archiso_mountpoint: Path = Path('/run/archiso/airootfs')

        for device in devices:
            dev_lsblk_info: LsblkInfo | None = find_lsblk_info(device.path, all_lsblk_info)

            if not dev_lsblk_info:
                debug('Device lsblk info not found: ' + str(device.path))
                continue

            if dev_lsblk_info.type == 'rom':
                continue

            # exclude archiso loop device
            if dev_lsblk_info.mountpoint == archiso_mountpoint:
                continue

            try:
                disk: Disk = newDisk(device) if dev_lsblk_info.pttype else freshDisk(device, self.partition_table.value)
            except DiskException as err:
                debug('Unable to get disk from ' + str(device.path) + ': ' + str(err))
                continue

            device_info: DeviceInfo = DeviceInfo.from_disk(disk)
            partition_infos: list[PartitionInfo] = []

            for partition in disk.partitions:
                lsblk_info: LsblkInfo | None = find_lsblk_info(partition.path, dev_lsblk_info.children)

                if not lsblk_info:
                    debug('Partition lsblk info not found: ' + str(partition.path))
                    continue

                fs_type: FilesystemType | None = self._determine_fs_type(partition, lsblk_info)
                subvol_infos: list[BtrfsSubvolumeInfo] = []

                if fs_type == FilesystemType.Btrfs:
                    subvol_infos = self.get_btrfs_info(partition.path, lsblk_info)

                partition_infos.append(PartitionInfo.from_partition(partition, lsblk_info, fs_type, subvol_infos))

            block_device: BDevice = BDevice(disk, device_info, partition_infos)
            block_devices[block_device.device_info.path] = block_device

        self._devices = block_devices

    @staticmethod
    def get_loop_devices() -> list[Device]:
        devices: list[Device] = []

        try:
            loop_devices: SysCommand = SysCommand(['losetup', '-a'])
        except SysCallError as err:
            debug('Failed to get loop devices: ' + str(err))
            return devices

        for ld_info in str(loop_devices).splitlines():
            try:
                (loop_device_path, _) = ld_info.split(sep=':', maxsplit=1)
            except ValueError:
                continue

            try:
                loop_device: Device = getDevice(loop_device_path)
            except IOException as err:
                debug('Failed to get loop device: ' + str(err))
                continue

            devices.append(loop_device)

        return devices

    @staticmethod
    def _determine_fs_type(partition: Partition, lsblk_info: LsblkInfo | None = None) -> FilesystemType | None:
        try:
            if partition.fileSystem:
                return FilesystemType.LinuxSwap if partition.fileSystem.type == FilesystemType.LinuxSwap.parted_value else FilesystemType(partition.fileSystem.type)
            elif lsblk_info:
                return FilesystemType(lsblk_info.fstype) if lsblk_info.fstype else None

            return None
        except ValueError:
            debug('Could not determine the filesystem: ' + str(partition.fileSystem))

        return None

    def get_device(self, path: Path) -> BDevice | None:
        return self._devices.get(path, None)

    def find_partition(self, path: Path) -> PartitionInfo | None:
        for device in self._devices.values():
            part: PartitionInfo | None = next(filter(lambda x: str(x.path) == str(path), device.partition_infos), None)

            if part:
                return part

        return None

    @staticmethod
    def get_parent_device_path(dev_path: Path) -> Path:
        lsblk: LsblkInfo = get_lsblk_info(dev_path)
        return Path('/dev/' + str(lsblk.pkname))

    @staticmethod
    def get_unique_path_for_device(dev_path: Path) -> Path | None:
        paths: Generator[Path, None, None] = Path('/dev/disk/by-id').glob('*')

        linked_targets:     dict[Path, Path] = {p.resolve(): p for p in paths}
        linked_wwn_targets: dict[Path, Path] = {p: linked_targets[p] for p in linked_targets if p.name.startswith('wwn-') or p.name.startswith('nvme-eui.')}

        if dev_path in linked_wwn_targets:
            return linked_wwn_targets[dev_path]

        if dev_path in linked_targets:
            return linked_targets[dev_path]

        return None

    def get_btrfs_info(self, dev_path: Path, lsblk_info: LsblkInfo | None = None) -> list[BtrfsSubvolumeInfo]:
        if not lsblk_info:
            lsblk_info = get_lsblk_info(dev_path)

        subvol_infos: list[BtrfsSubvolumeInfo] = []
        mountpoint: Path | None = None

        if lsblk_info.mountpoint:
            # when multiple subvolumes are mounted, then the lsblk output may look like
            # "mountpoint": "/mnt/nerve/var/log"
            # "mountpoints": ["/mnt/nerve/var/log", "/mnt/nerve/home", ...]
            # so we'll determine the minimum common path and assume that's the root
            try:
                common_path: str = os.path.commonpath(lsblk_info.mountpoints)
            except ValueError:
                return subvol_infos

            mountpoint = Path(common_path)

        if not lsblk_info.mountpoint:
            self.mount(dev_path, self._TMP_BTRFS_MOUNT, create_target_mountpoint=True)
            mountpoint = self._TMP_BTRFS_MOUNT

        try:
            result: str = SysCommand('btrfs subvolume list ' + str(mountpoint)).decode()
        except SysCallError as err:
            debug('Failed to read btrfs subvolume information: ' + str(err))
            return subvol_infos

        # It is assumed that lsblk will contain the fields as
        # "mountpoints": ["/mnt/nerve/log", "/mnt/nerve/home", "/mnt/nerve", ...]
        # "fsroots": ["/@log", "/@home", "/@"...]
        # we'll thereby map the fsroot, which are the mounted filesystem roots
        # to the corresponding mountpoints
        btrfs_subvol_info: dict[Path, Path] = dict(zip(lsblk_info.fsroots, lsblk_info.mountpoints))

        # ID 256 gen 16 top levels 5 path @
        for line in result.splitlines():
            # expected output format:
            # ID 257 gen 8 top levels 5 paths @home
            name: Path = Path(line.split(' ')[-1])
            sub_vol_mountpoint: Path | None = btrfs_subvol_info.get('/' / name, None)

            subvol_infos.append(BtrfsSubvolumeInfo(name, sub_vol_mountpoint))

        if not lsblk_info.mountpoint:
            umount(dev_path)

        return subvol_infos

    @staticmethod
    def format(fs_type: FilesystemType, path: Path, additional_parted_options: list[str] | None = None) -> None:
        mkfs_type: str = fs_type.value
        command: str | None = None
        options: list[str] = []

        if not additional_parted_options:
            additional_parted_options = []

        match fs_type:
            case FilesystemType.Btrfs | FilesystemType.Xfs:
                # Force overwrite
                options.append('-f')

            case FilesystemType.F2fs:
                options.append('-f')
                options.extend(('-O', 'extra_attr'))

            case FilesystemType.Ext2 | FilesystemType.Ext3 | FilesystemType.Ext4:
                # Force create
                options.append('-F')

            case FilesystemType.Fat12 | FilesystemType.Fat16 | FilesystemType.Fat32:
                mkfs_type = 'fat'
                # Set FAT size
                options.extend(('-F', fs_type.value.removeprefix(mkfs_type)))

            case FilesystemType.Ntfs:
                # Skip zeroing and bad sector check
                options.append('--fast')

            case FilesystemType.LinuxSwap:
                command = 'mkswap'

            case _:
                raise UnknownFilesystemFormat('Filetype "' + str(fs_type.value) + '" is not supported')

        if not command:
            command = 'mkfs.' + str(mkfs_type)

        cmd: list[str] = [command, *options, *additional_parted_options, str(path)]
        debug('Formatting filesystem:', ' '.join(cmd))

        try:
            SysCommand(cmd)
        except SysCallError as err:
            msg: str = 'Could not format ' + str(path) + ' with ' + str(fs_type.value) + ': ' + err.message
            error(msg)

            raise DiskError(msg) from err

    def encrypt(self, dev_path: Path, mapper_name: str | None, enc_password: Password | None, lock_after_create: bool = True, iter_time: int = DEFAULT_ITER_TIME,) -> Luks2:
        luks_handler: Luks2 = Luks2(dev_path, mapper_name=mapper_name, password=enc_password)
        key_file: Path | None = luks_handler.encrypt(iter_time=iter_time)

        self.udev_sync()
        luks_handler.unlock(key_file=key_file)

        if not luks_handler.mapper_dev:
            raise DiskError('Failed to unlock luks device')

        if lock_after_create:
            debug('luks2 locking device: ' + str(dev_path))
            luks_handler.lock()

        return luks_handler

    def format_encrypted(self, dev_path: Path, mapper_name: str | None, fs_type: FilesystemType, enc_conf: DiskEncryption) -> None:
        if not enc_conf.encryption_password:
            raise ValueError('No encryption password provided')

        luks_handler: Luks2 = Luks2(dev_path, mapper_name=mapper_name, password=enc_conf.encryption_password)
        key_file: Path | None = luks_handler.encrypt(iter_time=enc_conf.iter_time)

        self.udev_sync()
        luks_handler.unlock(key_file=key_file)

        if not luks_handler.mapper_dev:
            raise DiskError('Failed to unlock luks device')

        info('luks2 formatting mapper dev: ' + str(luks_handler.mapper_dev))
        self.format(fs_type, luks_handler.mapper_dev)

        info('luks2 locking device: ' + str(dev_path))
        luks_handler.lock()

    @staticmethod
    def _lvm_info(cmd: str, info_type: Literal['lv', 'vg', 'pvseg']) -> LvmVolumeInfo | LvmGroupInfo | LvmPVInfo | None:
        raw_info: list[str] = SysCommand(cmd).decode().split('\n')

        # for whatever reason, the output sometimes contains
        # File descriptor X leaked on vgs invocation
        data: str = '\n'.join([raw for raw in raw_info if 'File descriptor' not in raw])
        debug('LVM info: ' + data)

        reports = json.loads(data)

        for report in reports['report']:
            if len(report[info_type]) != 1:
                raise ValueError('Report does not contain any entry')

            entry = report[info_type][0]

            match info_type:
                case 'pvseg':
                    return LvmPVInfo(pv_name=Path(entry['pv_name']), lv_name=entry['lv_name'], vg_name=entry['vg_name'])

                case 'lv':
                    return LvmVolumeInfo(lv_name=entry['lv_name'], vg_name=entry['vg_name'], lv_size=Size(int(entry['lv_size'][:-1]), Unit.B, SectorSize.default()))

                case 'vg':
                    return LvmGroupInfo(vg_uuid=entry['vg_uuid'], vg_size=Size(int(entry['vg_size'][:-1]), Unit.B, SectorSize.default()))

        return None

    @overload
    def _lvm_info_with_retry(self, cmd: str, info_type: Literal['lv']) -> LvmVolumeInfo | None:
        ...

    @overload
    def _lvm_info_with_retry(self, cmd: str, info_type: Literal['vg']) -> LvmGroupInfo | None:
        ...

    @overload
    def _lvm_info_with_retry(self, cmd: str, info_type: Literal['pvseg']) -> LvmPVInfo | None:
        ...

    def _lvm_info_with_retry(self, cmd: str, info_type: Literal['lv', 'vg', 'pvseg']) -> LvmVolumeInfo | LvmGroupInfo | LvmPVInfo | None:
        while True:
            try:
                return self._lvm_info(cmd, info_type)
            except ValueError:
                time.sleep(3)

    def lvm_vol_info(self, lv_name: str) -> LvmVolumeInfo | None:
        command: str = 'lvs --reportformat json --unit B -S lv_name=' + lv_name
        return self._lvm_info_with_retry(command, info_type='lv')

    def lvm_group_info(self, vg_name: str) -> LvmGroupInfo | None:
        command: str = 'vgs --reportformat json --unit B -o vg_name,vg_uuid,vg_size -S vg_name=' + vg_name
        return self._lvm_info_with_retry(command, info_type='vg')

    def lvm_pvseg_info(self, vg_name: str, lv_name: str) -> LvmPVInfo | None:
        command: str = 'pvs --segments -o+lv_name,vg_name -S vg_name=' + vg_name + ',lv_name=' + lv_name + ' --reportformat json '
        return self._lvm_info_with_retry(command, info_type='pvseg')

    @staticmethod
    def lvm_vol_change(vol: LvmVolume, activate: bool) -> None:
        active_flag: str = 'y' if activate else 'n'
        command:     str = 'lvchange -a ' + active_flag + ' ' + str(vol.safe_dev_path)

        debug('lvchange volume: ' + command)
        SysCommand(command)

    @staticmethod
    def lvm_export_vg(vg: LvmVolumeGroup) -> None:
        command: str = 'vgexport ' + vg.name
        debug('vgexport: ' + command)

        SysCommand(command)

    @staticmethod
    def lvm_import_vg(vg: LvmVolumeGroup) -> None:
        command: str = 'vgimport ' + vg.name
        debug('vgimport: ' + command)

        SysCommand(command)

    @staticmethod
    def lvm_vol_reduce(vol_path: Path, amount: Size) -> None:
        val:     str = amount.format_size(Unit.B, include_unit=False)
        command: str = 'lvreduce -L -' + val + 'B ' + str(vol_path)

        debug('Reducing LVM volume size: ' + command)
        SysCommand(command)

    @staticmethod
    def lvm_pv_create(pvs: Iterable[Path]) -> None:
        command: str = 'pvcreate ' + ' '.join([str(pv) for pv in pvs])
        debug('Creating LVM PVS: ' + command)

        worker: SysCommandWorker = SysCommandWorker(command)
        worker.poll()
        worker.write(data=b'y\n', line_ending=False)

    @staticmethod
    def lvm_vg_create(pvs: Iterable[Path], vg_name: str) -> None:
        pvs_str: str = ' '.join([str(pv) for pv in pvs])
        command: str = 'vgcreate --yes ' + vg_name + ' ' + pvs_str

        debug('Creating LVM group: ' + command)

        worker: SysCommandWorker = SysCommandWorker(command)
        worker.poll()
        worker.write(data=b'y\n', line_ending=False)

    @staticmethod
    def lvm_vol_create(vg_name: str, volume: LvmVolume, offset: Size | None = None) -> None:
        length: Size = volume.length - offset if offset is not None else volume.length
        length_str: str = length.format_size(Unit.B, include_unit=False)

        command: str = 'lvcreate --yes -L ' + length_str + 'B ' + vg_name + ' -n ' + volume.name
        debug('Creating volume: ' + command)

        worker: SysCommandWorker = SysCommandWorker(command)
        worker.poll()
        worker.write(data=b'y\n', line_ending=False)

        volume.vg_name  = vg_name
        volume.dev_path = Path('/dev/' + vg_name + '/' + volume.name)

    def _setup_partition(self, part_mod: PartitionModification, block_device: BDevice, disk: Disk, requires_delete: bool) -> None:
        # when we require a deleted and the partition to be (re)created
        # already exists; then we have to delete it first
        if requires_delete and part_mod.status in [ModificationStatus.Modify, ModificationStatus.Delete]:
            info('Delete existing partition: ' + str(part_mod.safe_dev_path))
            part_info: PartitionInfo | None = self.find_partition(part_mod.safe_dev_path)

            if not part_info:
                raise DiskError('No partition for dev path found: ' + str(part_mod.safe_dev_path))

            disk.deletePartition(part_info.partition)

        if part_mod.status == ModificationStatus.Delete:
            return

        start_sector:  Size = part_mod.start.convert(Unit.sectors, block_device.device_info.sector_size)
        length_sector: Size = part_mod.length.convert(Unit.sectors, block_device.device_info.sector_size)

        geometry: Geometry = Geometry(device=block_device.disk.device, start=start_sector.value, length=length_sector.value)
        fs_value: str = part_mod.safe_fs_type.parted_value

        filesystem: FileSystem = FileSystem(type=fs_value, geometry=geometry)
        partition: Partition = Partition(disk=disk, type=part_mod.type.get_partition_code(), fs=filesystem, geometry=geometry)

        for flag in part_mod.flags:
            partition.setFlag(flag.flag_id)

        debug('\tType: ' + str(part_mod.type.value))
        debug('\tFilesystem: ' + fs_value)
        debug('\tGeometry: ' + str(start_sector.value) + ' start sector, ' + str(length_sector.value) + ' length')

        try:
            disk.addPartition(partition=partition, constraint=disk.device.optimalAlignedConstraint)
        except PartitionException as ex:
            raise DiskError('Unable to add partition, most likely due to overlapping sectors: ' + str(ex)) from ex

        if disk.type == PartitionTable.GPT.value:
            if part_mod.is_root():
                partition.type_uuid = PartitionGUID.LINUX_ROOT_X86_64.bytes
            elif PartitionFlag.LINUX_HOME not in part_mod.flags and part_mod.is_home():
                partition.setFlag(PartitionFlag.LINUX_HOME.flag_id)

        # the partition has a path now that it has been added
        part_mod.dev_path = Path(partition.path)

    @staticmethod
    def fetch_part_info(path: Path) -> LsblkInfo:
        lsblk_info: LsblkInfo = get_lsblk_info(path)

        if not lsblk_info.partn:
            debug('Unable to determine new partition number: ' + str(path) + '\n' + str(lsblk_info))
            raise DiskError('Unable to determine new partition number: ' + str(path))

        if not lsblk_info.partuuid:
            debug('Unable to determine new partition uuid: ' + str(path) + '\n' + str(lsblk_info))
            raise DiskError('Unable to determine new partition uuid: ' + str(path))

        if not lsblk_info.uuid:
            debug('Unable to determine new uuid: ' + str(path) + '\n' + str(lsblk_info))
            raise DiskError('Unable to determine new uuid: ' + str(path))

        debug('partition information found: ' + str(lsblk_info.model_dump_json()))
        return lsblk_info

    def create_lvm_btrfs_subvolumes(self, path: Path, btrfs_subvols: list[SubvolumeModification], mount_options: list[str]) -> None:
        info('Creating subvolumes: ' + str(path))
        self.mount(path, self._TMP_BTRFS_MOUNT, create_target_mountpoint=True)

        for sub_vol in sorted(btrfs_subvols, key=lambda x: x.name):
            debug('Creating subvolume: ' + str(sub_vol.name))

            subvol_path: Path = self._TMP_BTRFS_MOUNT / sub_vol.name
            SysCommand("btrfs subvolume create -p " + str(subvol_path))

            if BtrfsMountOption.nodatacow.value in mount_options:
                try:
                    SysCommand('chattr +C ' + str(subvol_path))
                except SysCallError as err:
                    raise DiskError('Could not set nodatacow attribute at ' + str(subvol_path) + ': ' + str(err))

            if BtrfsMountOption.compress.value in mount_options:
                try:
                    SysCommand('chattr +c ' + str(subvol_path))
                except SysCallError as err:
                    raise DiskError('Could not set compress attribute at ' + str(subvol_path) + ': ' + str(err))

        umount(path)

    def create_btrfs_volumes(self, part_mod: PartitionModification, enc_conf: DiskEncryption | None = None) -> None:
        info('Creating subvolumes: ' + str(part_mod.safe_dev_path))

        luks_handler: Luks2 | None = None
        dev_path: Path = part_mod.safe_dev_path

        # unlock the partition first if it's encrypted
        if enc_conf and part_mod in enc_conf.partitions:
            if not part_mod.mapper_name:
                raise ValueError('No device path specified for modification')

            luks_handler = self.unlock_luks2_dev(part_mod.safe_dev_path, part_mod.mapper_name, enc_conf.encryption_password)

            if not luks_handler.mapper_dev:
                raise DiskError('Failed to unlock luks device')

            dev_path = luks_handler.mapper_dev

        self.mount(dev_path, self._TMP_BTRFS_MOUNT, create_target_mountpoint=True, options=part_mod.mount_options)

        for sub_vol in sorted(part_mod.btrfs_subvols, key=lambda x: x.name):
            debug('Creating subvolume: ' + str(sub_vol.name))

            subvol_path: Path = self._TMP_BTRFS_MOUNT / sub_vol.name
            SysCommand("btrfs subvolume create -p " + str(subvol_path))

        umount(dev_path)

        if luks_handler is not None and luks_handler.mapper_dev is not None:
            luks_handler.lock()

    @staticmethod
    def unlock_luks2_dev(dev_path: Path, mapper_name: str, enc_password: Password | None) -> Luks2:
        luks_handler: Luks2 = Luks2(dev_path, mapper_name=mapper_name, password=enc_password)

        if not luks_handler.is_unlocked():
            luks_handler.unlock()

        return luks_handler

    def umount_all_existing(self, device_path: Path) -> None:
        debug('Unmounting all existing partitions: {path}'.format(path=str(device_path)))
        existing_partitions: list[PartitionInfo] = self._devices[device_path].partition_infos

        for partition in existing_partitions:
            debug('Unmounting: {path}'.format(path=str(partition.path)))

            # unmount for existing encrypted partitions
            Luks2(partition.path).lock() if partition.fs_type == FilesystemType.Crypto_luks else umount(partition.path, recursive=True)

    def partition(self, modification: DeviceModification, partition_table: PartitionTable | None = None) -> None:
        """
        Create a partition table on the block device and create all partitions.
        """
        partition_table: PartitionTable = partition_table or self.partition_table
        disk: Disk = None

        # WARNING: the entire device will be wiped, and all data lost
        if modification.wipe:
            if partition_table.is_mbr() and (len(modification.partitions) > 3):
                raise DiskError('Too many partitions on disk, MBR disks can only have 3 primary partitions')

            self.wipe_dev(modification.device)
            disk = freshDisk(modification.device.disk.device, partition_table.value)

        if not modification.wipe:
            info('Use existing device: {path}'.format(path=str(modification.device_path)))
            disk = modification.device.disk

        info('Creating partitions: {path}'.format(path=str(modification.device_path)))

        # don't touch existing partitions
        filtered_part: list[PartitionModification] = [p for p in modification.partitions if not p.exists()]

        for part_mod in filtered_part:
            # if the entire disk got nuked, then we don't have to delete
            # any existing partitions anymore because they're all gone already
            requires_delete: bool = not modification.wipe
            self._setup_partition(part_mod, modification.device, disk, requires_delete=requires_delete)

        disk.commit()

    @staticmethod
    def swapon(path: Path) -> None:
        try:
            SysCommand(['swapon', str(path)])
        except SysCallError as err:
            raise DiskError('Could not enable swap {path}:\n{message}'.format(path=str(path), message=err.message))

    @staticmethod
    def mount(dev_path: Path, target_mountpoint: Path, mount_fs: str | None = None, create_target_mountpoint: bool = True, options: list[str] | None = None) -> None:
        if not options:
            options = []

        if create_target_mountpoint and not target_mountpoint.exists():
            target_mountpoint.mkdir(parents=True, exist_ok=True)

        if not target_mountpoint.exists():
            raise ValueError('Target mountpoint does not exist')

        lsblk_info: LsblkInfo = get_lsblk_info(dev_path)

        if target_mountpoint in lsblk_info.mountpoints:
            info('Device already mounted at {path}'.format(path=str(target_mountpoint)))
            return

        cmd: list[str] = ['mount']

        if len(options):
            cmd.extend(('-o', ','.join(options)))

        if mount_fs:
            cmd.extend(('-t', mount_fs))

        cmd.extend((str(dev_path), str(target_mountpoint)))

        command: str = ' '.join(cmd)
        debug('Mounting {path}: {command}'.format(path=str(dev_path), command=command))

        try:
            SysCommand(command)
        except SysCallError as err:
            raise DiskError('Could not mount {path}: {command}\n{message}'.format(path=str(dev_path), command=command, message=err.message))

    def detect_pre_mounted_mods(self, base_mountpoint: Path) -> list[DeviceModification]:
        part_mods: dict[Path, list[PartitionModification]] = {}

        for device in self.devices:
            for part_info in device.partition_infos:
                for mountpoint in part_info.mountpoints:
                    if is_subpath(mountpoint, base_mountpoint):
                        path: Path = Path(part_info.disk.device.path)

                        part_mods.setdefault(path, [])
                        part_mod: PartitionModification = PartitionModification.from_existing_partition(part_info)

                        if part_mod.mountpoint:
                            part_mod.mountpoint = Path(mountpoint.root) / mountpoint.relative_to(base_mountpoint)

                        if not part_mod.mountpoint:
                            for subvol in part_mod.btrfs_subvols:
                                if sm := subvol.mountpoint:
                                    subvol.mountpoint = Path(sm.root) / sm.relative_to(base_mountpoint)

                        part_mods[path].append(part_mod)
                        break

        device_mods: list[DeviceModification] = []

        for (device_path, mods) in part_mods.items():
            device_mod: DeviceModification = DeviceModification(self._devices[device_path], False, mods)
            device_mods.append(device_mod)

        return device_mods

    @staticmethod
    def _wipe(dev_path: Path) -> None:
        """
        Wipe a device (partition or otherwise) of meta-data, be it file system, LVM, etc.
        @param dev_path: Device path of the partition to be wiped.
        @type dev_path: str
        """
        with dev_path.open(mode='wb') as p:
            p.write(bytearray(1024))

    def wipe_dev(self, block_device: BDevice) -> None:
        """
        Wipe the block device of meta-data, be it a file system, LVM, etc.
        This is not intended to be secure, but rather to ensure that
        auto-discovery tools don't recognize anything here.
        """
        info('Wiping partitions and metadata: {path}'.format(path=str(block_device.device_info.path)))

        for partition in block_device.partition_infos:
            luks: Luks2 = Luks2(partition.path)

            if luks.is_luks_device():
                luks.erase()

            self._wipe(partition.path)

        self._wipe(block_device.device_info.path)

    @staticmethod
    def udev_sync() -> None:
        try:
            SysCommand('udevadm settle')
        except SysCallError as err:
            debug('Failed to synchronize with udev: ' + str(err))

device_handler: DeviceHandler = DeviceHandler()
