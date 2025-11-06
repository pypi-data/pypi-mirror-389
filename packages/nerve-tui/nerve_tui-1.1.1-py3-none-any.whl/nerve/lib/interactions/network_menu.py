# SPDX-FileCopyrightText: 2023 CELESTIFYX Team
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

import ipaddress

from typing import (assert_never, override, ValuesView)

from nerve.lib.translationhandler import tr
from nerve.tui.curses_menu import (EditMenu, SelectMenu)
from nerve.tui.menu_item import (MenuItem, MenuItemGroup)
from nerve.tui.result import (ResultType, Result)
from nerve.tui.types import (Alignment, FrameProperties)
from nerve.lib.menu.list_manager import ListManager
from nerve.lib.models.network import (NetworkConfiguration, Nic, NicType)
from nerve.lib.networking import list_interfaces

class ManualNetworkConfig(ListManager[Nic]):
    def __init__(self, prompt: str, preset: list[Nic]) -> None:
        self._actions: list[str] = [
            tr('Add interface'),
            tr('Edit interface'),
            tr('Delete interface')
        ]

        super().__init__(entries=preset, base_actions=[self._actions[0]], sub_menu_actions=self._actions[1:], prompt=prompt)

    @override
    def selected_action_display(self, selection: Nic) -> str:
        return selection.iface if selection.iface else ''

    @override
    def handle_action(self, action: str, entry: Nic | None, data: list[Nic]) -> list[Nic]:
        if action == self._actions[0]:  # add
            iface: str | None = self._select_iface(data)

            if iface:
                nic: Nic = Nic(iface=iface)
                nic = self._edit_iface(nic)

                data += [nic]

        elif entry:
            if action == self._actions[1]:  # edit interface
                data = [d for d in data if d.iface != entry.iface]
                data.append(self._edit_iface(entry))
            elif action == self._actions[2]:  # delete
                data = [d for d in data if d != entry]

        return data

    @staticmethod
    def _select_iface(data: list[Nic]) -> str | None:
        all_ifaces: ValuesView[str] = list_interfaces().values()
        existing_ifaces: list[str | None] = [d.iface for d in data]
        available: set[str] = set(all_ifaces) - set(existing_ifaces)

        if not available:
            return None

        if not available:
            return None

        items: list[MenuItem] = [MenuItem(i, value=i) for i in available]
        group: MenuItemGroup = MenuItemGroup(items, sort_items=True)

        result: Result[str] = SelectMenu[str](group, alignment=Alignment.CENTER, frame=FrameProperties.min(tr('Interfaces')), allow_skip=True).run()

        match result.type_:
            case ResultType.Skip:
                return None

            case ResultType.Selection:
                return result.get_value()

            case ResultType.Reset:
                raise ValueError('Unhandled result type')

            case _:
                assert_never(result.type_)

    @staticmethod
    def _get_ip_address(title: str, header: str, allow_skip: bool, multi: bool, preset: str | None = None) -> str:
        def validator(ip: str | None) -> str | None:
            failure: str = tr('You need to enter a valid IP in IP-config mode')

            if not ip:
                return failure

            ips: list[str] = ip.split(' ') if multi else [ip]

            try:
                for ip in ips:
                    ipaddress.ip_interface(ip)

                return None
            except ValueError:
                return failure

        result: Result[str] = EditMenu(title, header=header, validator=validator, allow_skip=allow_skip, default_text=preset).input()

        match result.type_:
            case ResultType.Skip:
                return preset

            case ResultType.Selection:
                return result.text()

            case ResultType.Reset:
                raise ValueError('Unhandled result type')

            case _:
                assert_never(result.type_)

    def _edit_iface(self, edit_nic: Nic) -> Nic:
        iface_name: str | None = edit_nic.iface
        mode: str | None = None

        modes: set[str] = {
            'DHCP (auto detect)',
            'IP (static)'
        }

        default_mode: str = 'DHCP (auto detect)'
        header:       str = tr('Select which mode to configure for "{name}"'.format(name=iface_name)) + '\n'

        items: list[MenuItem] = [MenuItem(m, value=m) for m in modes]
        group: MenuItemGroup = MenuItemGroup(items, sort_items=True)

        group.set_default_by_value(default_mode)
        result: Result[str] = SelectMenu[str](group, header=header, allow_skip=False, alignment=Alignment.CENTER, frame=FrameProperties.min(tr('Modes'))).run()

        match result.type_:
            case ResultType.Selection:
                mode = result.get_value()

            case ResultType.Reset:
                raise ValueError('Unhandled result type')

            case ResultType.Skip:
                raise ValueError('The mode menu should not be skippable')

            case _:
                assert_never(result.type_)

        if mode == 'IP (static)':
            header: str = tr('Enter the IP and subnet for ' + str(iface_name) + ' (example: 192.168.0.5/24): ') + '\n'
            ip:     str = self._get_ip_address(tr('IP address'), header, allow_skip=False, multi=False)

            header:  str  = tr('Enter your gateway (router) IP address (leave blank for none)') + '\n'
            gateway: str = self._get_ip_address(tr('Gateway address'), header, allow_skip=True, multi=False)

            display_dns: str = ' '.join(edit_nic.dns) if edit_nic.dns else None
            header:      str = tr('Enter your DNS servers with space separated (leave blank for none)') + '\n'

            dns_servers: str = self._get_ip_address(tr('DNS servers'), header, allow_skip=True, multi=True, preset=display_dns)
            dns: list[str] = []

            if dns_servers is not None:
                dns = dns_servers.split(' ')

            return Nic(iface=iface_name, ip=ip, gateway=gateway, dns=dns, dhcp=False)

        # this will contain network iface names
        return Nic(iface=iface_name)

def ask_to_configure_network(preset: NetworkConfiguration | None) -> NetworkConfiguration | None:
    """
    Configure the network on the newly installed system
    """
    items: list[MenuItem] = [MenuItem(n.display_msg(), value=n) for n in NicType]
    group: MenuItemGroup = MenuItemGroup(items, sort_items=True)

    if preset:
        group.set_selected_by_value(preset.type)

    result: Result[NicType] = SelectMenu[NicType](group, alignment=Alignment.CENTER, frame=FrameProperties.min(tr('Network configuration')), allow_reset=True, allow_skip=True).run()

    match result.type_:
        case ResultType.Skip:
            return preset

        case ResultType.Reset:
            return None

        case ResultType.Selection:
            config: NicType = result.get_value()

            match config:
                case NicType.ISO:
                    return NetworkConfiguration(NicType.ISO)

                case NicType.NM:
                    return NetworkConfiguration(NicType.NM)

                case NicType.MANUAL:
                    preset_nics: list[Nic] = preset.nics if preset else []
                    nics:        list[Nic] = ManualNetworkConfig(tr('Configure interfaces'), preset_nics).run()

                    if nics:
                        return NetworkConfiguration(NicType.MANUAL, nics)

    return preset
