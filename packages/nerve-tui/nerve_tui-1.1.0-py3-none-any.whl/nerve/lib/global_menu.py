# SPDX-FileCopyrightText: 2023 CELESTIFYX Team
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations
from typing import override

from nerve.tui.menu_item import (MenuItem, MenuItemGroup)
from nerve.lib import __packages__
from nerve.lib.translationhandler import tr
from nerve.lib.disk.disk_menu import DiskLayoutConfigurationMenu
from nerve.lib.packages import list_available_packages
from nerve.lib.args import Config
from nerve.lib.applications.application_menu import ApplicationMenu
from nerve.lib.authentication.authentication_menu import AuthenticationMenu
from nerve.lib.configuration import save_config
from nerve.lib.hardware import SysInfo
from nerve.lib.interactions.general_conf import (add_number_of_parallel_downloads, ask_additional_packages_to_install, ask_for_a_timezone, ask_hostname, ask_ntp)
from nerve.lib.interactions.network_menu import ask_to_configure_network
from nerve.lib.interactions.system_conf import (ask_for_bootloader, ask_for_swap, ask_for_uki, select_kernel)
from nerve.lib.locale.locale_menu import LocaleMenu
from nerve.lib.menu.abstract_menu import (CONFIG_KEY, AbstractMenu)
from nerve.lib.mirrors import MirrorMenu
from nerve.lib.models.application import (ApplicationConfiguration, AudioConfiguration, ShellConfiguration)
from nerve.lib.models.authentication import (AuthenticationConfiguration, U2FLoginConfiguration)
from nerve.lib.models.device import (DiskLayoutConfiguration, DiskLayoutType, EncryptionType, FilesystemType, BtrfsOptions, PartitionModification)
from nerve.lib.models.bootloader import Bootloader
from nerve.lib.models.locale import LocaleConfiguration
from nerve.lib.models.mirrors import MirrorConfiguration
from nerve.lib.models.network import (NetworkConfiguration, NicType)
from nerve.lib.models.packages import Repository
from nerve.lib.models.profile import ProfileConfiguration
from nerve.lib.output import FormattedOutput
from nerve.lib.pacman.config import PacmanConfig
from nerve.lib.translationhandler import (Language, translation_handler)

