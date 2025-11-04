# SPDX-FileCopyrightText: 2024 Daniel Biehl <daniel.biehl@imbus.de>
#
# SPDX-License-Identifier: Apache-2.0

from typing import Optional

from robotlibcore import keyword

from ..core.types import Point
from ..ui.core.devices.mousebutton import MouseButton
from ..ui.locator import Locator
from ..ui.strategies import HasMouse
from .assertable import assertable
from .types import ElementDescriptor

__all__ = ["Mouse"]

desktop_descriptor: ElementDescriptor[HasMouse] = ElementDescriptor(Locator(path="/."))


class Mouse:
    @keyword
    def mouse_click(
        self,
        descriptor: ElementDescriptor[HasMouse] | None = None,
        x: float | None = None,
        y: float | None = None,
        button: Optional[MouseButton] = None,
        times: int = 1,
    ) -> Point:
        descriptor = descriptor or desktop_descriptor
        descriptor().mouse.click(x=x, y=y, button=button, times=times)
        return self.mouse_position()

    @keyword
    def mouse_double_click(
        self,
        descriptor: ElementDescriptor[HasMouse] | None = None,
        x: float | None = None,
        y: float | None = None,
        button: Optional[MouseButton] = None,
    ) -> None:
        descriptor = descriptor or desktop_descriptor
        descriptor().mouse.double_click(x=x, y=y, button=button)
        return self.mouse_position()

    @keyword
    def mouse_move_to(
        self,
        descriptor: ElementDescriptor[HasMouse] | None = None,
        x: float | None = None,
        y: float | None = None,
    ) -> None:
        descriptor = descriptor or desktop_descriptor
        descriptor().mouse.move_to(x=x, y=y)
        return self.mouse_position()

    @keyword
    def mouse_press(
        self,
        descriptor: ElementDescriptor[HasMouse] | None = None,
        x: float | None = None,
        y: float | None = None,
        button: Optional[MouseButton] = None,
    ) -> None:
        descriptor = descriptor or desktop_descriptor
        descriptor().mouse.press(x=x, y=y, button=button)
        return self.mouse_position()

    @keyword
    def mouse_release(
        self,
        descriptor: ElementDescriptor[HasMouse] | None = None,
        x: float | None = None,
        y: float | None = None,
        button: Optional[MouseButton] = None,
    ) -> None:
        descriptor = descriptor or desktop_descriptor
        descriptor().mouse.release(x=x, y=y, button=button)
        return self.mouse_position()

    @keyword
    @assertable
    def mouse_position(self) -> Point:
        return desktop_descriptor().mouse.mouse_device.get_position()
