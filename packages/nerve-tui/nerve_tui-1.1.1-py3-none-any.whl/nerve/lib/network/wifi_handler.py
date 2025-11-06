# SPDX-FileCopyrightText: 2023 CELESTIFYX Team
# SPDX-License-Identifier: GPL-3.0-or-later

from asyncio import sleep
from dataclasses import dataclass
from pathlib import Path
from typing import (Any, assert_never)

from nerve.lib.exceptions import SysCallError
from nerve.lib.general import SysCommand
from nerve.lib.models.network import (WifiConfiguredNetwork, WifiNetwork)
from nerve.lib.network.wpa_supplicant import (WpaSupplicantConfig, WpaSupplicantNetwork)
from nerve.lib.output import debug
from nerve.lib.translationhandler import tr
from nerve.tui.menu_item import MenuItemGroup
from nerve.tui.ui.components import (ConfirmationScreen, InputScreen, LoadingScreen, NotifyScreen, TableSelectionScreen, tui)
from nerve.tui.ui.result import ResultType

@dataclass
class WpaCliResult:
    success: bool
    response: str | None = None
    error: str | None = None

class WifiHandler:
    def __init__(self) -> None:
        tui.set_main(self)
        self._wpa_config = WpaSupplicantConfig()

    @staticmethod
    def setup() -> Any:
        result: Any = tui.run()
        return result

    async def run(self) -> None:
        """
        This is the entry point that is called by components.TApp
        """
        wifi_iface: str | None = self._find_wifi_interface()

        if not wifi_iface:
            debug('No wifi interface found')
            tui.exit(False)

            return None

        prompt: str = tr('No network connection found') + '\n\n'
        prompt += tr('Would you like to connect to a Wifi?') + '\n'

        result: ResultType[bool] = await ConfirmationScreen[bool](MenuItemGroup.yes_no(), header=prompt, allow_skip=True, allow_reset=True).run()

        match result.type_:
            case ResultType.Selection:
                if not result.value():
                    tui.exit(False)
                    return None

            case ResultType.Skip | ResultType.Reset:
                tui.exit(False)
                return None

            case _:
                assert_never(result.type_)

        setup_result: bool = await self._setup_wifi(wifi_iface)
        tui.exit(setup_result)

        return None

    async def _enable_supplicant(self, wifi_iface: str) -> bool:
        self._wpa_config.load_config()

        result: WpaCliResult = self._wpa_cli('status')  # if it is being running it will blow up

        if result.success:
            debug('wpa_supplicant already running')
            return True

        if result.error and 'failed to connect to non-global ctrl_ifname'.lower() not in result.error.lower():
            debug('Unexpected wpa_cli failure')
            return False

        debug('wpa_supplicant not running, trying to enable')

        try:
            SysCommand('wpa_supplicant -B -i ' + wifi_iface + ' -c ' + str(self._wpa_config.config_file))
            result: WpaCliResult = self._wpa_cli('status')  # if it is being running it will blow up

            debug('successfully enabled wpa_supplicant' if result.success else 'failed to enable wpa_supplicant: ' + str(result.error))
            return result.success
        except SysCallError as err:
            debug('failed to enable wpa_supplicant: ' + str(err))
            return False

    @staticmethod
    def _find_wifi_interface() -> str | None:
        net_path: Path = Path('/sys/class/net')

        for iface in net_path.iterdir():
            maybe_wireless_path: Path = net_path / iface / 'wireless'

            if maybe_wireless_path.is_dir():
                return iface.name

        return None

    async def _setup_wifi(self, wifi_iface: str) -> bool:
        debug('Setting up wifi')

        if not await self._enable_supplicant(wifi_iface):
            debug('Failed to enable wpa_supplicant')
            return False

        if not wifi_iface:
            debug('No wifi interface found')
            await NotifyScreen(header=tr('No wifi interface found')).run()

            return False

        debug('Found wifi interface: ' + wifi_iface)

        async def get_wifi_networks() -> list[WifiNetwork]:
            debug('Scanning Wifi networks')
            result_: WpaCliResult = self._wpa_cli('scan', wifi_iface)

            if not result_.success:
                debug('Failed to scan wifi networks: ' + str(result_.error))
                return []

            await sleep(5)
            return self._get_scan_results(wifi_iface)

        result: ResultType[WifiNetwork] = await TableSelectionScreen[WifiNetwork](header=tr('Select wifi network to connect to'), loading_header=tr('Scanning wifi networks...'), data_callback=get_wifi_networks, allow_skip=True, allow_reset=True).run()
        network: WifiNetwork | None = None

        match result.type_:
            case ResultType.Selection:
                if not result.has_data():
                    debug('No networks found')
                    await NotifyScreen(header=tr('No wifi networks found')).run()

                    tui.exit(False)
                    return False

                network: WifiNetwork = result.value()

            case ResultType.Skip | ResultType.Reset:
                tui.exit(False)
                return False

            case _:
                assert_never(result.type_)

        existing_network: WpaSupplicantNetwork | None = self._wpa_config.get_existing_network(network.ssid)
        existing_psk: str | None = existing_network.psk if existing_network else None
        psk: str | None = await self._prompt_psk(existing_psk)

        if not psk:
            debug('No password specified')
            return False

        self._wpa_config.set_network(network, psk)
        self._wpa_config.write_config()

        wpa_result: WpaCliResult = self._wpa_cli('reconfigure')

        if not wpa_result.success:
            debug('Failed to reconfigure wpa_supplicant: ' + str(wpa_result.error))
            await self._notify_failure()

            return False

        await LoadingScreen(3, 'Setting up wifi...').run()
        network_id: int | None = self._find_network_id(network.ssid, wifi_iface)

        if not network_id:
            debug('Failed to find network id')
            await self._notify_failure()

            return False

        wpa_result: WpaCliResult = self._wpa_cli(f'enable {network_id}', wifi_iface)

        if not wpa_result.success:
            debug('Failed to enable network: ' + str(wpa_result.error))
            await self._notify_failure()

            return False

        await LoadingScreen(5, 'Connecting wifi...').run()
        return True

    @staticmethod
    async def _notify_failure() -> None:
        await NotifyScreen(header=tr('Failed setting up wifi')).run()

    @staticmethod
    def _wpa_cli(command: str, iface: str | None = None) -> WpaCliResult:
        cmd = 'wpa_cli'

        if iface:
            cmd += ' -i ' + str(iface)

        cmd += ' ' + command

        try:
            result: str = SysCommand(cmd).decode()

            if 'FAIL' in result:
                debug('wpa_cli returned FAIL: ' + result)
                return WpaCliResult(success=False, error='wpa_cli returned a failure: ' + result)

            return WpaCliResult(success=True, response=result)
        except SysCallError as err:
            debug('error running wpa_cli command: ' + str(err))
            return WpaCliResult(success=False, error='Error running wpa_cli command: ' + str(err))

    def _find_network_id(self, ssid: str, iface: str) -> int | None:
        result: WpaCliResult = self._wpa_cli('list_networks', iface)

        if not result.success:
            debug('Failed to list networks: ' + str(result.error))
            return None

        list_networks: str | None = result.response

        if not list_networks:
            debug('No networks found')
            return None

        existing_networks: list[WifiConfiguredNetwork] = WifiConfiguredNetwork.from_wpa_cli_output(list_networks)

        for network in existing_networks:
            if network.ssid == ssid:
                return network.network_id

        return None

    @staticmethod
    async def _prompt_psk(existing: str | None = None) -> str | None:
        result: ResultType[str] = await InputScreen(header=tr('Enter wifi password'), password=True, allow_skip=True, allow_reset=True, default_value=existing).run()

        if result.type_ != ResultType.Selection:
            debug('No password provided, aborting connection')
            return None

        return result.value()

    def _get_scan_results(self, iface: str) -> list[WifiNetwork]:
        debug('Retrieving scan results: ' + iface)

        try:
            result: WpaCliResult = self._wpa_cli('scan_results', iface)

            if not result.success:
                debug('Failed to retrieve scan results: ' + str(result.error))
                return []

            if not result.response:
                debug('No wifi networks found')
                return []

            networks: list[WifiNetwork] = WifiNetwork.from_wpa(result.response)
            return networks
        except SysCallError as err:
            debug('Unable to retrieve wifi results')
            raise err

wifi_handler: WifiHandler = WifiHandler()
