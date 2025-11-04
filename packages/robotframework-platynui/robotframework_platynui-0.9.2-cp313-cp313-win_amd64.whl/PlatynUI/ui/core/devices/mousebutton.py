# SPDX-FileCopyrightText: 2024 Daniel Biehl <daniel.biehl@imbus.de>
#
# SPDX-License-Identifier: Apache-2.0

from enum import IntEnum

__all__ = ["MouseButton"]


class MouseButton(IntEnum):
    left = 0
    middle = 1
    right = 2
    x1 = 3
    x2 = 4
