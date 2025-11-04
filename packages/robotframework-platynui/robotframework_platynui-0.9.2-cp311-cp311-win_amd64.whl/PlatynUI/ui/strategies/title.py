# SPDX-FileCopyrightText: 2024 Daniel Biehl <daniel.biehl@imbus.de>
#
# SPDX-License-Identifier: Apache-2.0

from abc import abstractmethod

from ...core import StrategyBase

__all__ = ["Title"]


class Title(StrategyBase):
    strategy_name = "org.platynui.strategies.Title"

    @property
    @abstractmethod
    def title(self) -> str:
        pass
