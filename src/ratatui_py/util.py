from __future__ import annotations
import threading
from time import monotonic
from typing import Callable, Optional, Any

# ProcessTask depends on multiprocessing but is imported lazily to avoid
# impacting interpreter start and to play nicely with frozen apps on Windows.
_MP = None  # populated on first ProcessTask.start()

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


class ProcessTask:
    """Run CPU-bound work in a separate process with a simple, UI-friendly API.

    - Avoids the GIL for pure-Python CPU loops; UI stays responsive.
    - Submit the latest job parameters via `submit()`; the worker reads the
      most recent job with `ctx.recv_latest()` and publishes results with
      `ctx.publish(result)`.
    - The main thread calls `peek()` each frame to fetch the newest completed
      result without blocking (older results are dropped).

    Usage (looping worker):
        def worker(ctx):
            params = None
            while not ctx.should_stop():
                # get the most recent request (drops stale ones)
                msg = ctx.recv_latest(timeout=0.01)
                if msg is not None:
                    params = msg
                if params is None:
                    continue
                result = do_heavy_compute(params)
                ctx.publish(result)

        task = ProcessTask(worker, loop=True)
        task.start()
        task.submit({"zoom": 1.5})
        ...
        latest = task.peek()  # None or last completed result

    Notes:
    - Messages and results must be picklable.
    - Default start method is 'spawn' for cross-platform safety.
    - Use `stop(join=True)` on shutdown; pass `terminate=True` to force-kill.
    """

    class _Ctx:
        def __init__(self, in_q, out_q, stop_evt):
            self._in = in_q
            self._out = out_q
            self._stop = stop_evt

        def should_stop(self) -> bool:
            return self._stop.is_set()

        def stop(self) -> None:
            self._stop.set()

        def recv_latest(self, timeout: float | int = 0) -> Any:
            try:
                item = self._in.get(timeout=timeout) if timeout and timeout > 0 else self._in.get_nowait()
            except Exception:
                return None
            # drain to the most recent
            try:
                while True:
                    item = self._in.get_nowait()
            except Exception:
                pass
            return item

        def publish(self, result: Any) -> None:
            try:
                self._out.put_nowait(result)
            except Exception:
                # drop oldest then try once more
                try:
                    self._out.get_nowait()
                except Exception:
                    pass
                try:
                    self._out.put_nowait(result)
                except Exception:
                    pass

    def __init__(
        self,
        fn: Callable[["ProcessTask._Ctx"], Any],
        *,
        loop: bool = False,
        start_method: str = "spawn",
        max_queue: int = 4,
    ) -> None:
        self._fn = fn
        self._loop = bool(loop)
        self._start_method = start_method
        self._max_queue = max(1, int(max_queue))
        self._proc = None
        self._in_q = None
        self._out_q = None
        self._stop_evt = None
        self._last_result = None
        self._error: Optional[str] = None

    def _ensure_mp(self):
        global _MP
        if _MP is None:
            import multiprocessing as _mp
            _MP = _mp

    @staticmethod
    def _worker(fn, loop, in_q, out_q, stop_evt):
        import traceback
        ctx = ProcessTask._Ctx(in_q, out_q, stop_evt)
        try:
            if loop:
                while not stop_evt.is_set():
                    fn(ctx)
            else:
                fn(ctx)
        except BaseException as e:
            try:
                out_q.put_nowait({"__error__": "".join(traceback.format_exception(type(e), e, e.__traceback__))})
            except Exception:
                pass

    def start(self, daemon: bool = True) -> None:
        if self._proc is not None:
            return
        self._ensure_mp()
        ctx = _MP.get_context(self._start_method)
        self._in_q = ctx.Queue(self._max_queue)
        self._out_q = ctx.Queue(self._max_queue)
        self._stop_evt = ctx.Event()
        self._proc = ctx.Process(
            target=ProcessTask._worker,
            args=(self._fn, self._loop, self._in_q, self._out_q, self._stop_evt),
            daemon=daemon,
        )
        self._proc.start()

    def submit(self, msg: Any) -> None:
        if not self._in_q:
            self.start()
        try:
            self._in_q.put_nowait(msg)
        except Exception:
            # drop oldest then try again
            try:
                self._in_q.get_nowait()
            except Exception:
                pass
            try:
                self._in_q.put_nowait(msg)
            except Exception:
                pass

    def peek(self) -> Any:
        if not self._out_q:
            return None
        latest = None
        try:
            while True:
                item = self._out_q.get_nowait()
                # capture worker error if present
                if isinstance(item, dict) and "__error__" in item:
                    self._error = str(item["__error__"]).strip()
                    continue
                latest = item
        except Exception:
            pass
        if latest is not None:
            self._last_result = latest
        return latest

    def error(self) -> Optional[str]:
        # also surface errors queued but not yet peeked
        self.peek()
        return self._error

    def stop(self, *, join: bool = False, timeout: Optional[float] = None, terminate: bool = False) -> None:
        if self._stop_evt is not None:
            self._stop_evt.set()
        if join and self._proc is not None:
            self._proc.join(timeout=timeout)
        if terminate and self._proc is not None and self._proc.is_alive():
            self._proc.terminate()

    def alive(self) -> bool:
        return bool(self._proc and self._proc.is_alive())

    def __enter__(self) -> "ProcessTask":
        self.start()
        return self

    def __exit__(self, exc_type, exc, tb):
        self.stop(join=True, timeout=0.5, terminate=True)