class GlobalMenu(AbstractMenu[None]):
    def __init__(self, config: Config) -> None:
        self._config: Config = config
        menu_options: list[MenuItem] = self._get_menu_options()

        self._item_group: MenuItemGroup = MenuItemGroup(menu_options, sort_items=False, checkmarks=True)
        super().__init__(self._item_group, config=config)

    def _get_menu_options(self) -> list[MenuItem]:
        import sys

        from nerve.lib.utils.system_info import SystemInfo

        return [
            MenuItem(text=tr('Language'), action=self._select_language, display_action=lambda x: x.display_name if x else '', key='language'),
            MenuItem(text=tr('Locales'), action=self._locale_selection, preview_action=self._prev_locale, key='locale_config'),
            MenuItem(text=tr('Mirrors and repositories'), action=self._mirror_configuration, preview_action=self._prev_mirror_config, key='mirror_config'),
            MenuItem(text=tr('Disk configuration'), action=self._select_disk_config, preview_action=self._prev_disk_config, mandatory=True, key='disk_config'),
            MenuItem(text=tr('Swap'), value=True, action=ask_for_swap, preview_action=self._prev_swap, key='swap'),
            MenuItem(text=tr('Bootloader'), value=Bootloader.get_default(), action=self._select_bootloader, preview_action=self._prev_bootloader, mandatory=True, key='bootloader'),
            MenuItem(text=tr('Unified kernel images'), value=False, enabled=SysInfo.has_uefi(), action=ask_for_uki, preview_action=self._prev_uki, key='uki'),
            MenuItem(text=tr('Hostname'), value=SystemInfo().os_id, action=ask_hostname, preview_action=self._prev_hostname, key='hostname'),
            MenuItem(text=tr('Authentication'), action=self._select_authentication, preview_action=self._prev_authentication, key='auth_config'),
            MenuItem(text=tr('Profile'), action=self._select_profile, preview_action=self._prev_profile, key='profile_config'),
            MenuItem(text=tr('Applications'), action=self._select_applications, value=[], preview_action=self._prev_applications, key='app_config'),
            MenuItem(text=tr('Kernels'), value=[__packages__[3]], action=select_kernel, preview_action=self._prev_kernel, mandatory=True, key='kernels'),
            MenuItem(text=tr('Network configuration'), action=ask_to_configure_network, value={}, preview_action=self._prev_network_config, key='network_config'),
            MenuItem(text=tr('Parallel Downloads'), action=add_number_of_parallel_downloads, value=0, preview_action=self._prev_parallel_dw, key='parallel_downloads'),
            MenuItem(text=tr('Additional packages'), action=self._select_additional_packages, value=[], preview_action=self._prev_additional_pkgs, key='packages'),
            MenuItem(text=tr('Timezone'), action=ask_for_a_timezone, value=SystemInfo().timezone, preview_action=self._prev_tz, key='timezone'),
            MenuItem(text=tr('Automatic time sync (NTP)'), action=ask_ntp, value=True, preview_action=self._prev_ntp, key='ntp'),
            MenuItem(text=''),
            MenuItem(text=tr('Save configuration'), action=lambda x: self._safe_config(), key=CONFIG_KEY + '_save'),
            MenuItem(text=tr('Install'), preview_action=self._prev_install_invalid_config, key=CONFIG_KEY + '_install'),
            MenuItem(text=tr('Abort'), action=lambda x: sys.exit(1), key=CONFIG_KEY + '_abort')
        ]

    def _safe_config(self) -> None:
        self.sync_all_to_config()
        save_config(self._config)

    def _missing_configs(self) -> list[str]:
        item: MenuItem = self._item_group.find_by_key('auth_config')
        auth_config: AuthenticationConfiguration | None = item.value

        def check(s: str) -> bool:
            _item: MenuItem = self._item_group.find_by_key(s)
            return _item.has_value()

        def has_superuser() -> bool:
            return any([u.sudo for u in auth_config.users]) if auth_config and auth_config.users else False

        missing: set[str] = set()

        if (not auth_config or not auth_config.root_enc_password) and not has_superuser():
            missing.add(tr('Either root-password or at least 1 user with sudo privileges must be specified'))

        for item in self._item_group.items:
            if item.mandatory:
                assert item.key is not None

                if not check(item.key):
                    missing.add(item.text)

        return list(missing)

    @override
    def _is_config_valid(self) -> bool:
        """
        Checks the validity of the current configuration.
        """
        return not self._missing_configs() and not self._validate_bootloader()

    def _select_language(self, preset: Language) -> Language:
        from nerve.lib.interactions.general_conf import select_language

        language: Language = select_language(translation_handler.translated_languages, preset)
        translation_handler.activate(language)

        self._update_lang_text()
        return language

    @staticmethod
    def _select_applications(preset: ApplicationConfiguration | None) -> ApplicationConfiguration:
        app_config: ApplicationConfiguration = ApplicationMenu(preset).run()
        return app_config

    @staticmethod
    def _select_authentication(preset: AuthenticationConfiguration | None) -> AuthenticationConfiguration:
        auth_config: AuthenticationConfiguration = AuthenticationMenu(preset).run()
        return auth_config

    def _update_lang_text(self) -> None:
        """
        The options for the global menu are generated with a static text;
        each entry of the menu needs to be updated with the new translation
        """
        new_options: list[MenuItem] = self._get_menu_options()

        for o in new_options:
            if o.key is not None:
                self._item_group.find_by_key(o.key).text = o.text

    @staticmethod
    def _locale_selection(preset: LocaleConfiguration) -> LocaleConfiguration:
        locale_config: LocaleConfiguration = LocaleMenu(preset).run()
        return locale_config

    @staticmethod
    def _prev_locale(item: MenuItem) -> str | None:
        if not item.value:
            return None

        config: LocaleConfiguration = item.value
        return config.preview()

    @staticmethod
    def _prev_network_config(item: MenuItem) -> str | None:
        if item.value:
            network_config: NetworkConfiguration = item.value
            output: str = FormattedOutput.as_table(network_config.nics) if network_config.type == NicType.MANUAL else (tr('Network configuration') + ':\n' + network_config.type.display_msg())

            return output

        return None

    @staticmethod
    def _prev_additional_pkgs(item: MenuItem) -> str | None:
        if item.value:
            output: str = '\n'.join(sorted(item.value))
            return output

        return None

    @staticmethod
    def _prev_authentication(item: MenuItem) -> str | None:
        if item.value:
            auth_config: AuthenticationConfiguration = item.value
            output: str = ''

            if auth_config.root_enc_password:
                output += tr("Root password") + ': ' + auth_config.root_enc_password.hidden() + '\n'

            if auth_config.users:
                output += FormattedOutput.as_table(auth_config.users) + '\n'

            if auth_config.u2f_config:
                u2f_config: U2FLoginConfiguration = auth_config.u2f_config

                login_method: str = u2f_config.u2f_login_method.display_value()
                output = tr('U2F login method: ') + login_method

                output += '\n'
                output += tr('Passwordless sudo: ') + (tr('Enabled') if u2f_config.passwordless_sudo else tr('Disabled'))

            return output

        return None

    @staticmethod
    def _prev_applications(item: MenuItem) -> str | None:
        if item.value:
            app_config: ApplicationConfiguration = item.value
            output: str = ''

            if app_config.bluetooth_config:
                output += tr('Bluetooth') + ': '
                output += tr('Enabled') if app_config.bluetooth_config.enabled else tr('Disabled')
                output += '\n'

            if app_config.audio_config:
                audio_config: AudioConfiguration | None = app_config.audio_config

                output += tr('Audio') + ': ' + str(audio_config.audio.value)
                output += '\n'

            if app_config.fonts_config and app_config.fonts_config.selected_fonts:
                output += tr('Fonts') + ': ' + ', '.join(app_config.fonts_config.selected_fonts)
                output += '\n'

            if app_config.shell_config:
                shell_config: ShellConfiguration | None = app_config.shell_config

                output += tr('Shell') + ': ' + str(shell_config.shell.value)
                output += '\n'

            return output

        return None

    @staticmethod
    def _prev_tz(item: MenuItem) -> str | None:
        return (tr('Timezone') + ': ' + str(item.value)) if item.value else None

    @staticmethod
    def _prev_ntp(item: MenuItem) -> str | None:
        if item.value is not None:
            output: str = tr('NTP') + ': '
            output += tr('Enabled') if item.value else tr('Disabled')

            return output

        return None

    @staticmethod
    def _prev_disk_config(item: MenuItem) -> str | None:
        disk_layout_conf: DiskLayoutConfiguration | None = item.value

        if disk_layout_conf:
            output: str = tr('Configuration type: {configuration_type}\n'.format(configuration_type=disk_layout_conf.config_type.display_msg()))

            if disk_layout_conf.config_type == DiskLayoutType.Pre_mount:
                output += tr('Mountpoint') + ': ' + str(disk_layout_conf.mountpoint)

            if disk_layout_conf.lvm_config:
                output += tr('LVM configuration type') + ': ' + disk_layout_conf.lvm_config.config_type.display_msg() + '\n'

            if disk_layout_conf.disk_encryption:
                output += tr('Disk encryption') + ': ' + EncryptionType.type_to_text(disk_layout_conf.disk_encryption.encryption_type) + '\n'

            if disk_layout_conf.btrfs_options:
                btrfs_options: BtrfsOptions = disk_layout_conf.btrfs_options

                if btrfs_options.snapshot_config:
                    output += tr('Btrfs snapshot type: {snapshot_type}').format(snapshot_type=str(btrfs_options.snapshot_config.snapshot_type.value)) + '\n'

            return output

        return None

    @staticmethod
    def _prev_swap(item: MenuItem) -> str | None:
        if item.value is not None:
            output: str = tr("Swap on zram") + ': '
            output += tr('Enabled') if item.value else tr('Disabled')

            return output

        return None

    @staticmethod
    def _prev_uki(item: MenuItem) -> str | None:
        if item.value is not None:
            output: str = tr('Unified kernel images') + ': '
            output += tr('Enabled') if item.value else tr('Disabled')

            return output

        return None

    @staticmethod
    def _prev_hostname(item: MenuItem) -> str | None:
        return (tr('Hostname') + ': ' + str(item.value)) if item.value is not None else None

    @staticmethod
    def _prev_parallel_dw(item: MenuItem) -> str | None:
        return (tr("Parallel Downloads") + ': ' + str(item.value)) if item.value is not None else None

    @staticmethod
    def _prev_kernel(item: MenuItem) -> str | None:
        if item.value:
            kernel: str = ', '.join(item.value)
            return tr('Kernel') + ': ' + kernel

        return None

    @staticmethod
    def _prev_bootloader(item: MenuItem) -> str | None:
        return (tr('Bootloader') + ': ' + str(item.value.value)) if item.value is not None else None

    def _validate_bootloader(self) -> str | None:
        """
        Checks the selected bootloader is valid for the selected filesystem
        type of the boot partition.

        Returns [`None`] if the bootloader is valid, otherwise returns a
        string with the error message.
        """
        bootloader: Bootloader | None = self._item_group.find_by_key('bootloader').value

        if bootloader == Bootloader.NO_BOOTLOADER:
            return None

        disk_config: DiskLayoutConfiguration = self._item_group.find_by_key('disk_config').value

        if not disk_config:
            return "No disk layout selected"

        root_partition: PartitionModification | None = next((d.get_root_partition() for d in disk_config.device_modifications), None)
        boot_partition: PartitionModification | None = next((d.get_boot_partition() for d in disk_config.device_modifications), None)
        efi_partition:  PartitionModification | None = next((d.get_efi_partition()  for d in disk_config.device_modifications), None) if SysInfo.has_uefi() else None

        fat_filesystems: set[FilesystemType] = {
            FilesystemType.Fat12,
            FilesystemType.Fat16,
            FilesystemType.Fat32
        }

        errors: list[tuple[bool, str]] = [
            (not root_partition, "Root partition not found"),
            (not boot_partition, "Boot partition not found"),

            (SysInfo.has_uefi() and (not efi_partition or efi_partition.fs_type not in fat_filesystems), "ESP must be formatted as a FAT filesystem"),
            ((bootloader == Bootloader.Limine) and boot_partition.fs_type not in fat_filesystems, "Limine requires a FAT boot partition")
        ]

        return next((msg for (condition, msg) in errors if condition), None)

    def _prev_install_invalid_config(self, _: MenuItem) -> str | None:
        missing: list[str] = self._missing_configs()

        if missing:
            return tr('Missing configurations:\n') + ''.join(['- ' + m + '\n' for m in missing])[:-1]

        error: str | None = self._validate_bootloader()
        return tr("Invalid configuration: {error}".format(error=error)) if error else None

    @staticmethod
    def _prev_profile(item: MenuItem) -> str | None:
        profile_config: ProfileConfiguration | None = item.value

        if profile_config and profile_config.profile:
            output: str = tr('Profiles') + ': '
            output += ', '.join(profile_names) + '\n' if (profile_names := profile_config.profile.current_selection_names()) else profile_config.profile.name + '\n'

            if profile_config.gfx_driver:
                output += tr('Graphics driver') + ': ' + str(profile_config.gfx_driver.value) + '\n'

            if profile_config.greeter:
                output += tr('Greeter') + ': ' + str(profile_config.greeter.value) + '\n'

            return output

        return None

    @staticmethod
    def _select_disk_config(preset: DiskLayoutConfiguration | None = None) -> DiskLayoutConfiguration | None:
        disk_config: DiskLayoutConfiguration | None = DiskLayoutConfigurationMenu(preset).run()
        return disk_config

    def _select_bootloader(self, preset: Bootloader | None) -> Bootloader:
        bootloader: Bootloader | None = ask_for_bootloader(preset)

        if bootloader:
            uki: MenuItem = self._item_group.find_by_key('uki')
            (uki.value, uki.enabled) = (False, False) if not SysInfo.has_uefi() or not bootloader.has_uki_support() else (uki.value, True)

        return bootloader

    @staticmethod
    def _select_profile(current_profile: ProfileConfiguration | None) -> ProfileConfiguration | None:
        from nerve.lib.profile.profile_menu import ProfileMenu
        profile_config: ProfileConfiguration | None = ProfileMenu(preset=current_profile).run()

        return profile_config

    def _select_additional_packages(self, preset: list[str]) -> list[str]:
        config: MirrorConfiguration | None = self._item_group.find_by_key('mirror_config').value
        repositories: set[Repository] = set()

        if config:
            repositories = set(config.optional_repositories)

        packages: list[str] = ask_additional_packages_to_install(preset, repositories=repositories)
        return packages

    @staticmethod
    def _mirror_configuration(preset: MirrorConfiguration | None = None) -> MirrorConfiguration:
        mirror_configuration: MirrorConfiguration = MirrorMenu(preset=preset).run()

        if mirror_configuration.optional_repositories:
            # reset the package list cache in case the repository selection has changed
            list_available_packages.cache_clear()

            # enable the repositories in the config
            pacman_config: PacmanConfig = PacmanConfig(None)
            pacman_config.enable(mirror_configuration.optional_repositories)
            pacman_config.apply()

        return mirror_configuration

    @staticmethod
    def _prev_mirror_config(item: MenuItem) -> str | None:
        if not item.value:
            return None

        mirror_config: MirrorConfiguration = item.value
        output: str = ''

        if mirror_config.mirror_regions:
            title:   str = tr('Selected mirror regions')
            divider: str = '-' * len(title)
            regions: str = mirror_config.region_names

            output += title + '\n' + divider + '\n' + regions + '\n\n'

        if mirror_config.custom_servers:
            title:   str = tr('Custom servers')
            divider: str = '-' * len(title)
            servers: str = mirror_config.custom_server_urls

            output += title + '\n' + divider + '\n' + servers + '\n\n'

        if mirror_config.optional_repositories:
            title:   str = tr('Optional repositories')
            divider: str = '-' * len(title)
            repos:   str = ', '.join([r.value for r in mirror_config.optional_repositories])

            output += title + '\n' + divider + '\n' + repos + '\n\n'

        if mirror_config.custom_repositories:
            title: str = tr('Custom repositories')
            table: str = FormattedOutput.as_table(mirror_config.custom_repositories)

            output += title + ':\n\n' + table

        return output.strip()
