from __future__ import annotations
import ctypes as C
from dataclasses import dataclass
from typing import Optional, Tuple

from ._ffi import (
    load_library,
    FfiRect,
    FfiStyle,
    FfiEvent,
    FFI_EVENT_KIND,
    FFI_COLOR,
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
