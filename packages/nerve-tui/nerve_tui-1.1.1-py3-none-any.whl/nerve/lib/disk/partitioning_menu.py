# SPDX-FileCopyrightText: 2023 CELESTIFYX Team
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

import re

from pathlib import Path
from typing import (override, Iterator, cast)

from nerve.lib.models import (BDevice, DeviceInfo)
from nerve.lib.models.device import (BtrfsMountOption, DeviceModification, FilesystemType, ModificationStatus, PartitionFlag, PartitionModification, PartitionTable, PartitionType, SectorSize, Size, Unit)
from nerve.lib.translationhandler import tr
from nerve.tui.curses_menu import (EditMenu, SelectMenu)
from nerve.tui.menu_item import (MenuItem, MenuItemGroup)
from nerve.tui.result import (ResultType, Result)
from nerve.tui.types import (Alignment, FrameProperties, Orientation)
from nerve.lib.menu.list_manager import ListManager
from nerve.lib.output import FormattedOutput
from nerve.lib.utils.util import prompt_dir
from nerve.lib.disk.subvolume_menu import SubvolumeMenu

class FreeSpace:
    def __init__(self, start: Size, end: Size) -> None:
        self.start: Size = start
        self.end:   Size = end

    @property
    def length(self) -> Size:
        return self.end - self.start

    def table_data(self) -> dict[str, str]:
        """
        Called for displaying data in table format
        """
        return {
            'Start': self.start.format_size(Unit.sectors, self.start.sector_size, include_unit=False),
            'End':   self.end.format_size(Unit.sectors, self.start.sector_size, include_unit=False),
            'Size':  self.length.format_highest()
        }

class DiskSegment:
    def __init__(self, segment: PartitionModification | FreeSpace) -> None:
        self.segment = segment

    def table_data(self) -> dict[str, str]:
        """
        Called for displaying data in table format
        """
        if isinstance(self.segment, PartitionModification):
            return self.segment.table_data()

        part_mod: PartitionModification = PartitionModification(status=ModificationStatus.Create, type=PartitionType.Unknown, start=self.segment.start, length=self.segment.length)
        data: dict[str, str] = part_mod.table_data()

        data.update({
            'Status':  'free',
            'Type':    '',
            'FS type': ''
        })

        return data

