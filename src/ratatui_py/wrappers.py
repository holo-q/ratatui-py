from __future__ import annotations
import ctypes as C
from dataclasses import dataclass
from typing import Optional, Tuple, Iterable, Sequence, Callable, Any, List as _List, Union
from time import monotonic

from ._ffi import (
    load_library,
    FfiRect,
    FfiStyle,
    FfiEvent,
    FFI_EVENT_KIND,
    FFI_COLOR,
    FFI_KEY_CODE,
    FFI_KEY_MODS,
    FFI_MOUSE_KIND,
    FFI_MOUSE_BUTTON,
    FFI_WIDGET_KIND,
)
from .types import RectLike

@dataclass
class Style:
    fg: int = 0  # FFI_COLOR[...] value or 0
    bg: int = 0
    mods: int = 0

    def to_ffi(self) -> FfiStyle:
        return FfiStyle(self.fg, self.bg, self.mods)

class Paragraph:
    def __init__(self, handle: int, lib=None):
        self._lib = lib or load_library()
        self._handle = C.c_void_p(handle)

    @classmethod
    def from_text(cls, text: str) -> "Paragraph":
        lib = load_library()
        ptr = lib.ratatui_paragraph_new(text.encode("utf-8"))
        if not ptr:
            raise RuntimeError("ratatui_paragraph_new failed")
        return cls(ptr, lib)

    @classmethod
    def new_empty(cls) -> "Paragraph":
        lib = load_library()
        ptr = lib.ratatui_paragraph_new_empty()
        if not ptr:
            raise RuntimeError("ratatui_paragraph_new_empty failed")
        return cls(ptr, lib)

    def append_span(self, text: str, style: Optional[Style] = None) -> None:
        st = (style or Style()).to_ffi()
        self._lib.ratatui_paragraph_append_span(self._handle, text.encode("utf-8"), st)

    def line_break(self) -> None:
        self._lib.ratatui_paragraph_line_break(self._handle)

    def set_block_title(self, title: Optional[str], show_border: bool = True) -> None:
        t = title.encode("utf-8") if title is not None else None
        self._lib.ratatui_paragraph_set_block_title(self._handle, t, bool(show_border))

    def append_line(self, text: str, style: Optional[Style] = None) -> None:
        st = (style or Style()).to_ffi()
        self._lib.ratatui_paragraph_append_line(self._handle, text.encode("utf-8"), st)

    # Note: no __del_name__ shim; rely on __del__ below guardedly.

    def close(self) -> None:
        if getattr(self, "_handle", None):
            self._lib.ratatui_paragraph_free(self._handle)
            self._handle = None

    def __del__(self):
        try:
            self.close()
        except Exception:
            pass

