# SPDX-FileCopyrightText: 2024 Daniel Biehl <daniel.biehl@imbus.de>
#
# SPDX-License-Identifier: Apache-2.0

from ...core import context
from ...ui.desktopbase import DesktopBase
from .locator import locator

__all__ = ["Desktop"]


@locator(path="/.")
@context
class Desktop(DesktopBase):
    pass
