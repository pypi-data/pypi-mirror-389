# SPDX-FileCopyrightText: 2024 Daniel Biehl <daniel.biehl@imbus.de>
#
# SPDX-License-Identifier: Apache-2.0

from ..core import context
from .element import *

__all__ = ["Graphic"]


@context
class Graphic(Element):
    pass


@context
class GraphicItem(Element):
    default_prefix = "item"
