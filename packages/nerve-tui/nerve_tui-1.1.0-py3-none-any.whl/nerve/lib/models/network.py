# SPDX-FileCopyrightText: 2023 CELESTIFYX Team
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations
from dataclasses import (dataclass, field)
from enum import Enum
from typing import (TYPE_CHECKING, NotRequired, TypedDict, override)

from nerve.lib.output import debug
from nerve.lib.translationhandler import tr
from nerve.lib.models.profile import ProfileConfiguration

if TYPE_CHECKING:
    from nerve.lib.installer import Installer

class NicType(Enum):
    ISO    = "iso"
    NM     = "nm"
    MANUAL = "manual"

    def display_msg(self) -> str:
        match self:
            case NicType.ISO:
                return tr('Copy ISO network configuration to installation')

            case NicType.NM:
                return tr('Use NetworkManager (necessary to configure internet graphically in GNOME and KDE Plasma)')

            case NicType.MANUAL:
                return tr('Manual configuration')

class _NicSerialization(TypedDict):
    iface: str | None
    ip: str | None
    dhcp: bool
    gateway: str | None
    dns: list[str]

@dataclass
class Nic:
    iface: str | None = None
    ip: str | None = None
    dhcp: bool = True
    gateway: str | None = None
    dns: list[str] = field(default_factory=list)

    def table_data(self) -> dict[str, str | bool | list[str]]:
        return {
            'iface':   self.iface if self.iface else '',
            'ip':      self.ip if self.ip else '',
            'dhcp':    self.dhcp,
            'gateway': self.gateway if self.gateway else '',
            'dns':     self.dns
        }

    def json(self) -> _NicSerialization:
        return {
            'iface':   self.iface,
            'ip':      self.ip,
            'dhcp':    self.dhcp,
            'gateway': self.gateway,
            'dns':     self.dns
        }

    @staticmethod
    def parse_arg(arg: _NicSerialization) -> Nic:
        return Nic(iface=arg.get('iface', None), ip=arg.get('ip', None), dhcp=arg.get('dhcp', True), gateway=arg.get('gateway', None), dns=arg.get('dns', []))

    def as_systemd_config(self) -> str:
        match:   list[tuple[str, str]] = []
        network: list[tuple[str, str]] = []

        if self.iface:
            match.append(('Name', self.iface))

        if not self.dhcp:
            if self.ip:
                network.append(('Address', self.ip))

            if self.gateway:
                network.append(('Gateway', self.gateway))

            for dns in self.dns:
                network.append(('DNS', dns))

        if self.dhcp:
            network.append(('DHCP', 'yes'))

        config: dict[str, list[tuple[str, str]]] = {
            'Match': match,
            'Network': network
        }

        config_str: str = ''

        for (top, entries) in config.items():
            config_str += '[' + top + ']\n'
            config_str += '\n'.join([k + '=' + v for (k, v) in entries])
            config_str += '\n\n'

        return config_str

class _NetworkConfigurationSerialization(TypedDict):
    type: str
    nics: NotRequired[list[_NicSerialization]]

@dataclass
class NetworkConfiguration:
    type: NicType
    nics: list[Nic] = field(default_factory=list)

    def json(self) -> _NetworkConfigurationSerialization:
        config: _NetworkConfigurationSerialization = {
            'type': self.type.value
        }

        if self.nics:
            config['nics'] = [n.json() for n in self.nics]

        return config

    @staticmethod
    def parse_arg(config: _NetworkConfigurationSerialization) -> NetworkConfiguration | None:
        nic_type: str | None = config.get('type', None)

        if not nic_type:
            return None

        match NicType(nic_type):
            case NicType.ISO:
                return NetworkConfiguration(NicType.ISO)

            case NicType.NM:
                return NetworkConfiguration(NicType.NM)

            case NicType.MANUAL:
                nics_arg: list[_NicSerialization] = config.get('nics', [])

                if nics_arg:
                    nics: list[Nic] = [Nic.parse_arg(n) for n in nics_arg]
                    return NetworkConfiguration(NicType.MANUAL, nics)

        return None

    def install_network_config(self, installation: Installer, profile_config: ProfileConfiguration | None = None) -> None:
        match self.type:
            case NicType.ISO:
                installation.copy_iso_network_config(enable_services=True)

            case NicType.NM:
                installation.add_additional_packages('networkmanager')

                if profile_config and profile_config.profile and profile_config.profile.is_desktop_profile():
                    installation.add_additional_packages('network-manager-applet')

                installation.enable_service('NetworkManager.service')

            case NicType.MANUAL:
                for nic in self.nics:
                    installation.configure_nic(nic)

                installation.enable_service(['systemd-networkd', 'systemd-resolved'])

@dataclass
class WifiNetwork:
    bssid:        str
    frequency:    str
    signal_level: str
    flags:        str
    ssid:         str

    @override
    def __hash__(self) -> int:
        return hash((self.bssid, self.frequency, self.signal_level, self.flags, self.ssid))

    def table_data(self) -> dict[str, str | int]:
        """Format Wi-Fi data for table display"""
        return {
            'SSID':      self.ssid,
            'Signal':    self.signal_level + ' dBm',
            'Frequency': self.frequency + ' MHz',
            'Security':  self.flags,
            'BSSID':     self.bssid
        }

    @staticmethod
    def from_wpa(results: str) -> list[WifiNetwork]:
        entries: list[WifiNetwork] = []

        for line in results.splitlines():
            line: str = line.strip()

            if not line:
                continue

            parts: list[str] = line.split()

            if len(parts) != 5:
                continue

            wifi: WifiNetwork = WifiNetwork(bssid=parts[0], frequency=parts[1], signal_level=parts[2], flags=parts[3], ssid=parts[4])
            entries.append(wifi)

        return entries

@dataclass
class WifiConfiguredNetwork:
    network_id: int
    ssid: str
    bssid: str
    flags: list[str]

    @classmethod
    def from_wpa_cli_output(cls, list_networks: str) -> list[WifiConfiguredNetwork]:
        """
        Example output from 'wpa_cli list_networks'

        Selected interface 'wlan0'
        network id / ssid / bssid / flags
        0	WifiGuest any	[CURRENT]
        1		any [DISABLED]
        2		any [DISABLED]
        """
        lines: list[str] = list_networks.strip().splitlines()[1:]
        networks: list[WifiConfiguredNetwork] = []

        for line in lines:
            line: str = line.strip()
            parts: list[str] = line.split('\t')

            if len(parts) < 3:
                continue

            try:
                flags: list[str] = []
                networks.append(WifiConfiguredNetwork(network_id=int(parts[0]), ssid=parts[1], bssid=parts[2], flags=flags))
            except (ValueError, IndexError):
                debug('Parsing error for network output')

        return networks
