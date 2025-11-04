# SPDX-FileCopyrightText: 2024 Daniel Biehl <daniel.biehl@imbus.de>
#
# SPDX-License-Identifier: Apache-2.0

import threading
from functools import cached_property
from typing import Optional

from ...core import adapterfactory
from ..core import ui_technology
from ..core.devices import (
    DefaultDisplayDevice,
    DefaultKeyboardDevice,
    DefaultMouseDevice,
    DisplayDevice,
    KeyboardDevice,
    MouseDevice,
)
from ..core.window_manager import WindowManager

__all__ = ["get_technology"]


class TechnologyImpl(ui_technology.UiTechnology):
    @cached_property
    def adapter_factory(self) -> adapterfactory.AdapterFactory:
        from .adapterfactory_impl import AdapterFactoryImpl

        return AdapterFactoryImpl(self)

    @cached_property
    def mouse_device(self) -> MouseDevice:
        from .mouse_device_impl import MouseDeviceImpl

        return DefaultMouseDevice(MouseDeviceImpl())

    @cached_property
    def keyboard_device(self) -> KeyboardDevice:
        from .keyboard_device_impl import KeyboardDeviceImpl

        return DefaultKeyboardDevice(KeyboardDeviceImpl())

    @cached_property
    def display_device(self) -> DisplayDevice:
        from .display_device_impl import DisplayDeviceImpl

        return DefaultDisplayDevice(DisplayDeviceImpl())

    @cached_property
    def window_manager(self) -> WindowManager:
        raise NotImplementedError


__instance: Optional[TechnologyImpl] = None
__lock = threading.Lock()


def get_technology() -> TechnologyImpl:
    global __instance
    with __lock:
        if __instance is None:
            __instance = TechnologyImpl()
        return __instance
