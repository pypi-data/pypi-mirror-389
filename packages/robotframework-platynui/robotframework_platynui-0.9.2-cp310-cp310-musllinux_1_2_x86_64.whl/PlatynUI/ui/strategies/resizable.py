# SPDX-FileCopyrightText: 2024 Daniel Biehl <daniel.biehl@imbus.de>
#
# SPDX-License-Identifier: Apache-2.0

from abc import abstractmethod

from ...core import StrategyBase
from ...core.types import Size

__all__ = ["Resizable"]


class Resizable(StrategyBase):
    strategy_name = "org.platynui.strategies.Resizable"

    @abstractmethod
    def resize(self, size: Size) -> None: ...
