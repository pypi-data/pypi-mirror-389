# SPDX-FileCopyrightText: 2024 Daniel Biehl <daniel.biehl@imbus.de>
#
# SPDX-License-Identifier: Apache-2.0

from enum import IntEnum

__all__ = ["Orientation"]


class Orientation(IntEnum):
    NoOrientation = 0
    Horizontal = 1
    Vertical = 2
