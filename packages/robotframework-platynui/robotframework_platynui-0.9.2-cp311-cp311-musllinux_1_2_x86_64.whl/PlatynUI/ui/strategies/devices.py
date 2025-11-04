# SPDX-FileCopyrightText: 2024 Daniel Biehl <daniel.biehl@imbus.de>
#
# SPDX-License-Identifier: Apache-2.0

from abc import abstractmethod

from ...core import StrategyBase
from ..core.devices.keyboardproxy import KeyboardProxy
from ..core.devices.mouseproxy import MouseProxy

__all__ = ["HasKeyboard", "HasMouse"]


class HasMouse(StrategyBase):
    strategy_name = "org.platynui.strategies.HasMouse"

    @property
    @abstractmethod
    def mouse(self) -> MouseProxy: ...


class HasKeyboard(StrategyBase):
    strategy_name = "org.platynui.strategies.HasKeyboard"

    @property
    @abstractmethod
    def keyboard(self) -> KeyboardProxy: ...
