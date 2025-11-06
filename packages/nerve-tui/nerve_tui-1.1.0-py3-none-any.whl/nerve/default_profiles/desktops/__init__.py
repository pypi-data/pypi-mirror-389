# SPDX-FileCopyrightText: 2023 CELESTIFYX Team
# SPDX-License-Identifier: GPL-3.0-or-later

from enum import Enum

class SeatAccess(Enum):
    seatd  = 'seatd'
    polkit = 'polkit'