class Terminal:
    def __init__(self):
        self._lib = load_library()
        ptr = self._lib.ratatui_init_terminal()
        if not ptr:
            raise RuntimeError("ratatui_init_terminal failed")
        self._handle = C.c_void_p(ptr)

    def clear(self) -> None:
        self._lib.ratatui_terminal_clear(self._handle)

    def draw_paragraph(self, p: Paragraph, rect: Optional[RectLike] = None) -> bool:
        if rect is None:
            return bool(self._lib.ratatui_terminal_draw_paragraph(self._handle, p._handle))
        r = _ffi_rect(rect)
        return bool(self._lib.ratatui_terminal_draw_paragraph_in(self._handle, p._handle, r))

    def draw_list(self, lst: "List", rect: RectLike) -> bool:
        r = _ffi_rect(rect)
        return bool(self._lib.ratatui_terminal_draw_list_in(self._handle, lst._handle, r))

    def draw_table(self, tbl: "Table", rect: RectLike) -> bool:
        r = _ffi_rect(rect)
        return bool(self._lib.ratatui_terminal_draw_table_in(self._handle, tbl._handle, r))

    def draw_gauge(self, g: "Gauge", rect: RectLike) -> bool:
        r = _ffi_rect(rect)
        return bool(self._lib.ratatui_terminal_draw_gauge_in(self._handle, g._handle, r))

    def draw_tabs(self, t: "Tabs", rect: RectLike) -> bool:
        r = _ffi_rect(rect)
        return bool(self._lib.ratatui_terminal_draw_tabs_in(self._handle, t._handle, r))

    def draw_barchart(self, b: "BarChart", rect: RectLike) -> bool:
        r = _ffi_rect(rect)
        return bool(self._lib.ratatui_terminal_draw_barchart_in(self._handle, b._handle, r))

    def draw_sparkline(self, s: "Sparkline", rect: RectLike) -> bool:
        r = _ffi_rect(rect)
        return bool(self._lib.ratatui_terminal_draw_sparkline_in(self._handle, s._handle, r))

    # Chart and batched frames
    def draw_chart(self, c: "Chart", rect: RectLike) -> bool:
        r = _ffi_rect(rect)
        return bool(self._lib.ratatui_terminal_draw_chart_in(self._handle, c._handle, r))

    def draw_frame(self, cmds: _List["DrawCmd"]) -> bool:
        FfiDrawCmd = self._lib.FfiDrawCmd
        arr = (FfiDrawCmd * len(cmds))()
        # Keep owners alive across the FFI call to prevent use-after-free of handles.
        owners = []
        for i, cmd in enumerate(cmds):
            arr[i] = FfiDrawCmd(cmd.kind, cmd.handle, cmd.rect)
            if getattr(cmd, 'owner', None) is not None:
                owners.append(cmd.owner)
        ok = bool(self._lib.ratatui_terminal_draw_frame(self._handle, arr, len(cmds)))
        # owners list goes out of scope here, after the draw returns.
        return ok

    def size(self) -> Tuple[int, int]:
        w = C.c_uint16(0)
        h = C.c_uint16(0)
        ok = self._lib.ratatui_terminal_size(C.byref(w), C.byref(h))
        if not ok:
            raise RuntimeError("ratatui_terminal_size failed")
        return (int(w.value), int(h.value))

    def next_event(self, timeout_ms: int) -> Optional[dict]:
        evt = FfiEvent()
        ok = self._lib.ratatui_next_event(C.c_uint64(timeout_ms), C.byref(evt))
        if not ok:
            return None
        if evt.kind == FFI_EVENT_KIND["KEY"]:
            return {
                "kind": "key",
                "code": int(evt.key.code),
                "ch": int(evt.key.ch),
                "mods": int(evt.key.mods),
            }
        if evt.kind == FFI_EVENT_KIND["RESIZE"]:
            return {"kind": "resize", "width": int(evt.width), "height": int(evt.height)}
        if evt.kind == FFI_EVENT_KIND["MOUSE"]:
            return {
                "kind": "mouse",
                "x": int(evt.mouse_x),
                "y": int(evt.mouse_y),
                "mouse_kind": int(evt.mouse_kind),
                "mouse_btn": int(evt.mouse_btn),
                "mods": int(evt.mouse_mods),
            }
        return {"kind": "none"}

    def close(self) -> None:
        if getattr(self, "_handle", None):
            self._lib.ratatui_terminal_free(self._handle)
            self._handle = None

    def __enter__(self) -> "Terminal":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    def __del__(self):
        try:
            self.close()
        except Exception:
            pass


class App:
    """Minimal app runner to simplify event loops.

    Example:
        def render(term: Terminal, state: dict) -> None:
            w, h = term.size()
            p = Paragraph.from_text("Hello ratatui-py!\nPress q to quit.")
            p.set_block_title("Demo", True)
            term.draw_paragraph(p, (0, 0, w, h))

        def on_event(term: Terminal, evt: dict, state: dict) -> bool:
            if evt.get("kind") == "key" and evt.get("ch") in (ord('q'), ord('Q')):
                return False  # stop
            return True

        App(render=render, on_event=on_event, tick_ms=250).run({})

    """

    def __init__(
        self,
        *,
        render: Callable[["Terminal", Any], None],
        on_event: Optional[Callable[["Terminal", dict, Any], bool]] = None,
        on_tick: Optional[Callable[["Terminal", Any], None]] = None,
        on_start: Optional[Callable[["Terminal", Any], None]] = None,
        on_stop: Optional[Callable[[Optional[BaseException], "Terminal", Any], None]] = None,
        tick_ms: int = 100,
        clear_each_frame: bool = False,
    ) -> None:
        self.render = render
        self.on_event = on_event
        self.on_tick = on_tick
        self.on_start = on_start
        self.on_stop = on_stop
        self.tick_ms = int(tick_ms)
        self.clear_each_frame = bool(clear_each_frame)

    def run(self, state: Any = None) -> None:
        with Terminal() as term:
            if self.on_start:
                self.on_start(term, state)
            last_tick = monotonic()
            try:
                running = True
                while running:
                    if self.clear_each_frame:
                        term.clear()
                    self.render(term, state)
                    now = monotonic()
                    # Budget remaining time for event wait so ticks are paced.
                    elapsed_ms = int((now - last_tick) * 1000)
                    wait_ms = max(0, self.tick_ms - elapsed_ms)
                    evt = term.next_event(wait_ms)
                    if evt is not None and self.on_event is not None:
                        keep_going = self.on_event(term, evt, state)
                        if keep_going is False:
                            break
                    now2 = monotonic()
                    if (now2 - last_tick) * 1000 >= self.tick_ms:
                        if self.on_tick is not None:
                            self.on_tick(term, state)
                        last_tick = now2
            except BaseException as e:
                if self.on_stop:
                    self.on_stop(e, term, state)
                raise
            else:
                if self.on_stop:
                    self.on_stop(None, term, state)

