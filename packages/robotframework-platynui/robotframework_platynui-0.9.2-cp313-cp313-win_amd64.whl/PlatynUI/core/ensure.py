import threading
import time
from typing import Any, Callable, List, Optional, Protocol, runtime_checkable

from .exceptions import CannotEnsureError, PlatynUiFatalError
from .settings import Settings


@runtime_checkable
class HasFullRepr(Protocol):
    def full_repr(self) -> str: ...


def full_repr(obj: Any) -> str:
    try:
        if isinstance(obj, HasFullRepr):
            return obj.full_repr()
    except Exception:
        pass
    return repr(obj)


class _EnsureLocal(threading.local):
    def __init__(self) -> None:
        self.ensure_that_start_time: Optional[float] = None
        self.ensure_that_raise_exception: Optional[bool] = None
        self.in_ensure_that: int = 0
        self.succeeded_predicates: List[Callable[..., Any]] = []
        self.ensure_timeout: Optional[float] = None


class Ensure:
    __thread_local = _EnsureLocal()

    __ensure_that_hooks: List[Callable[[Any], None]] = []

    @classmethod
    def add_ensure_hook(cls, hook: Callable[[Any], None]) -> None:
        cls.__ensure_that_hooks.append(hook)

    @classmethod
    def __exec_ensure_that_hooks(cls, the_context: Any) -> None:
        for hook in cls.__ensure_that_hooks:
            hook(the_context)

    @classmethod
    def that(
        cls,
        context: Any,
        *predicates: Optional[Callable[[], bool]],
        timeout: Optional[float] = None,
        raise_exception: Optional[bool] = None,
        failed_func: Optional[Callable[[], None]] = None,
    ) -> bool:
        if timeout is None:
            timeout = Settings.current().ensure_timeout

        cls.__thread_local.in_ensure_that += 1
        try:
            if cls.__thread_local.in_ensure_that == 1:
                cls.__thread_local.succeeded_predicates = []
                cls.__thread_local.ensure_that_raise_exception = raise_exception
                cls.__thread_local.ensure_timeout = timeout
            else:
                raise_exception = cls.__thread_local.ensure_that_raise_exception

            if raise_exception is None:
                raise_exception = True

            result = False
            set_start_time = False
            if cls.__thread_local.ensure_that_start_time is None:
                cls.__thread_local.ensure_that_start_time = time.time()
                set_start_time = True

            last_exception = None
            last_predicate = None

            try:
                while not result:
                    for p in predicates:
                        # skip empty predicates
                        if p is None:
                            continue

                        if not callable(p):
                            raise PlatynUiFatalError("%s is not callable " % p)

                        if p in cls.__thread_local.succeeded_predicates:
                            result = True
                            continue

                        last_predicate = p
                        try:
                            cls.__exec_ensure_that_hooks(context)

                            result = p()

                            if not result:
                                cls.__thread_local.succeeded_predicates.clear()
                                break

                            cls.__thread_local.succeeded_predicates.append(p)

                        except (PlatynUiFatalError, KeyboardInterrupt, SystemExit):
                            raise
                        except BaseException as e:
                            last_exception = e
                            result = False
                            break

                    if result:
                        break

                    thread_ensure_that_start_time = cls.__thread_local.ensure_that_start_time
                    thread_local_ensure_timeout = cls.__thread_local.ensure_timeout

                    if thread_local_ensure_timeout is None or thread_ensure_that_start_time is None:
                        raise PlatynUiFatalError

                    if time.time() - thread_ensure_that_start_time > thread_local_ensure_timeout:
                        break

                    if not result:
                        time.sleep(Settings.current().ensure_delay)

                        if failed_func is not None:
                            failed_func()

            finally:
                if set_start_time:
                    cls.__thread_local.ensure_that_start_time = None

            if not result and raise_exception:
                raise CannotEnsureError(
                    "Cannot ensure that %s%s"
                    % (
                        (
                            "%s" % last_predicate.message.format(full_repr(context))
                            if last_predicate is not None and hasattr(last_predicate, "message")
                            else "%s for %s" % (last_predicate, context)
                        ),
                        (
                            ",\n   because %s"
                            % (last_exception if str(last_exception).strip() != "" else repr(last_exception))
                            if last_exception is not None
                            else ""
                        ),
                    )
                ) from last_exception

            return result
        finally:
            cls.__thread_local.in_ensure_that -= 1
            assert cls.__thread_local.in_ensure_that >= 0
