# SPDX-FileCopyrightText: 2023 CELESTIFYX Team
# SPDX-License-Identifier: GPL-3.0-or-later

from pathlib import Path

from nerve.lib.args import config_handler
from nerve.lib.translationhandler import tr
from nerve.lib.disk.device_handler import device_handler
from nerve.lib.disk.partitioning_menu import manual_partitioning
from nerve.lib.menu.menu_helper import MenuHelper
from nerve.lib.models.device import (BDevice, BtrfsMountOption, DeviceModification, DiskLayoutConfiguration, DiskLayoutType, FilesystemType, LvmConfiguration, LvmLayoutType, LvmVolume, LvmVolumeGroup, ModificationStatus, PartitionFlag, PartitionModification, PartitionType, SectorSize, Size, SubvolumeModification, Unit, LvmVolumeStatus, DeviceInfo)
from nerve.lib.output import debug
from nerve.tui.curses_menu import SelectMenu
from nerve.tui.menu_item import (MenuItem, MenuItemGroup)
from nerve.tui.result import (ResultType, Result)
from nerve.tui.types import (Alignment, FrameProperties, Orientation, PreviewStyle)
from nerve.lib.output import FormattedOutput
from nerve.lib.utils.util import prompt_dir
from nerve.lib.utils.system_info import SystemInfo

def select_devices(preset: list[BDevice] | None = None) -> list[BDevice]:
    def _preview_device_selection(item: MenuItem) -> str | None:
        _device: DeviceInfo = item.get_value()
        dev: BDevice | None = device_handler.get_device(_device.path)

        return FormattedOutput.as_table(dev.partition_infos) if dev and dev.partition_infos else None

    if not preset:
        preset = []

    devices: list[BDevice] = device_handler.devices
    options: list[DeviceInfo] = [d.device_info for d in devices]
    presets: list[DeviceInfo] = [p.device_info for p in preset]

    group: MenuItemGroup = MenuHelper(options).create_menu_group()
    group.set_selected_by_value(presets)

    group.set_preview_for_all(_preview_device_selection)
    result: Result[DeviceInfo] = SelectMenu[DeviceInfo](group, alignment=Alignment.CENTER, search_enabled=False, multi=True, preview_style=PreviewStyle.BOTTOM, preview_size='auto', preview_frame=FrameProperties.max('Partitions'), allow_skip=True).run()

    match result.type_:
        case ResultType.Reset:
            return []

        case ResultType.Skip:
            return preset

        case ResultType.Selection:
            selected_device_info: list[DeviceInfo] = result.get_values()
            selected_devices: list[BDevice] = []

            for device in devices:
                if device.device_info in selected_device_info:
                    selected_devices.append(device)

            return selected_devices

def get_default_partition_layout(devices: list[BDevice], filesystem_type: FilesystemType | None = None) -> list[DeviceModification]:
    return [suggest_single_disk_layout(devices[0], filesystem_type=filesystem_type)] if len(devices) == 1 else suggest_multi_disk_layout(devices, filesystem_type=filesystem_type)

def _manual_partitioning(preset: list[DeviceModification], devices: list[BDevice]) -> list[DeviceModification]:
    modifications: list[DeviceModification] = []

    for device in devices:
        mod: DeviceModification | None = next(filter(lambda x: x.device == device, preset), None)

        if not mod:
            mod = DeviceModification(device, wipe=False)

        if device_mod := manual_partitioning(mod, device_handler.partition_table):
            modifications.append(device_mod)

    return modifications

