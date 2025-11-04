# SPDX-FileCopyrightText: 2024 Daniel Biehl <daniel.biehl@imbus.de>
#
# SPDX-License-Identifier: Apache-2.0

from abc import abstractmethod

from ...core import StrategyBase

__all__ = ["Restorable"]


class Restorable(StrategyBase):
    strategy_name = "org.platynui.strategies.Restorable"

    @abstractmethod
    def restore(self) -> None:
        pass