# Convenience: headless render paragraph

def headless_render_paragraph(width: int, height: int, p: Paragraph) -> str:
    lib = p._lib
    out = C.c_char_p()
    ok = lib.ratatui_headless_render_paragraph(C.c_uint16(width), C.c_uint16(height), p._handle, C.byref(out))
    if not ok or not out:
        return ""
    try:
        s = C.cast(out, C.c_char_p).value.decode("utf-8", errors="replace")
    finally:
        lib.ratatui_string_free(out)
    return s


class List:
    def __init__(self):
        self._lib = load_library()
        ptr = self._lib.ratatui_list_new()
        if not ptr:
            raise RuntimeError("ratatui_list_new failed")
        self._handle = C.c_void_p(ptr)

    def append_item(self, text: str, style: Optional[Style] = None) -> None:
        st = (style or Style()).to_ffi()
        self._lib.ratatui_list_append_item(self._handle, text.encode("utf-8"), st)

    def set_block_title(self, title: Optional[str], show_border: bool = True) -> None:
        t = title.encode("utf-8") if title is not None else None
        self._lib.ratatui_list_set_block_title(self._handle, t, bool(show_border))

    def set_selected(self, idx: Optional[int]) -> None:
        self._lib.ratatui_list_set_selected(self._handle, -1 if idx is None else int(idx))

    def set_highlight_style(self, style: Style) -> None:
        self._lib.ratatui_list_set_highlight_style(self._handle, style.to_ffi())

    def set_highlight_symbol(self, sym: Optional[str]) -> None:
        s = None if sym is None else sym.encode("utf-8")
        self._lib.ratatui_list_set_highlight_symbol(self._handle, s)

    def close(self) -> None:
        if getattr(self, "_handle", None):
            self._lib.ratatui_list_free(self._handle)
            self._handle = None

    def __del__(self):
        try:
            self.close()
        except Exception:
            pass


class Table:
    def __init__(self):
        self._lib = load_library()
        ptr = self._lib.ratatui_table_new()
        if not ptr:
            raise RuntimeError("ratatui_table_new failed")
        self._handle = C.c_void_p(ptr)

    def set_headers(self, headers: Sequence[str]) -> None:
        tsv = "\t".join(headers).encode("utf-8")
        self._lib.ratatui_table_set_headers(self._handle, tsv)

    def append_row(self, row: Sequence[str]) -> None:
        tsv = "\t".join(row).encode("utf-8")
        self._lib.ratatui_table_append_row(self._handle, tsv)

    def set_block_title(self, title: Optional[str], show_border: bool = True) -> None:
        t = title.encode("utf-8") if title is not None else None
        self._lib.ratatui_table_set_block_title(self._handle, t, bool(show_border))

    def set_selected(self, idx: Optional[int]) -> None:
        self._lib.ratatui_table_set_selected(self._handle, -1 if idx is None else int(idx))

    def set_row_highlight_style(self, style: Style) -> None:
        self._lib.ratatui_table_set_row_highlight_style(self._handle, style.to_ffi())

    def set_highlight_symbol(self, sym: Optional[str]) -> None:
        s = None if sym is None else sym.encode("utf-8")
        self._lib.ratatui_table_set_highlight_symbol(self._handle, s)

    def close(self) -> None:
        if getattr(self, "_handle", None):
            self._lib.ratatui_table_free(self._handle)
            self._handle = None

    def __del__(self):
        try:
            self.close()
        except Exception:
            pass