def select_disk_config(preset: DiskLayoutConfiguration | None = None) -> DiskLayoutConfiguration | None:
    default_layout: str = DiskLayoutType.Default.display_msg()
    manual_mode:    str = DiskLayoutType.Manual.display_msg()
    pre_mount_mode: str = DiskLayoutType.Pre_mount.display_msg()

    items: list[MenuItem] = [
        MenuItem(default_layout, value=default_layout),
        MenuItem(manual_mode,    value=manual_mode),
        MenuItem(pre_mount_mode, value=pre_mount_mode)
    ]

    group: MenuItemGroup = MenuItemGroup(items, sort_items=False)

    if preset:
        group.set_selected_by_value(preset.config_type.display_msg())

    result: Result[str] = SelectMenu[str](group, allow_skip=True, alignment=Alignment.CENTER, frame=FrameProperties.min(tr('Disk configuration type')), allow_reset=True).run()

    match result.type_:
        case ResultType.Skip:
            return preset

        case ResultType.Reset:
            return None

        case ResultType.Selection:
            selection: str = result.get_value()

            if selection == pre_mount_mode:
                output: str = 'You will use whatever drive-setup is mounted at the specified directory\n'
                output += "WARNING: Nerve won't check the suitability of this setup\n"

                path: Path | None = prompt_dir(tr('Root mount directory'), output, allow_skip=True)

                if not path:
                    return None

                mods: list[DeviceModification] = device_handler.detect_pre_mounted_mods(path)
                return DiskLayoutConfiguration(config_type=DiskLayoutType.Pre_mount, device_modifications=mods, mountpoint=path)

            preset_devices: list[BDevice] = [mod.device for mod in preset.device_modifications] if preset else []
            devices:        list[BDevice] = select_devices(preset_devices)

            if not devices:
                return None

            if result.get_value() == default_layout:
                modifications: list[DeviceModification] = get_default_partition_layout(devices)

                if modifications:
                    return DiskLayoutConfiguration(config_type=DiskLayoutType.Default, device_modifications=modifications)

            elif result.get_value() == manual_mode:
                preset_mods:   list[DeviceModification] = preset.device_modifications if preset else []
                modifications: list[DeviceModification] = _manual_partitioning(preset_mods, devices)

                if modifications:
                    return DiskLayoutConfiguration(config_type=DiskLayoutType.Manual, device_modifications=modifications)

    return None

def select_lvm_config(disk_config: DiskLayoutConfiguration, preset: LvmConfiguration | None = None) -> LvmConfiguration | None:
    preset_value: str | None = preset.config_type.display_msg() if preset else None
    default_mode: str = LvmLayoutType.Default.display_msg()

    items: list[MenuItem] = [MenuItem(default_mode, value=default_mode)]
    group: MenuItemGroup = MenuItemGroup(items)

    group.set_focus_by_value(preset_value)
    result: Result[str] = SelectMenu[str](group, allow_reset=True, allow_skip=True, frame=FrameProperties.min(tr('LVM configuration type')), alignment=Alignment.CENTER).run()

    match result.type_:
        case ResultType.Skip:
            return preset

        case ResultType.Reset:
            return None

        case ResultType.Selection:
            if result.get_value() == default_mode:
                return suggest_lvm_layout(disk_config)

    return None

def _boot_partition(sector_size: SectorSize, using_gpt: bool) -> PartitionModification:
    flags: list[PartitionFlag] = [PartitionFlag.BOOT]

    size:  Size = Size(1, Unit.GiB, sector_size)
    start: Size = Size(1, Unit.MiB, sector_size)

    if using_gpt:
        flags.append(PartitionFlag.ESP)

    # boot partition
    return PartitionModification(status=ModificationStatus.Create, type=PartitionType.Primary, start=start, length=size, mountpoint=Path('/boot'), fs_type=FilesystemType.Fat32, flags=flags)

def select_main_filesystem_format() -> FilesystemType:
    items: list[MenuItem] = [
        MenuItem('btrfs', value=FilesystemType.Btrfs),
        MenuItem('ext4',  value=FilesystemType.Ext4),
        MenuItem('xfs',   value=FilesystemType.Xfs),
        MenuItem('f2fs',  value=FilesystemType.F2fs)
    ]

    if config_handler.args.advanced:
        items.append(MenuItem('ntfs', value=FilesystemType.Ntfs))

    group: MenuItemGroup = MenuItemGroup(items, sort_items=False)
    result: Result[FilesystemType] = SelectMenu[FilesystemType](group, alignment=Alignment.CENTER, frame=FrameProperties.min('Filesystem'), allow_skip=False).run()

    match result.type_:
        case ResultType.Selection:
            return result.get_value()

        case _:
            raise ValueError('Unhandled result type')

