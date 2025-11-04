# SPDX-FileCopyrightText: 2024 Daniel Biehl <daniel.biehl@imbus.de>
#
# SPDX-License-Identifier: Apache-2.0

from abc import abstractmethod

from ...core import StrategyBase

__all__ = ["HasNativeWindowHandle"]


class HasNativeWindowHandle(StrategyBase):
    strategy_name = "org.platynui.strategies.HasNativeWindowHandle"

    @property
    @abstractmethod
    def native_window_handle(self) -> bytes:
        pass
