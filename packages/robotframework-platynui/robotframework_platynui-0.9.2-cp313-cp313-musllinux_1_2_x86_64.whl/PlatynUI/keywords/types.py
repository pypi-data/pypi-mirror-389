# SPDX-FileCopyrightText: 2024 Daniel Biehl <daniel.biehl@imbus.de>
#
# SPDX-License-Identifier: Apache-2.0

from typing import Any, Generic, Optional, Type, Union, cast

from robot.running.context import EXECUTION_CONTEXTS
from robot.utils import secs_to_timestr
from typing_extensions import TypeVar

from ..core.contextbase import ContextBase, ContextFactory, TContextBase
from ..core.locatorbase import LocatorBase
from ..ui import Locator

T = TypeVar("T", default=ContextBase)

ROOT_ELEMENT_VAR = "PLATYNUI_ROOT_ELEMENT"


class ElementDescriptor(Generic[T]):
    """Descriptor for elements in the UI.

    This descriptor is used to access elements in the UI.
    A descriptor can be created by providing a locator or an already existing context.
    """

    def __init__(
        self,
        locator: Optional[LocatorBase] = None,
        context_type: Optional[Type[TContextBase]] = None,
        parent: Optional["ElementDescriptor"] = None,
        context: Optional[ContextBase] = None,
    ) -> None:
        self.__locator = locator
        self.__context_type = context_type
        self.__parent = parent
        self.__context = context
        self.__has_full_context = context is not None

    def __repr__(self) -> str:
        return f"<Proxy for {self.__context if self.__context is not None else self.__locator!r}>"

    def __call__(self, full_context: bool = True) -> T:
        return self.context(full_context)

    def context(self, full_context: bool = True) -> T:
        if self.__context is None:
            self.__context = ContextBase(self.__locator, self.__parent() if self.__parent else None)

        if full_context and self.__context is not None and not self.__has_full_context:
            adapter = self.__context.get_adapter()

            if adapter is not None:
                context_type = ContextFactory.find_context_class_for(adapter, self.__context_type)
                self.__has_full_context = True

                self.__context = context_type(
                    self.__locator,
                    context_parent=self.__context.context_parent,
                    adapter=adapter,
                )

        return cast(T, self.__context)

    @staticmethod
    def convert(value: Union[str, ContextBase]) -> "ElementDescriptor[T]":
        if isinstance(value, ContextBase):
            return ElementDescriptor(context=value)
        return ElementDescriptor(Locator(path=value), parent=ElementDescriptor.get_root_element())

    @staticmethod
    def set_root_element(element: "ElementDescriptor[Any]") -> "ElementDescriptor[Any]":
        old = ElementDescriptor.get_root_element()

        EXECUTION_CONTEXTS.current.variables[f"${{{ROOT_ELEMENT_VAR}}}"] = element

        return old

    @staticmethod
    def get_root_element() -> "ElementDescriptor[Any]":
        return cast(
            ElementDescriptor[Any],
            (
                EXECUTION_CONTEXTS.current.variables[f"${{{ROOT_ELEMENT_VAR}}}"]
                if ROOT_ELEMENT_VAR in EXECUTION_CONTEXTS.current.variables
                else None
            ),
        )


class RootElementDescriptor(ElementDescriptor[T]):
    @staticmethod
    def convert(value: Union[str, ContextBase]) -> "ElementDescriptor[T]":
        if isinstance(value, ContextBase):
            return ElementDescriptor(context=value)
        return RootElementDescriptor(Locator(path=value))


class TimeSpan:
    def __init__(self, seconds: float) -> None:
        self.seconds = seconds

    def __str__(self) -> str:
        return str(secs_to_timestr(self.seconds))
