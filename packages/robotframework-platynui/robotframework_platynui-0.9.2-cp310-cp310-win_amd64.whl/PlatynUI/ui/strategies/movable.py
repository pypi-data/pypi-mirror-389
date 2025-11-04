# SPDX-FileCopyrightText: 2024 Daniel Biehl <daniel.biehl@imbus.de>
#
# SPDX-License-Identifier: Apache-2.0

from abc import abstractmethod

from ...core import StrategyBase
from ...core.types import Point

__all__ = ["Movable"]


class Movable(StrategyBase):
    strategy_name = "org.platynui.strategies.Movable"

    @abstractmethod
    def move(self, point: Point) -> None:
        pass