def select_mount_options() -> list[str]:
    prompt:      str = tr('Would you like to use compression or disable CoW?') + '\n'
    compression: str = tr('Use compression')
    disable_cow: str = tr('Disable Copy-on-Write')

    items: list[MenuItem] = [
        MenuItem(compression, value=BtrfsMountOption.compress.value),
        MenuItem(disable_cow, value=BtrfsMountOption.nodatacow.value)
    ]

    group: MenuItemGroup = MenuItemGroup(items, sort_items=False)
    result: Result[str] = SelectMenu[str](group, header=prompt, alignment=Alignment.CENTER, columns=2, orientation=Orientation.HORIZONTAL, search_enabled=False, allow_skip=True).run()

    match result.type_:
        case ResultType.Skip:
            return []

        case ResultType.Selection:
            return [result.get_value()]

        case _:
            raise ValueError('Unhandled result type')

def process_root_partition_size(total_size: Size, sector_size: SectorSize) -> Size:
    # root partition size processing
    total_device_size: Size = total_size.convert(Unit.GiB)

    if total_device_size.value > 500:
        # maximum size
        return Size(value=50, unit=Unit.GiB, sector_size=sector_size)
    elif total_device_size.value < 320:
        # minimum size
        return Size(value=32, unit=Unit.GiB, sector_size=sector_size)
    else:
        # 10% of total size
        length: int = (total_device_size.value // 10)
        return Size(value=length, unit=Unit.GiB, sector_size=sector_size)

def get_default_btrfs_subvols() -> list[SubvolumeModification]:
    # https://btrfs.wiki.kernel.org/index.php/FAQ
    # https://unix.stackexchange.com/questions/246976/btrfs-subvolume-uuid-clash
    # https://github.com/classy-giraffe/easy-arch/blob/main/easy-arch.sh
    return [
        SubvolumeModification(Path('@'),     Path('/')),
        SubvolumeModification(Path('@home'), Path('/home')),
        SubvolumeModification(Path('@log'),  Path('/var/log')),
        SubvolumeModification(Path('@pkg'),  Path('/var/cache/pacman/pkg'))
    ]

def _ask_yes_no_question(prompt: str) -> bool:
    group: MenuItemGroup = MenuItemGroup.yes_no()
    group.set_focus_by_value(MenuItem.yes().value)

    result: Result[bool] = SelectMenu[bool](group, header=prompt, alignment=Alignment.CENTER, columns=2, orientation=Orientation.HORIZONTAL, allow_skip=False).run()
    return result.item() == MenuItem.yes()

def suggest_single_disk_layout(device: BDevice, filesystem_type: FilesystemType | None = None, separate_home: bool | None = None) -> DeviceModification:
    if not filesystem_type:
        filesystem_type = select_main_filesystem_format()

    sector_size: SectorSize = device.device_info.sector_size
    total_size: Size = device.device_info.total_size

    available_space:             Size = total_size
    min_size_to_allow_home_part: Size = Size(64, Unit.GiB, sector_size)

    using_subvolumes: bool = False
    mount_options: list[str] = []

    if filesystem_type == FilesystemType.Btrfs:
        prompt: str = tr('Would you like to use BTRFS subvolumes with a default structure?') + '\n'

        using_subvolumes = _ask_yes_no_question(prompt)
        mount_options = select_mount_options()

    device_modification: DeviceModification = DeviceModification(device, wipe=True)
    using_gpt: bool = device_handler.partition_table.is_gpt()

    if using_gpt:
        # Remove space for the end alignment buffer
        available_space = available_space.gpt_end()

    available_space = available_space.align()

    # Used for reference: https://wiki.archlinux.org/title/partitioning
    boot_partition: PartitionModification = _boot_partition(sector_size, using_gpt)
    device_modification.add_partition(boot_partition)

    if separate_home is False or using_subvolumes or (total_size < min_size_to_allow_home_part):
        using_home_partition = False
    elif separate_home:
        using_home_partition = True
    else:
        prompt: str = tr('Would you like to create a separate partition for /home?') + '\n'
        using_home_partition = _ask_yes_no_question(prompt)

    # root partition
    root_start: Size = boot_partition.start + boot_partition.length

    # Set a size for / (/root)
    root_length: Size = process_root_partition_size(total_size, sector_size) if using_home_partition else available_space - root_start
    root_partition: PartitionModification = PartitionModification(status=ModificationStatus.Create, type=PartitionType.Primary, start=root_start, length=root_length, mountpoint=Path('/') if not using_subvolumes else None, fs_type=filesystem_type, mount_options=mount_options)

    device_modification.add_partition(root_partition)

    if using_subvolumes:
        root_partition.btrfs_subvols = get_default_btrfs_subvols()
    elif using_home_partition:
        # If we don't want to use subvolumes,
        # But we want to be able to reuse data between re-installations.
        # A second partition for /home would be nice if we have the space for it
        home_start:  Size = root_partition.start + root_partition.length
        home_length: Size = available_space - home_start

        flags: list[PartitionFlag] = []

        if using_gpt:
            flags.append(PartitionFlag.LINUX_HOME)

        home_partition: PartitionModification = PartitionModification(status=ModificationStatus.Create, type=PartitionType.Primary, start=home_start, length=home_length, mountpoint=Path('/home'), fs_type=filesystem_type, mount_options=mount_options, flags=flags)
        device_modification.add_partition(home_partition)

    return device_modification

def suggest_multi_disk_layout(devices: list[BDevice], filesystem_type: FilesystemType | None = None) -> list[DeviceModification]:
    if not devices:
        return []

    # Not really a rock solid foundation of information to stand on, but it's a start:
    # https://www.reddit.com/r/btrfs/comments/m287gp/partition_strategy_for_two_physical_disks/
    # https://www.reddit.com/r/btrfs/comments/9us4hr/what_is_your_btrfs_partitionsubvolumes_scheme/
    min_home_partition_size:     Size = Size(40, Unit.GiB, SectorSize.default())
    # rough estimate taking in to account user desktops etc. TODO: Catch user packages to detect size?
    desired_root_partition_size: Size = Size(32, Unit.GiB, SectorSize.default())

    mount_options: list[str] = []

    if not filesystem_type:
        filesystem_type = select_main_filesystem_format()

    # find a proper disk for /home
    possible_devices: list[BDevice] = [d for d in devices if d.device_info.total_size >= min_home_partition_size]
    home_device: BDevice | None = max(possible_devices, key=lambda d: d.device_info.total_size) if possible_devices else None

    # find a proper device for /root
    devices_delta: dict[BDevice, Size] = {}

    for device in devices:
        if device is not home_device:
            delta: Size = device.device_info.total_size - desired_root_partition_size
            devices_delta[device] = delta

    sorted_delta: list[tuple[BDevice, Size]] = sorted(devices_delta.items(), key=lambda x: x[1])
    root_device: BDevice | None = sorted_delta[0][0]

    if not home_device or not root_device:
        text: str = tr('The selected drives do not have the minimum capacity required for an automatic suggestion\n')
        text += tr('Minimum capacity for /home partition: {size}GiB\n'.format(size=min_home_partition_size.format_size(Unit.GiB)))
        text += tr('Minimum capacity for {name} partition: {size}GiB'.format(name=SystemInfo().os_name, size=desired_root_partition_size.format_size(Unit.GiB)))

        items: list[MenuItem] = [MenuItem(tr('Continue'))]
        group: MenuItemGroup = MenuItemGroup(items)

        SelectMenu(group).run()
        return []

    if filesystem_type == FilesystemType.Btrfs:
        mount_options = select_mount_options()

    device_paths: str = ', '.join([str(d.device_info.path) for d in devices])

    debug('Suggesting multi-disk-layout for devices: ' + device_paths)
    debug('/root: ' + str(root_device.device_info.path))
    debug('/home: ' + str(home_device.device_info.path))

    root_device_modification: DeviceModification = DeviceModification(root_device, wipe=True)
    home_device_modification: DeviceModification = DeviceModification(home_device, wipe=True)

    root_device_sector_size: SectorSize = root_device_modification.device.device_info.sector_size
    home_device_sector_size: SectorSize = home_device_modification.device.device_info.sector_size

    using_gpt: bool = device_handler.partition_table.is_gpt()

    # add boot partition to the root device
    boot_partition: PartitionModification = _boot_partition(root_device_sector_size, using_gpt)
    root_device_modification.add_partition(boot_partition)

    root_start:  Size = boot_partition.start + boot_partition.length
    root_length: Size = root_device.device_info.total_size - root_start

    if using_gpt:
        root_length = root_length.gpt_end()

    root_length = root_length.align()

    # add root partition to the root device
    root_partition: PartitionModification = PartitionModification(status=ModificationStatus.Create, type=PartitionType.Primary, start=root_start, length=root_length, mountpoint=Path('/'), mount_options=mount_options, fs_type=filesystem_type)
    root_device_modification.add_partition(root_partition)

    home_start:  Size = Size(1, Unit.MiB, home_device_sector_size)
    home_length: Size = home_device.device_info.total_size - home_start

    flags: list[PartitionFlag] = []

    if using_gpt:
        home_length -= home_length.gpt_end()
        flags.append(PartitionFlag.LINUX_HOME)

    home_length = home_length.align()

    # add home partition to a home device
    home_partition: PartitionModification = PartitionModification(status=ModificationStatus.Create, type=PartitionType.Primary, start=home_start, length=home_length, mountpoint=Path('/home'), mount_options=mount_options, fs_type=filesystem_type, flags=flags)
    home_device_modification.add_partition(home_partition)

    return [root_device_modification, home_device_modification]

def suggest_lvm_layout(disk_config: DiskLayoutConfiguration, filesystem_type: FilesystemType | None = None, vg_grp_name: str = 'NerveVg') -> LvmConfiguration:
    if disk_config.config_type != DiskLayoutType.Default:
        raise ValueError('LVM suggested volumes are only available for default partitioning')

    home_volume:      bool = True
    using_subvolumes: bool = False

    btrfs_subvols: list[SubvolumeModification] = []
    mount_options: list[str] = []

    if not filesystem_type:
        filesystem_type = select_main_filesystem_format()

    if filesystem_type == FilesystemType.Btrfs:
        prompt: str = tr('Would you like to use BTRFS subvolumes with a default structure?') + '\n'
        group: MenuItemGroup = MenuItemGroup.yes_no()

        group.set_focus_by_value(MenuItem.yes().value)
        result: Result[bool] = SelectMenu[bool](group, header=prompt, search_enabled=False, allow_skip=False, orientation=Orientation.HORIZONTAL, columns=2, alignment=Alignment.CENTER).run()

        using_subvolumes = MenuItem.yes() == result.item()
        mount_options    = select_mount_options()

    if using_subvolumes:
        btrfs_subvols = get_default_btrfs_subvols()
        home_volume   = False

    boot_part: PartitionModification | None = None
    other_part: list[PartitionModification] = []

    for mod in disk_config.device_modifications:
        for part in mod.partitions:
            is_boot: bool = part.is_boot()

            if is_boot:
                boot_part = part

            if not is_boot:
                other_part.append(part)

    if not boot_part:
        raise ValueError('Unable to find boot partition in partition modifications')

    total_vol_available: Size = sum([p.length for p in other_part], Size(0, Unit.B, SectorSize.default()))

    root_vol_size: Size = Size(20, Unit.GiB, SectorSize.default())
    home_vol_size: Size = total_vol_available - root_vol_size

    lvm_vol_group: LvmVolumeGroup = LvmVolumeGroup(vg_grp_name, pvs=other_part)
    root_vol: LvmVolume = LvmVolume(status=LvmVolumeStatus.Create, name='root', fs_type=filesystem_type, length=root_vol_size, mountpoint=Path('/'), btrfs_subvols=btrfs_subvols, mount_options=mount_options)
    lvm_vol_group.volumes.append(root_vol)

    if home_volume:
        home_vol: LvmVolume = LvmVolume(status=LvmVolumeStatus.Create, name='home', fs_type=filesystem_type, length=home_vol_size, mountpoint=Path('/home'))
        lvm_vol_group.volumes.append(home_vol)

    return LvmConfiguration(LvmLayoutType.Default, [lvm_vol_group])
