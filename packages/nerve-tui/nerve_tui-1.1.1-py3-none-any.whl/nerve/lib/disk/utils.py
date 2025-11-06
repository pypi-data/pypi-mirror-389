# SPDX-FileCopyrightText: 2023 CELESTIFYX Team
# SPDX-License-Identifier: GPL-3.0-or-later

from pathlib import Path
from pydantic import BaseModel

from nerve.lib.exceptions import (DiskError, SysCallError)
from nerve.lib.general import SysCommand
from nerve.lib.models.device import LsblkInfo
from nerve.lib.output import (debug, warn)

class LsblkOutput(BaseModel):
    blockdevices: list[LsblkInfo]

def _fetch_lsblk_info(dev_path: Path | str | None = None, reverse: bool = False, full_dev_path: bool = False) -> LsblkOutput:
    cmd: list[str] = ['lsblk', '--json', '--bytes', '--output', ','.join(LsblkInfo.fields())]

    if reverse:
        cmd.append('--inverse')

    if full_dev_path:
        cmd.append('--paths')

    if dev_path:
        cmd.append(str(dev_path))

    try:
        worker: SysCommand = SysCommand(cmd)
    except SysCallError as err:
        # Get the output minus the message/info from lsblk if it returns a non-zero exit code.
        if err.worker_log:
            debug('Error calling lsblk: ' + err.worker_log.decode())

        if dev_path:
            raise DiskError('Failed to read disk "' + str(dev_path) + '" with lsblk')

        raise err

    output: bytes = worker.output(remove_cr=False)
    return LsblkOutput.model_validate_json(output)

def get_lsblk_info(dev_path: Path | str, reverse: bool = False, full_dev_path: bool = False) -> LsblkInfo:
    infos: LsblkOutput = _fetch_lsblk_info(dev_path, reverse=reverse, full_dev_path=full_dev_path)

    if infos.blockdevices:
        return infos.blockdevices[0]

    raise DiskError('lsblk failed to retrieve information for "' + str(dev_path) + '"')

def get_all_lsblk_info() -> list[LsblkInfo]:
    return _fetch_lsblk_info().blockdevices

def get_lsblk_output() -> LsblkOutput:
    return _fetch_lsblk_info()

def find_lsblk_info(dev_path: Path | str, info: list[LsblkInfo]) -> LsblkInfo | None:
    if isinstance(dev_path, str):
        dev_path = Path(dev_path)

    for lsblk_info in info:
        if lsblk_info.path == dev_path:
            return lsblk_info

    return None

def disk_layouts() -> str:
    try:
        lsblk_output: LsblkOutput = get_lsblk_output()
    except SysCallError as err:
        warn("Could not return disk layouts: " + str(err))
        return ''

    return lsblk_output.model_dump_json(indent=4)

def umount(mountpoint: Path, recursive: bool = False) -> None:
    lsblk_info: LsblkInfo = get_lsblk_info(mountpoint)

    if not lsblk_info.mountpoints:
        return

    debug('Partition ' + str(mountpoint) + ' is currently mounted at: ' + str([str(m) for m in lsblk_info.mountpoints]))
    cmd: list[str] = ['umount']

    if recursive:
        cmd.append('-R')

    for path in lsblk_info.mountpoints:
        debug('Unmounting mountpoint: ' + str(path))
        SysCommand(cmd + [str(path)])
