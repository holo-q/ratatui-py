from __future__ import annotations
import ctypes as C
from dataclasses import dataclass
from typing import Optional, Tuple, Iterable, Sequence, List as _List

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

    def set_block_title(self, title: str | None, show_border: bool = True) -> None:
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

    def draw_paragraph(self, p: Paragraph, rect: Optional[Tuple[int,int,int,int]] = None) -> bool:
        if rect is None:
            return bool(self._lib.ratatui_terminal_draw_paragraph(self._handle, p._handle))
        r = FfiRect(*map(int, rect))
        return bool(self._lib.ratatui_terminal_draw_paragraph_in(self._handle, p._handle, r))

    def draw_list(self, lst: "List", rect: Tuple[int,int,int,int]) -> bool:
        r = FfiRect(*map(int, rect))
        return bool(self._lib.ratatui_terminal_draw_list_in(self._handle, lst._handle, r))

    def draw_table(self, tbl: "Table", rect: Tuple[int,int,int,int]) -> bool:
        r = FfiRect(*map(int, rect))
        return bool(self._lib.ratatui_terminal_draw_table_in(self._handle, tbl._handle, r))

    def draw_gauge(self, g: "Gauge", rect: Tuple[int,int,int,int]) -> bool:
        r = FfiRect(*map(int, rect))
        return bool(self._lib.ratatui_terminal_draw_gauge_in(self._handle, g._handle, r))

    def draw_tabs(self, t: "Tabs", rect: Tuple[int,int,int,int]) -> bool:
        r = FfiRect(*map(int, rect))
        return bool(self._lib.ratatui_terminal_draw_tabs_in(self._handle, t._handle, r))

    def draw_barchart(self, b: "BarChart", rect: Tuple[int,int,int,int]) -> bool:
        r = FfiRect(*map(int, rect))
        return bool(self._lib.ratatui_terminal_draw_barchart_in(self._handle, b._handle, r))

    def draw_sparkline(self, s: "Sparkline", rect: Tuple[int,int,int,int]) -> bool:
        r = FfiRect(*map(int, rect))
        return bool(self._lib.ratatui_terminal_draw_sparkline_in(self._handle, s._handle, r))

    # Chart and batched frames
    def draw_chart(self, c: "Chart", rect: Tuple[int,int,int,int]) -> bool:
        r = FfiRect(*map(int, rect))
        return bool(self._lib.ratatui_terminal_draw_chart_in(self._handle, c._handle, r))

    def draw_frame(self, cmds: _List["DrawCmd"]) -> bool:
        FfiDrawCmd = self._lib.FfiDrawCmd
        arr = (FfiDrawCmd * len(cmds))()
        for i, cmd in enumerate(cmds):
            arr[i] = FfiDrawCmd(cmd.kind, cmd.handle, cmd.rect)
        return bool(self._lib.ratatui_terminal_draw_frame(self._handle, arr, len(cmds)))

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
    def __init__(self, kind: int, handle: C.c_void_p, rect: FfiRect):
        self.kind = int(kind)
        self.handle = handle
        self.rect = rect

    @staticmethod
    def paragraph(p: Paragraph, rect: Tuple[int,int,int,int]) -> "DrawCmd":
        return DrawCmd(FFI_WIDGET_KIND["Paragraph"], p._handle, FfiRect(*map(int, rect)))

    @staticmethod
    def list(lst: List, rect: Tuple[int,int,int,int]) -> "DrawCmd":
        return DrawCmd(FFI_WIDGET_KIND["List"], lst._handle, FfiRect(*map(int, rect)))

    @staticmethod
    def table(t: Table, rect: Tuple[int,int,int,int]) -> "DrawCmd":
        return DrawCmd(FFI_WIDGET_KIND["Table"], t._handle, FfiRect(*map(int, rect)))

    @staticmethod
    def gauge(g: Gauge, rect: Tuple[int,int,int,int]) -> "DrawCmd":
        return DrawCmd(FFI_WIDGET_KIND["Gauge"], g._handle, FfiRect(*map(int, rect)))

    @staticmethod
    def tabs(t: Tabs, rect: Tuple[int,int,int,int]) -> "DrawCmd":
        return DrawCmd(FFI_WIDGET_KIND["Tabs"], t._handle, FfiRect(*map(int, rect)))

    @staticmethod
    def barchart(b: BarChart, rect: Tuple[int,int,int,int]) -> "DrawCmd":
        return DrawCmd(FFI_WIDGET_KIND["BarChart"], b._handle, FfiRect(*map(int, rect)))

    @staticmethod
    def sparkline(s: Sparkline, rect: Tuple[int,int,int,int]) -> "DrawCmd":
        return DrawCmd(FFI_WIDGET_KIND["Sparkline"], s._handle, FfiRect(*map(int, rect)))

    @staticmethod
    def chart(c: Chart, rect: Tuple[int,int,int,int]) -> "DrawCmd":
        return DrawCmd(FFI_WIDGET_KIND["Chart"], c._handle, FfiRect(*map(int, rect)))
