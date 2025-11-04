# SPDX-FileCopyrightText: 2024 Daniel Biehl <daniel.biehl@imbus.de>
#
# SPDX-License-Identifier: Apache-2.0

from ..core import context
from . import Control

__all__ = ["Unknown"]


@context
class Unknown(Control):
    pass
