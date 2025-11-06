# SPDX-FileCopyrightText: 2023 CELESTIFYX Team
# SPDX-License-Identifier: GPL-3.0-or-later

# Any package that the Installer() is responsible for (optional and the default ones)
__packages__: list[str] = [
    "base",
    "base-devel",
    "linux-firmware",

    "linux",
    "linux-lts",
    "linux-zen",
    "linux-hardened"
]

# Additional packages that are installed if the user is running the Live ISO with accessibility tools enabled
__accessibility_packages__: list[str] = [
    "brltty",
    "espeakup",
    "alsa-utils"
]
