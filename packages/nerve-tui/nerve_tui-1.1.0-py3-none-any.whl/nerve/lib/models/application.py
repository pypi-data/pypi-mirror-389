# SPDX-FileCopyrightText: 2023 CELESTIFYX Team
# SPDX-License-Identifier: GPL-3.0-or-later

from dataclasses import dataclass
from enum import (StrEnum, auto)
from typing import (Any, NotRequired, TypedDict)

class Audio(StrEnum):
	NO_AUDIO = 'No audio server'
	PIPEWIRE = auto()
	PULSEAUDIO = auto()

class Fonts(StrEnum):
	NOTO           = 'Noto Fonts'
	JETBRAINS_MONO = 'JetBrains Mono'
	LIBERATION     = 'Liberation'
	DEJAVU         = 'Dejavu'
	FIRA           = 'Fira'
	ADOBE_SOURCE   = 'Adobe Source Sans'
	UBUNTU_FAMILY  = 'Ubuntu Family'
	UBUNTU_NERD    = 'Ubuntu Nerd'
	IOSEVKA_NERD   = 'Iosevka Nerd'
	HACK           = 'Hack'
	HACK_NERD      = 'Hack Nerd'

class Shell(StrEnum):
	BASH    = 'GNU Bourne Again Shell (bash)'
	DASH    = 'Debian Almquist Shell (dash)'
	FISH    = 'Friendly Interactive Shell (fish)'
	ZSH     = 'Z Shell (zsh)'
	NUSHELL = 'Nu Shell (nushell)'
	TCSH    = 'TENEX C Shell (tcsh)'
	KSH     = 'Korn Shell (ksh)'
	XONSH   = 'Python-powered Shell (xonsh)'
	ELVISH  = 'Elvish Shell (elvish)'

class AudioConfigSerialization(TypedDict):
	audio: str

class BluetoothConfigSerialization(TypedDict):
	enabled: bool

class FontsConfigSerialization(TypedDict):
	selected_fonts: list[str]

class ShellConfigSerialization(TypedDict):
	shell: str

class ApplicationSerialization(TypedDict):
	bluetooth_config: NotRequired[BluetoothConfigSerialization]
	audio_config:     NotRequired[AudioConfigSerialization]
	fonts_config:     NotRequired[FontsConfigSerialization]
	shell_config:     NotRequired[ShellConfigSerialization]

@dataclass
class AudioConfiguration:
	audio: Audio

	def json(self) -> AudioConfigSerialization:
		return {'audio': str(self.audio.value)}

	@staticmethod
	def parse_arg(arg: dict[str, Any]) -> 'AudioConfiguration':
		return AudioConfiguration(Audio(arg['audio']))

@dataclass
class BluetoothConfiguration:
	enabled: bool

	def json(self) -> BluetoothConfigSerialization:
		return {'enabled': self.enabled}

	@staticmethod
	def parse_arg(arg: dict[str, Any]) -> 'BluetoothConfiguration':
		return BluetoothConfiguration(arg['enabled'])

@dataclass
class FontsConfiguration:
	selected_fonts: list[str]

	def json(self) -> FontsConfigSerialization:
		return {'selected_fonts': self.selected_fonts}

	@staticmethod
	def parse_arg(arg: dict[str, Any]) -> 'FontsConfiguration':
		return FontsConfiguration(arg.get('selected_fonts', []))

@dataclass
class ShellConfiguration:
	shell: Shell

	def json(self) -> ShellConfigSerialization:
		return {'shell': str(self.shell)}

	@staticmethod
	def parse_arg(arg: dict[str, Any]) -> 'ShellConfiguration':
		return ShellConfiguration(arg.get('shell'))

@dataclass
class ApplicationConfiguration:
	bluetooth_config: BluetoothConfiguration | None = None
	audio_config: AudioConfiguration | None = None
	fonts_config: FontsConfiguration | None = None
	shell_config: ShellConfiguration | None = None

	@staticmethod
	def parse_arg(args: dict[str, Any] | None = None) -> 'ApplicationConfiguration':
		app_config: ApplicationConfiguration = ApplicationConfiguration()

		if args and (bluetooth_config := args.get('bluetooth_config')) is not None:
			app_config.bluetooth_config = BluetoothConfiguration.parse_arg(bluetooth_config)

		if args and (audio_config := args.get('audio_config')) is not None:
			app_config.audio_config = AudioConfiguration.parse_arg(audio_config)

		if args and (fonts_config := args.get('fonts_config')) is not None:
			app_config.fonts_config = FontsConfiguration.parse_arg(fonts_config)

		if args and (shell_config := args.get('shell_config')) is not None:
			app_config.shell_config = ShellConfiguration.parse_arg(shell_config)

		return app_config

	def json(self) -> ApplicationSerialization:
		config: ApplicationSerialization = {}

		if self.bluetooth_config:
			config['bluetooth_config'] = self.bluetooth_config.json()

		if self.audio_config:
			config['audio_config'] = self.audio_config.json()

		if self.fonts_config:
			config['fonts_config'] = self.fonts_config.json()

		if self.shell_config:
			config['shell_config'] = self.shell_config.json()

		return config
