# SPDX-FileCopyrightText: 2024 Daniel Biehl <daniel.biehl@imbus.de>
#
# SPDX-License-Identifier: Apache-2.0

from enum import Enum, auto
from typing import Union

from robotlibcore import keyword

from ..core.strategies import Properties
from .assertable import assertable
from .types import ElementDescriptor


class PropertyName(Enum):
    BoundingRectangle = auto()
    Enabled = auto()
    Visible = auto()


class Properties:
    @keyword
    @assertable
    def get_property_value(self, descriptor: ElementDescriptor[Properties], name: Union[PropertyName, str]) -> any:
        return descriptor().get_property_value(name)

    @keyword
    @assertable
    def get_property_names(self, descriptor: ElementDescriptor[Properties]) -> list[str]:
        return descriptor().get_property_names()