class Gauge:
    def __init__(self):
        self._lib = load_library()
        ptr = self._lib.ratatui_gauge_new()
        if not ptr:
            raise RuntimeError("ratatui_gauge_new failed")
        self._handle = C.c_void_p(ptr)

    def ratio(self, value: float) -> "Gauge":
        self._lib.ratatui_gauge_set_ratio(self._handle, float(value))
        return self

    def label(self, text: Optional[str]) -> "Gauge":
        t = text.encode("utf-8") if text is not None else None
        self._lib.ratatui_gauge_set_label(self._handle, t)
        return self

    def set_block_title(self, title: Optional[str], show_border: bool = True) -> None:
        t = title.encode("utf-8") if title is not None else None
        self._lib.ratatui_gauge_set_block_title(self._handle, t, bool(show_border))

    def close(self) -> None:
        if getattr(self, "_handle", None):
            self._lib.ratatui_gauge_free(self._handle)
            self._handle = None

    def __del__(self):
        try:
            self.close()
        except Exception:
            pass


class Tabs:
    def __init__(self):
        self._lib = load_library()
        ptr = self._lib.ratatui_tabs_new()
        if not ptr:
            raise RuntimeError("ratatui_tabs_new failed")
        self._handle = C.c_void_p(ptr)

    def set_titles(self, titles: Sequence[str]) -> None:
        tsv = "\t".join(titles).encode("utf-8")
        self._lib.ratatui_tabs_set_titles(self._handle, tsv)

    def set_selected(self, idx: int) -> None:
        self._lib.ratatui_tabs_set_selected(self._handle, int(idx))

    def set_block_title(self, title: Optional[str], show_border: bool = True) -> None:
        t = title.encode("utf-8") if title is not None else None
        self._lib.ratatui_tabs_set_block_title(self._handle, t, bool(show_border))

    def close(self) -> None:
        if getattr(self, "_handle", None):
            self._lib.ratatui_tabs_free(self._handle)
            self._handle = None

    def __del__(self):
        try:
            self.close()
        except Exception:
            pass


class BarChart:
    def __init__(self):
        self._lib = load_library()
        ptr = self._lib.ratatui_barchart_new()
        if not ptr:
            raise RuntimeError("ratatui_barchart_new failed")
        self._handle = C.c_void_p(ptr)

    def set_values(self, values: Iterable[int]) -> None:
        arr = (C.c_uint64 * len(list(values)))(*list(values))
        self._lib.ratatui_barchart_set_values(self._handle, arr, len(arr))

    def set_labels(self, labels: Sequence[str]) -> None:
        tsv = "\t".join(labels).encode("utf-8")
        self._lib.ratatui_barchart_set_labels(self._handle, tsv)

    def set_block_title(self, title: Optional[str], show_border: bool = True) -> None:
        t = title.encode("utf-8") if title is not None else None
        self._lib.ratatui_barchart_set_block_title(self._handle, t, bool(show_border))

    def close(self) -> None:
        if getattr(self, "_handle", None):
            self._lib.ratatui_barchart_free(self._handle)
            self._handle = None

    def __del__(self):
        try:
            self.close()
        except Exception:
            pass


class Sparkline:
    def __init__(self):
        self._lib = load_library()
        ptr = self._lib.ratatui_sparkline_new()
        if not ptr:
            raise RuntimeError("ratatui_sparkline_new failed")
        self._handle = C.c_void_p(ptr)

    def set_values(self, values: Iterable[int]) -> None:
        arr = (C.c_uint64 * len(list(values)))(*list(values))
        self._lib.ratatui_sparkline_set_values(self._handle, arr, len(arr))

    def set_block_title(self, title: Optional[str], show_border: bool = True) -> None:
        t = title.encode("utf-8") if title is not None else None
        self._lib.ratatui_sparkline_set_block_title(self._handle, t, bool(show_border))

    def close(self) -> None:
        if getattr(self, "_handle", None):
            self._lib.ratatui_sparkline_free(self._handle)
            self._handle = None

    def __del__(self):
        try:
            self.close()
        except Exception:
            pass


