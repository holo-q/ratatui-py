from __future__ import annotations
import threading
from time import monotonic
from typing import Callable, Optional, Any

_DEFAULT_BUDGET_MS = 12

class FrameBudget:
    def __init__(self, budget_ms: int = _DEFAULT_BUDGET_MS) -> None:
        self.start = monotonic()
        self.budget = max(1, int(budget_ms))

    def elapsed_ms(self) -> int:
        return int((monotonic() - self.start) * 1000)

    def should_yield(self) -> bool:
        return self.elapsed_ms() >= self.budget


def frame_begin(budget_ms: int = _DEFAULT_BUDGET_MS) -> FrameBudget:
    """Begin a new frame with a time budget in milliseconds.

    Usage:
        fb = frame_begin(12)
        while heavy_work:
            ...
            if fb.should_yield():
                break
    """
    return FrameBudget(budget_ms)


class BackgroundTask:
    """Simple, generic background worker.

    - Starts a thread that runs a function repeatedly or once.
    - Stores latest result thread-safely; UI can `peek()` without blocking.
    - Supports cooperative cancel via `stop()`.
    """
    def __init__(self, fn: Callable[["BackgroundTask"], Any], *, loop: bool = False) -> None:
        self._fn = fn
        self._loop = bool(loop)
        self._thread: Optional[threading.Thread] = None
        self._stop = threading.Event()
        self._lock = threading.Lock()
        self._result: Any = None
        self._error: Optional[BaseException] = None

    def start(self, daemon: bool = True) -> None:
        if self._thread and self._thread.is_alive():
            return
        def run():
            try:
                if self._loop:
                    while not self._stop.is_set():
                        res = self._fn(self)
                        with self._lock:
                            self._result = res
                else:
                    res = self._fn(self)
                    with self._lock:
                        self._result = res
            except BaseException as e:  # capture, don't kill process
                self._error = e
        t = threading.Thread(target=run, daemon=daemon)
        t.start()
        self._thread = t

    def stop(self, join: bool = False, timeout: Optional[float] = None) -> None:
        self._stop.set()
        if join and self._thread is not None:
            self._thread.join(timeout=timeout)

    def stopped(self) -> bool:
        return self._stop.is_set()

    def peek(self) -> Any:
        with self._lock:
            return self._result

    def error(self) -> Optional[BaseException]:
        return self._error

