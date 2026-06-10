import os
import signal
from collections.abc import Callable

_handlers: list[Callable[[], None]] = []


def register_shutdown(handler: Callable[[], None]) -> None:
    _handlers.append(handler)


def request_shutdown() -> None:
    if _handlers:
        for handler in _handlers:
            handler()
        return

    os.kill(os.getpid(), signal.SIGTERM)