# Optional Scrollbar (only if built with feature)
class Scrollbar:
    def __init__(self):
        self._lib = load_library()
        if not hasattr(self._lib, 'ratatui_scrollbar_new'):
            raise RuntimeError("ratatui_ffi built without 'scrollbar' feature")
        ptr = self._lib.ratatui_scrollbar_new()
        if not ptr:
            raise RuntimeError("ratatui_scrollbar_new failed")
        self._handle = C.c_void_p(ptr)

    def configure(self, orient: str, position: int, content_len: int, viewport_len: int) -> None:
        o = 0 if orient.lower().startswith('v') else 1
        self._lib.ratatui_scrollbar_configure(self._handle, o, int(position), int(content_len), int(viewport_len))

    def set_block_title(self, title: Optional[str], show_border: bool = True) -> None:
        t = title.encode("utf-8") if title is not None else None
        self._lib.ratatui_scrollbar_set_block_title(self._handle, t, bool(show_border))

    def close(self) -> None:
        if getattr(self, "_handle", None):
            self._lib.ratatui_scrollbar_free(self._handle)
            self._handle = None

    def __del__(self):
        try:
            self.close()
        except Exception:
            pass


# Headless helpers for other widgets
def headless_render_list(width: int, height: int, lst: List) -> str:
    lib = lst._lib
    out = C.c_char_p()
    ok = lib.ratatui_headless_render_list(C.c_uint16(width), C.c_uint16(height), lst._handle, C.byref(out))
    if not ok or not out:
        return ""
    try:
        return C.cast(out, C.c_char_p).value.decode("utf-8", errors="replace")
    finally:
        lib.ratatui_string_free(out)

def headless_render_table(width: int, height: int, tbl: Table) -> str:
    lib = tbl._lib
    out = C.c_char_p()
    ok = lib.ratatui_headless_render_table(C.c_uint16(width), C.c_uint16(height), tbl._handle, C.byref(out))
    if not ok or not out:
        return ""
    try:
        return C.cast(out, C.c_char_p).value.decode("utf-8", errors="replace")
    finally:
        lib.ratatui_string_free(out)

def headless_render_gauge(width: int, height: int, g: Gauge) -> str:
    lib = g._lib
    out = C.c_char_p()
    ok = lib.ratatui_headless_render_gauge(C.c_uint16(width), C.c_uint16(height), g._handle, C.byref(out))
    if not ok or not out:
        return ""
    try:
        return C.cast(out, C.c_char_p).value.decode("utf-8", errors="replace")
    finally:
        lib.ratatui_string_free(out)

def headless_render_tabs(width: int, height: int, t: Tabs) -> str:
    lib = t._lib
    out = C.c_char_p()
    ok = lib.ratatui_headless_render_tabs(C.c_uint16(width), C.c_uint16(height), t._handle, C.byref(out))
    if not ok or not out:
        return ""
    try:
        return C.cast(out, C.c_char_p).value.decode("utf-8", errors="replace")
    finally:
        lib.ratatui_string_free(out)

def headless_render_barchart(width: int, height: int, b: BarChart) -> str:
    lib = b._lib
    out = C.c_char_p()
    ok = lib.ratatui_headless_render_barchart(C.c_uint16(width), C.c_uint16(height), b._handle, C.byref(out))
    if not ok or not out:
        return ""
    try:
        return C.cast(out, C.c_char_p).value.decode("utf-8", errors="replace")
    finally:
        lib.ratatui_string_free(out)

def headless_render_sparkline(width: int, height: int, s: Sparkline) -> str:
    lib = s._lib
    out = C.c_char_p()
    ok = lib.ratatui_headless_render_sparkline(C.c_uint16(width), C.c_uint16(height), s._handle, C.byref(out))
    if not ok or not out:
        return ""
    try:
        return C.cast(out, C.c_char_p).value.decode("utf-8", errors="replace")
    finally:
        lib.ratatui_string_free(out)