class PartitioningList(ListManager[DiskSegment]):
    def __init__(self, device_mod: DeviceModification, partition_table: PartitionTable) -> None:
        device: BDevice = device_mod.device

        self._device = device
        self._wipe: bool = device_mod.wipe
        self._buffer: Size = Size(1, Unit.MiB, device.device_info.sector_size)
        self._using_gpt: bool = device_mod.using_gpt(partition_table)

        self._actions: dict[str, str] = {
            'create_new_partition':     tr('Create a new partition'),
            'suggest_partition_layout': tr('Suggest partition layout'),
            'remove_added_partitions':  tr('Remove all newly added partitions'),
            'assign_mountpoint':        tr('Assign mountpoint'),
            'mark_formatting':          tr('Mark/Unmark to be formatted (wipes data)')
        }

        if self._using_gpt:
            self._actions.update({
                'mark_esp':      tr('Mark/Unmark as ESP'),
                'mark_xbootldr': tr('Mark/Unmark as XBOOTLDR')
            })

        self._actions.update({
            'mark_bootable':         tr('Mark/Unmark as bootable'),
            'set_filesystem':        tr('Change filesystem'),
            'btrfs_mark_compressed': tr('Mark/Unmark as compressed'),  # btrfs only
            'btrfs_mark_nodatacow':  tr('Mark/Unmark as nodatacow'),   # btrfs only
            'btrfs_set_subvolumes':  tr('Set subvolumes'),             # btrfs only
            'delete_partition':      tr('Delete partition')
        })

        device_partitions: list[PartitionModification] = device_mod.partitions if device_mod.partitions else [PartitionModification.from_existing_partition(partition) for partition in device.partition_infos]

        prompt: str = tr('Partition management: {path}'.format(path=str(device.device_info.path))) + '\n'
        prompt += tr('Total length: {size}'.format(size=device.device_info.total_size.format_size(Unit.MiB)))

        self._info = prompt + '\n'
        display_actions: list[str] = list(self._actions.values())

        super().__init__(self.as_segments(device_partitions), display_actions[:1], display_actions[2:], (self._info + self.wipe_str()))

    def wipe_str(self) -> str:
        return tr('Wipe') + ': ' + str(self._wipe)

    def as_segments(self, device_partitions: list[PartitionModification]) -> list[DiskSegment]:
        end: Size = self._device.device_info.total_size

        if self._using_gpt:
            end = end.gpt_end()

        end = end.align()

        # Reorder device_partitions to move all deleted partitions to the top
        device_partitions.sort(key=lambda p: p.is_delete(), reverse=True)
        free_space: FreeSpace

        partitions: list[DiskSegment] = [DiskSegment(p) for p in device_partitions if not p.is_delete()]
        segments:   list[DiskSegment] = [DiskSegment(p) for p in device_partitions]

        if not partitions:
            free_space = FreeSpace(self._buffer, end)
            return (segments + [DiskSegment(free_space)]) if free_space.length > self._buffer else segments

        (first_part_index, first_partition) = next((i, disk_segment) for (i, disk_segment) in enumerate(segments) if isinstance(disk_segment.segment, PartitionModification) and not disk_segment.segment.is_delete())
        prev_partition: DiskSegment = first_partition
        index: int = 0

        for partition in segments[1:]:
            index += 1

            if isinstance(partition.segment, PartitionModification) and partition.segment.is_delete():
                continue

            if prev_partition.segment.end < partition.segment.start:
                free_space = FreeSpace(prev_partition.segment.end, partition.segment.start)

                if free_space.length > self._buffer:
                    segments.insert(index, DiskSegment(free_space))
                    index += 1

            prev_partition = partition

        if first_partition.segment.start > self._buffer:
            free_space = FreeSpace(self._buffer, first_partition.segment.start)

            if free_space.length > self._buffer:
                segments.insert(first_part_index, DiskSegment(free_space))

        if partitions[-1].segment.end < end:
            free_space = FreeSpace(partitions[-1].segment.end, end)

            if free_space.length > self._buffer:
                segments.append(DiskSegment(free_space))

        return segments

    @staticmethod
    def get_part_mods(disk_segments: list[DiskSegment]) -> list[PartitionModification]:
        return [s.segment for s in disk_segments if isinstance(s.segment, PartitionModification)]

    def get_device_mod(self) -> DeviceModification:
        disk_segments: list[DiskSegment] = super().run()
        partitions: list[PartitionModification] = self.get_part_mods(disk_segments)

        return DeviceModification(self._device, self._wipe, partitions)

    @override
    def _run_actions_on_entry(self, entry: DiskSegment) -> None:
        # Do not create a menu when the segment is free space
        self._data = self.handle_action(action='', entry=entry, data=self._data) if isinstance(entry.segment, FreeSpace) else super()._run_actions_on_entry(entry)

    @override
    def selected_action_display(self, selection: DiskSegment) -> str:
        if isinstance(selection.segment, PartitionModification):
            if selection.segment.status == ModificationStatus.Create:
                return tr('Partition - New')
            elif selection.segment.is_delete() and selection.segment.dev_path:
                title: str = tr('Partition') + '\n\n'
                title += 'status: delete\n'
                title += 'device: ' + str(selection.segment.dev_path) + '\n'

                for part in self._device.partition_infos:
                    if (part.path == selection.segment.dev_path) and part.partuuid:
                        title += 'partuuid: ' + part.partuuid

                return title

            return str(selection.segment.dev_path)

        return ''

    @override
    def filter_options(self, selection: DiskSegment, options: list[str]) -> list[str]:
        not_filter: list[str] = []

        if isinstance(selection.segment, PartitionModification):
            if selection.segment.is_delete():
                not_filter = list(self._actions.values())
            # only display formatting if the partition exists already
            elif not selection.segment.exists():
                not_filter += [self._actions['mark_formatting']]
            else:
                # Only allow options if the existing partition
                # was marked as formatting, otherwise we run into issues where
                # 1. Select a new fs -> potentially mark as wipe now
                # 2. Switch back to the old filesystem -> should unmark wipe now, but
                #     how do we know it was the original one?
                not_filter += [
                    self._actions['set_filesystem'],
                    self._actions['mark_bootable']
                ]

                if self._using_gpt:
                    not_filter += [
                        self._actions['mark_esp'],
                        self._actions['mark_xbootldr']
                    ]

                not_filter += [
                    self._actions['btrfs_mark_compressed'],
                    self._actions['btrfs_mark_nodatacow'],
                    self._actions['btrfs_set_subvolumes']
                ]

            # non btrfs partitions shouldn't get btrfs options
            not_filter += [
                self._actions['btrfs_mark_compressed'],
                self._actions['btrfs_mark_nodatacow'],
                self._actions['btrfs_set_subvolumes']
            ] if selection.segment.fs_type != FilesystemType.Btrfs else [self._actions['assign_mountpoint']]

        return [o for o in options if o not in not_filter]

    @override
    def handle_action(self, action: str, entry: DiskSegment | None, data: list[DiskSegment]) -> list[DiskSegment]:
        if not entry:
            action_key: str = [k for (k, v) in self._actions.items() if v == action][0]

            match action_key:
                case 'suggest_partition_layout':
                    part_mods: list[PartitionModification] = self.get_part_mods(data)
                    device_mod: DeviceModification | None = self._suggest_partition_layout(part_mods)

                    if device_mod and device_mod.partitions:
                        data = self.as_segments(device_mod.partitions)

                        self._wipe   = device_mod.wipe
                        self._prompt = self._info + self.wipe_str()

                case 'remove_added_partitions':
                    if self._reset_confirmation():
                        data = [s for s in data if isinstance(s.segment, PartitionModification) and s.segment.is_exists_or_modify()]

        elif isinstance(entry.segment, PartitionModification):
            partition: PartitionModification = entry.segment
            action_key: str = [k for (k, v) in self._actions.items() if v == action][0]

            match action_key:
                case 'assign_mountpoint':
                    new_mountpoint = self._prompt_mountpoint()

                    if not partition.is_swap():
                        if partition.is_home():
                            partition.invert_flag(PartitionFlag.LINUX_HOME)

                        partition.mountpoint = new_mountpoint

                        if partition.is_root():
                            partition.flags = []

                        if partition.is_boot():
                            partition.flags = []
                            partition.set_flag(PartitionFlag.BOOT)

                            if self._using_gpt:
                                partition.set_flag(PartitionFlag.ESP)

                        if partition.is_home():
                            partition.flags = []
                            partition.set_flag(PartitionFlag.LINUX_HOME)

                case 'mark_formatting':
                    self._prompt_formatting(partition)

                case 'mark_bootable':
                    if not partition.is_swap():
                        partition.invert_flag(PartitionFlag.BOOT)

                case 'mark_esp':
                    if not partition.is_root() and not partition.is_home() and not partition.is_swap():
                        if PartitionFlag.XBOOTLDR in partition.flags:
                            partition.invert_flag(PartitionFlag.XBOOTLDR)

                        partition.invert_flag(PartitionFlag.ESP)

                case 'mark_xbootldr':
                    if not partition.is_root() and not partition.is_home() and not partition.is_swap():
                        if PartitionFlag.ESP in partition.flags:
                            partition.invert_flag(PartitionFlag.ESP)

                        partition.invert_flag(PartitionFlag.XBOOTLDR)

                case 'set_filesystem':
                    fs_type: FilesystemType = self._prompt_partition_fs_type()

                    if partition.is_swap():
                        partition.invert_flag(PartitionFlag.SWAP)

                    partition.fs_type = fs_type

                    if partition.is_swap():
                        partition.mountpoint = None
                        partition.flags      = []

                        partition.set_flag(PartitionFlag.SWAP)

                    # btrfs subvolumes will define mountpoints
                    if fs_type == FilesystemType.Btrfs:
                        partition.mountpoint = None

                case 'btrfs_mark_compressed':
                    self._toggle_mount_option(partition, BtrfsMountOption.compress)

                case 'btrfs_mark_nodatacow':
                    self._toggle_mount_option(partition, BtrfsMountOption.nodatacow)

                case 'btrfs_set_subvolumes':
                    self._set_btrfs_subvolumes(partition)

                case 'delete_partition':
                    data = self._delete_partition(partition, data)

        else:
            part_mods = self.get_part_mods(data)
            index     = data.index(entry)

            part_mods.insert(index, self._create_new_partition(entry.segment))
            data = self.as_segments(part_mods)

        return data

    def _delete_partition(self, entry: PartitionModification, data: list[DiskSegment]) -> list[DiskSegment]:
        part_mods: list[PartitionModification] = []

        if entry.is_exists_or_modify():
            entry.status = ModificationStatus.Delete
            part_mods    = self.get_part_mods(data)

        if not entry.is_exists_or_modify():
            part_mods = [cast(PartitionModification, d.segment) for d in data if isinstance(d.segment, PartitionModification) and (d.segment != entry)]

        return self.as_segments(part_mods)

    @staticmethod
    def _toggle_mount_option(partition: PartitionModification, option: BtrfsMountOption) -> None:
        if not option.value not in partition.mount_options:
            partition.mount_options = [o for o in partition.mount_options if o != option.value]
            return

        if option == BtrfsMountOption.compress:
            partition.mount_options = [o for o in partition.mount_options if o != BtrfsMountOption.nodatacow.value]

        partition.mount_options = [o for o in partition.mount_options if not o.startswith(BtrfsMountOption.compress.name)]
        partition.mount_options.append(str(option.value))

    @staticmethod
    def _set_btrfs_subvolumes(partition: PartitionModification) -> None:
        partition.btrfs_subvols = SubvolumeMenu(partition.btrfs_subvols, prompt=None).run()

    def _prompt_formatting(self, partition: PartitionModification) -> None:
        # an existing partition can toggle between Exist or Modify
        if partition.is_modify():
            partition.status = ModificationStatus.Exist
            return

        elif partition.exists():
            partition.status = ModificationStatus.Modify

        # If we mark a partition for formatting, but the format is CRYPTO LUKS, there's no point in formatting it really
        # without asking the user which inner-filesystem they want to use. Since the flag 'encrypted' = True is already set,
        # it's safe to change the filesystem for this partition.
        if partition.fs_type == FilesystemType.Crypto_luks:
            prompt: str = tr('This partition is currently encrypted, to format it a filesystem has to be specified') + '\n'
            fs_type: FilesystemType = self._prompt_partition_fs_type(prompt)

            partition.fs_type = fs_type

            if fs_type == FilesystemType.Btrfs:
                partition.mountpoint = None

    @staticmethod
    def _prompt_mountpoint() -> Path:
        mountpoint: Path = prompt_dir(tr('Mountpoint'), tr('Partition mount-points are relative to inside the installation, the boot would be /boot as an example.') + '\n', validate=False, allow_skip=False)

        assert mountpoint
        return mountpoint

    @staticmethod
    def _prompt_partition_fs_type(prompt: str | None = None) -> FilesystemType:
        fs_types: Iterator[FilesystemType] = filter(lambda fs: fs != FilesystemType.Crypto_luks, FilesystemType)
        items: list[MenuItem] = [MenuItem(fs.value, value=fs) for fs in fs_types]

        group: MenuItemGroup = MenuItemGroup(items, sort_items=False)
        result: Result[FilesystemType] = SelectMenu[FilesystemType](group, header=prompt, alignment=Alignment.CENTER, frame=FrameProperties.min(tr('Filesystem')), allow_skip=False).run()

        match result.type_:
            case ResultType.Selection:
                return result.get_value()

            case _:
                raise ValueError('Unhandled result type')

    def _validate_value(self, sector_size: SectorSize, max_size: Size, text: str) -> Size | None:
        match: re.Match[str] | None = re.match(pattern=r'([0-9]+)([a-zA-Z|%]*)', string=text, flags=re.I)

        if not match:
            return None

        (str_value, unit) = match.groups()
        (value, unit)     = (int(max_size.value * (int(str_value) / 100)), max_size.unit.name) if unit == '%' else (int(str_value), unit)

        if unit and unit not in Unit.get_all_units():
            return None

        unit = Unit[unit] if unit else Unit.sectors
        size = Size(value, unit, sector_size)

        if size.format_highest() == max_size.format_highest():
            return max_size
        elif (size > max_size) or (size < self._buffer):
            return None

        return None

    def _prompt_size(self, free_space: FreeSpace) -> Size:
        def validate(_value: str | None) -> str | None:
            if not _value:
                return None

            _size: Size | None = self._validate_value(sector_size, max_size, _value)
            return tr('Invalid size') if not _size else None

        device_info: DeviceInfo = self._device.device_info
        sector_size = device_info.sector_size

        text:             str = tr('Selected free space segment on device {path}:'.format(path=str(device_info.path))) + '\n\n'
        free_space_table: str = FormattedOutput.as_table([free_space])
        prompt:           str = text + free_space_table + '\n'

        max_sectors: str = free_space.length.format_size(Unit.sectors, sector_size)
        max_bytes:   str = free_space.length.format_size(Unit.B)

        prompt += tr('Size: {sectors} / {bytes}'.format(sectors=max_sectors, bytes=max_bytes)) + '\n\n'
        prompt += tr('All entered values can be suffixed with a unit: %, B, KB, KiB, MB, MiB...') + '\n'
        prompt += tr('If no unit is provided, the value is interpreted as sectors') + '\n'

        max_size: Size = free_space.length
        title: str = tr('Size (default: {size}): '.format(size=max_size.format_highest()))

        result: Result[str] = EditMenu(title, header=prompt + '\b', allow_skip=True, validator=validate).input()
        size: Size | None = None

        match result.type_:
            case ResultType.Skip:
                size = max_size

            case ResultType.Selection:
                value: str = result.text()
                size = self._validate_value(sector_size, max_size, value) if value else max_size

        assert size
        return size

    def _create_new_partition(self, free_space: FreeSpace) -> PartitionModification:
        length: Size = self._prompt_size(free_space)
        fs_type: FilesystemType = self._prompt_partition_fs_type()
        mountpoint: Path | None = None

        if fs_type not in (FilesystemType.Btrfs, FilesystemType.LinuxSwap):
            mountpoint = self._prompt_mountpoint()

        partition: PartitionModification = PartitionModification(status=ModificationStatus.Create, type=PartitionType.Primary, start=free_space.start, length=length, fs_type=fs_type, mountpoint=mountpoint)

        if partition.mountpoint == Path('/boot'):
            partition.set_flag(PartitionFlag.BOOT)

            if self._using_gpt:
                partition.set_flag(PartitionFlag.ESP)

        elif partition.is_swap():
            partition.mountpoint = None
            partition.flags      = []

            partition.set_flag(PartitionFlag.SWAP)

        return partition

    @staticmethod
    def _reset_confirmation() -> bool:
        prompt: str = tr('This will remove all newly added partitions, continue?') + '\n'
        result: Result[bool] = SelectMenu[bool](MenuItemGroup.yes_no(), header=prompt, alignment=Alignment.CENTER, orientation=Orientation.HORIZONTAL, columns=2, reset_warning_msg=prompt, allow_skip=False).run()

        return result.item() == MenuItem.yes()

    def _suggest_partition_layout(self, data: list[PartitionModification]) -> DeviceModification | None:
        # if modifications have been done already, inform the user
        # that this operation will erase those modifications
        if any([not entry.exists() for entry in data]) and not self._reset_confirmation():
            return None

        from nerve.lib.interactions.disk_conf import suggest_single_disk_layout
        return suggest_single_disk_layout(self._device)

def manual_partitioning(device_mod: DeviceModification, partition_table: PartitionTable) -> DeviceModification | None:
    menu_list: PartitioningList = PartitioningList(device_mod, partition_table)
    mod: DeviceModification = menu_list.get_device_mod()

    return device_mod if menu_list.is_last_choice_cancel() else (mod if mod.partitions else None)
