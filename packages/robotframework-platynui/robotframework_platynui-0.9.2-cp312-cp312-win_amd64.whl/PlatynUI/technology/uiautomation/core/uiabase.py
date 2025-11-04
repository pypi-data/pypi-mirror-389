# SPDX-FileCopyrightText: 2024 Daniel Biehl <daniel.biehl@imbus.de>
#
# SPDX-License-Identifier: Apache-2.0

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from PlatynUI.Extension.Win32.UiAutomation.Client import IUIAutomationElement  # type: ignore

from PlatynUI.core.technology import Technology


class UiaBase(Protocol):
    @property
    def element(self) -> "IUIAutomationElement": ...

    @property
    def valid(self) -> bool: ...

    def invalidate(self) -> None: ...

    @property
    def technology(self) -> Technology: ...
