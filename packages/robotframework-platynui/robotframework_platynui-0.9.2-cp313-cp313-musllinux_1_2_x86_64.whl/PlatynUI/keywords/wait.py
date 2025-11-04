# SPDX-FileCopyrightText: 2024 Daniel Biehl <daniel.biehl@imbus.de>
#
# SPDX-License-Identifier: Apache-2.0

from datetime import timedelta
from typing import Optional

from robotlibcore import keyword

from .types import ElementDescriptor

__all__ = ["Wait"]


class Wait:
    @keyword
    def ensure_exists(
        self, descriptor: ElementDescriptor, timeout: Optional[timedelta] = None, raise_exception: bool = True
    ) -> bool:
        return descriptor(False).exists(
            timeout=None if timeout is None else timeout.total_seconds(), raise_exception=raise_exception
        )
