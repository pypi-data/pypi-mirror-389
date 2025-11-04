# SPDX-FileCopyrightText: 2024 Daniel Biehl <daniel.biehl@imbus.de>
#
# SPDX-License-Identifier: Apache-2.0

from ..core import context
from . import Control, strategies

__all__ = ["Label", "StaticText"]


@context
class Label(Control, strategies.Text):
    @property
    def text(self) -> str:
        self.ensure_that(self._application_is_ready)

        return self.adapter.get_strategy(strategies.Text).text


@context
class StaticText(Label):
    pass
