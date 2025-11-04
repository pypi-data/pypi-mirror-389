# SPDX-FileCopyrightText: 2024 Daniel Biehl <daniel.biehl@imbus.de>
#
# SPDX-License-Identifier: Apache-2.0

from ..core import context
from .window import *

__all__ = ["Dialog"]


@context
class Dialog(Window):
    # TODO: modal state and so on
    pass
