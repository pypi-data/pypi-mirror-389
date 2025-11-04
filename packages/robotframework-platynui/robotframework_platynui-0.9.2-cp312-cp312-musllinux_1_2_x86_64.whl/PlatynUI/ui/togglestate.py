# SPDX-FileCopyrightText: 2024 Daniel Biehl <daniel.biehl@imbus.de>
#
# SPDX-License-Identifier: Apache-2.0

from enum import IntEnum

__all__ = ["ToggleState"]


class ToggleState(IntEnum):
    Off = 0
    Indeterminate = 1
    On = 2

    Unchecked = Off
    Checked = On
