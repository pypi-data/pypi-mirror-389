# SPDX-FileCopyrightText: 2024 Daniel Biehl <daniel.biehl@imbus.de>
#
# SPDX-License-Identifier: Apache-2.0

from abc import abstractmethod

from ...core import StrategyBase

__all__ = ["Clearable", "EditableText", "HasEditor", "HasMultiLine", "Text"]


class Text(StrategyBase):
    strategy_name = "org.platynui.strategies.Text"

    @property
    @abstractmethod
    def text(self) -> str:
        pass


class Clearable(StrategyBase):
    strategy_name = "org.platynui.strategies.Clearable"

    @abstractmethod
    def clear(self) -> None:
        pass


class EditableText(StrategyBase):
    strategy_name = "org.platynui.strategies.EditableText"

    @abstractmethod
    def set_text(self, value: str) -> None:
        pass


class HasEditor(StrategyBase):
    strategy_name = "org.platynui.strategies.HasEditor"

    @abstractmethod
    def open_editor(self) -> None:
        pass

    @abstractmethod
    def cancel(self) -> None:
        pass

    @abstractmethod
    def accept(self) -> None:
        pass


class HasMultiLine(StrategyBase):
    strategy_name = "org.platynui.strategies.HasMultiLine"

    @property
    @abstractmethod
    def is_multi_line(self) -> bool:
        pass
