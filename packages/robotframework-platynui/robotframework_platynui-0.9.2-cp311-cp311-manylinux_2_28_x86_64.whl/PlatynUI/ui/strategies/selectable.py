# SPDX-FileCopyrightText: 2024 Daniel Biehl <daniel.biehl@imbus.de>
#
# SPDX-License-Identifier: Apache-2.0

from abc import abstractmethod

from ...core import StrategyBase

__all__ = ["HasSelected", "Selectable"]


class HasSelected(StrategyBase):
    strategy_name = "org.platynui.strategies.HasSelected"

    @property
    @abstractmethod
    def is_selectable(self) -> bool:
        pass

    @property
    @abstractmethod
    def is_selected(self) -> bool:
        pass


class Selectable(HasSelected):
    strategy_name = "org.platynui.strategies.Selectable"

    @abstractmethod
    def select(self) -> None:
        pass
