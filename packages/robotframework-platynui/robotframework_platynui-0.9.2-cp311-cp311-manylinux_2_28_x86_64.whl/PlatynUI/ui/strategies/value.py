# SPDX-FileCopyrightText: 2024 Daniel Biehl <daniel.biehl@imbus.de>
#
# SPDX-License-Identifier: Apache-2.0

from abc import abstractmethod
from typing import Any

from ...core import StrategyBase

__all__ = ["Value"]


class Value(StrategyBase):
    strategy_name = "org.platynui.strategies.Value"

    @property
    @abstractmethod
    def value(self) -> Any:
        pass