class Chart:
    def __init__(self):
        self._lib = load_library()
        ptr = self._lib.ratatui_chart_new()
        if not ptr:
            raise RuntimeError("ratatui_chart_new failed")
        self._handle = C.c_void_p(ptr)

    def add_line(self, name: str, points: Sequence[Tuple[float, float]], style: Optional[Style] = None) -> None:
        n = name.encode("utf-8")
        flat = []
        for (x, y) in points:
            flat.extend([float(x), float(y)])
        arr = (C.c_double * len(flat))(*flat)
        self._lib.ratatui_chart_add_line(self._handle, n, arr, len(points), (style or Style()).to_ffi())

    def set_axes_titles(self, x: Optional[str], y: Optional[str]) -> None:
        xx = None if x is None else x.encode("utf-8")
        yy = None if y is None else y.encode("utf-8")
        self._lib.ratatui_chart_set_axes_titles(self._handle, xx, yy)

    def set_block_title(self, title: Optional[str], show_border: bool = True) -> None:
        t = None if title is None else title.encode("utf-8")
        self._lib.ratatui_chart_set_block_title(self._handle, t, bool(show_border))

    def close(self) -> None:
        if getattr(self, "_handle", None):
            self._lib.ratatui_chart_free(self._handle)
            self._handle = None

    def __del__(self):
        try:
            self.close()
        except Exception:
            pass


def headless_render_chart(width: int, height: int, c: Chart) -> str:
    lib = c._lib
    out = C.c_char_p()
    ok = lib.ratatui_headless_render_chart(C.c_uint16(width), C.c_uint16(height), c._handle, C.byref(out))
    if not ok or not out:
        return ""
    try:
        return C.cast(out, C.c_char_p).value.decode("utf-8", errors="replace")
    finally:
        lib.ratatui_string_free(out)


class DrawCmd:
    def __init__(self, kind: int, handle: C.c_void_p, rect: FfiRect, owner: Optional[object] = None):
        self.kind = int(kind)
        self.handle = handle
        self.rect = rect
        # Keep a strong reference to the owning Python object so the FFI handle
        # isn't freed by GC before the draw call consumes it.
        self.owner = owner

    @staticmethod
    def paragraph(p: Paragraph, rect: RectLike) -> "DrawCmd":
        return DrawCmd(FFI_WIDGET_KIND["Paragraph"], p._handle, _ffi_rect(rect), owner=p)

    @staticmethod
    def list(lst: List, rect: RectLike) -> "DrawCmd":
        return DrawCmd(FFI_WIDGET_KIND["List"], lst._handle, _ffi_rect(rect), owner=lst)

    @staticmethod
    def table(t: Table, rect: RectLike) -> "DrawCmd":
        return DrawCmd(FFI_WIDGET_KIND["Table"], t._handle, _ffi_rect(rect), owner=t)

    @staticmethod
    def gauge(g: Gauge, rect: RectLike) -> "DrawCmd":
        return DrawCmd(FFI_WIDGET_KIND["Gauge"], g._handle, _ffi_rect(rect), owner=g)

    @staticmethod
    def tabs(t: Tabs, rect: RectLike) -> "DrawCmd":
        return DrawCmd(FFI_WIDGET_KIND["Tabs"], t._handle, _ffi_rect(rect), owner=t)

    @staticmethod
    def barchart(b: BarChart, rect: RectLike) -> "DrawCmd":
        return DrawCmd(FFI_WIDGET_KIND["BarChart"], b._handle, _ffi_rect(rect), owner=b)

    @staticmethod
    def sparkline(s: Sparkline, rect: RectLike) -> "DrawCmd":
        return DrawCmd(FFI_WIDGET_KIND["Sparkline"], s._handle, _ffi_rect(rect), owner=s)

    @staticmethod
    def chart(c: Chart, rect: RectLike) -> "DrawCmd":
        return DrawCmd(FFI_WIDGET_KIND["Chart"], c._handle, _ffi_rect(rect), owner=c)


def _ffi_rect(rect: RectLike) -> FfiRect:
    """Accept either a tuple or a Rect and produce an FfiRect.

    This keeps the external API pythonic while preserving a zero-copy path
    for the FFI struct construction.
    """
    if hasattr(rect, "to_tuple"):
        x, y, w, h = rect.to_tuple()  # type: ignore[attr-defined]
        return FfiRect(int(x), int(y), int(w), int(h))
    x, y, w, h = rect  # type: ignore[misc]
    return FfiRect(int(x), int(y), int(w), int(h))
