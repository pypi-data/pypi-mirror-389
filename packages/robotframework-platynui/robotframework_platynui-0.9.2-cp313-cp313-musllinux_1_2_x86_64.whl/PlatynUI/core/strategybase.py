# SPDX-FileCopyrightText: 2024 Daniel Biehl <daniel.biehl@imbus.de>
#
# SPDX-License-Identifier: Apache-2.0

from abc import ABC
from typing import ClassVar, Optional

__all__ = ["StrategyBase"]


class StrategyBase(ABC):
    strategy_name: ClassVar[Optional[str]] = None
