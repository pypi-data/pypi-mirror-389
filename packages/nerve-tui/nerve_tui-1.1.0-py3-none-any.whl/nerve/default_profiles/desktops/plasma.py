# SPDX-FileCopyrightText: 2023 CELESTIFYX Team
# SPDX-License-Identifier: GPL-3.0-or-later

from typing import override

from nerve.default_profiles.profile import (GreeterType, ProfileType)
from nerve.default_profiles.xorg import XorgProfile

class PlasmaProfile(XorgProfile):
    def __init__(self) -> None:
        super().__init__(name='KDE Plasma', profile_type=ProfileType.DesktopEnv)

    @property
    @override
    def packages(self) -> list[str]:
        from nerve.lib.args import config_handler

        return [
            'plasma-meta',
            'konsole',
            'kate',
            'dolphin',
            'ark',
            'plasma-workspace'
        ] if not config_handler.args.minimal_packages else [
            'bluedevil',
            'breeze',
            'breeze-gtk',
            'drkonqi',
            'kactivitymanagerd',
            'kde-cli-tools',
            'kde-gtk-config',
            'kdecoration',
            'kgamma',
            'kglobalacceld',
            'kinfocenter',
            'kpipewire',
            'kscreen',
            'kscreenlocker',
            'ksshaskpass',
            'ksystemstats',
            'kwallet-pam',
            'kwayland',
            'kwin',
            'kwrited',
            'layer-shell-qt',
            'libkscreen',
            'libksysguard',
            'libplasma',
            'milou',
            'ocean-sound-theme',
            'plasma-activities',
            'plasma-activities-stats',
            'plasma-browser-integration',
            'plasma-desktop',
            'plasma-disks',
            'plasma-firewall',
            'plasma-integration',
            'plasma-nm',
            'plasma-pa',
            'plasma-systemmonitor',
            'plasma-thunderbolt',
            'plasma-vault',
            'plasma-workspace',
            'plasma5support',
            'polkit-kde-agent',
            'powerdevil',
            'qqc2-breeze-style',
            'systemsettings',
            'dolphin',
            'konsole',
            'ark',
            'gwenview',
            'spectacle',
            'fwupd',
            'power-profiles-daemon',
            'sddm-kcm'
        ]

    @property
    @override
    def default_greeter_type(self) -> GreeterType:
        return GreeterType.Sddm
