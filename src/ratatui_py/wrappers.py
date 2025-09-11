from __future__ import annotations
import ctypes as C
from dataclasses import dataclass
from typing import Optional, Tuple, Iterable, Sequence, Callable, Any, List as _List, Union
import enum
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
    FFI_ALIGN,
    FFI_BORDERS,
    FFI_BORDER_TYPE,
    FFI_WIDGET_KIND,
)
from .types import RectLike, Color, KeyCode, KeyMods, MouseKind, MouseButton, Mod

@dataclass
class Style:
    fg: Union[int, enum.IntEnum] = 0  # accepts raw int or Color-like enums
    bg: Union[int, enum.IntEnum] = 0
    mods: int = 0

    def to_ffi(self) -> FfiStyle:
        fg = int(self.fg) if isinstance(self.fg, enum.IntEnum) else int(self.fg)
        bg = int(self.bg) if isinstance(self.bg, enum.IntEnum) else int(self.bg)
        return FfiStyle(fg, bg, int(self.mods))

    # Fluent helpers (return a new Style for chaining)
    def with_fg(self, fg: Union[int, enum.IntEnum]) -> "Style":
        return Style(fg=fg, bg=self.bg, mods=self.mods)

    def with_bg(self, bg: Union[int, enum.IntEnum]) -> "Style":
        return Style(fg=self.fg, bg=bg, mods=self.mods)

    def with_mods(self, mods: int | Mod) -> "Style":
        return Style(fg=self.fg, bg=self.bg, mods=int(mods))

    def add_mods(self, mods: int | Mod) -> "Style":
        return Style(fg=self.fg, bg=self.bg, mods=(int(self.mods) | int(mods)))

    def bold(self) -> "Style":
        return self.add_mods(Mod.BOLD)

    def italic(self) -> "Style":
        return self.add_mods(Mod.ITALIC)

    def underlined(self) -> "Style":
        return self.add_mods(Mod.UNDERLINED)

    def reversed(self) -> "Style":
        return self.add_mods(Mod.REVERSED)

    def dim(self) -> "Style":
        return self.add_mods(Mod.DIM)

    def crossed_out(self) -> "Style":
        return self.add_mods(Mod.CROSSED_OUT)

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

    def set_alignment(self, align: str | int) -> "Paragraph":
        if hasattr(self._lib, 'ratatui_paragraph_set_alignment'):
            a = _align_value(align)
            self._lib.ratatui_paragraph_set_alignment(self._handle, C.c_uint(a))
        return self

    def set_block_title_alignment(self, align: str | int) -> "Paragraph":
        if hasattr(self._lib, 'ratatui_paragraph_set_block_title_alignment'):
            a = _align_value(align)
            self._lib.ratatui_paragraph_set_block_title_alignment(self._handle, C.c_uint(a))
        return self

    def append_line(self, text: str, style: Optional[Style] = None) -> None:
        st = (style or Style()).to_ffi()
        self._lib.ratatui_paragraph_append_line(self._handle, text.encode("utf-8"), st)

    # Advanced configuration (v0.2.0+)
    def set_style(self, style: Style) -> "Paragraph":
        if hasattr(self._lib, 'ratatui_paragraph_set_style'):
            self._lib.ratatui_paragraph_set_style(self._handle, style.to_ffi())
        return self

    def set_wrap(self, trim: bool = True) -> "Paragraph":
        if hasattr(self._lib, 'ratatui_paragraph_set_wrap'):
            self._lib.ratatui_paragraph_set_wrap(self._handle, bool(trim))
        return self

    def set_scroll(self, offset: int) -> "Paragraph":
        if hasattr(self._lib, 'ratatui_paragraph_set_scroll'):
            self._lib.ratatui_paragraph_set_scroll(self._handle, C.c_uint16(int(offset)))
        return self

    def reserve_lines(self, n: int) -> "Paragraph":
        if hasattr(self._lib, 'ratatui_paragraph_reserve_lines'):
            self._lib.ratatui_paragraph_reserve_lines(self._handle, C.c_size_t(int(n)))
        return self

    # Batch span helpers
    def append_spans(self, spans: Sequence[tuple[str, "Style"]]) -> None:
        if not hasattr(self._lib, 'ratatui_paragraph_append_spans'):
            # fallback: join as a single line
            for text, style in spans:
                self.append_span(text, style)
            return
        arr, _keep = _build_spans(spans)
        self._lib.ratatui_paragraph_append_spans(self._handle, arr, len(arr))

    def append_line_spans(self, spans: Sequence[tuple[str, "Style"]]) -> None:
        if not hasattr(self._lib, 'ratatui_paragraph_append_line_spans'):
            self.append_spans(spans)
            self.line_break()
            return
        arr, _keep = _build_spans(spans)
        self._lib.ratatui_paragraph_append_line_spans(self._handle, arr, len(arr))

    def append_lines_spans(self, lines: Sequence[Sequence[tuple[str, "Style"]]]) -> None:
        if not hasattr(self._lib, 'ratatui_paragraph_append_lines_spans'):
            for line in lines:
                self.append_line_spans(line)
            return
        lines_arr, _keep = _build_lines_spans(lines)
        self._lib.ratatui_paragraph_append_lines_spans(self._handle, lines_arr, len(lines_arr))

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

    # Context-managed frame builder for ergonomic batched draws
    def frame(self) -> "Frame":
        return Frame(self)

class Terminal:
    def __init__(self):
        self._lib = load_library()
        ptr = self._lib.ratatui_init_terminal()
        if not ptr:
            raise RuntimeError("ratatui_init_terminal failed")
        self._handle = C.c_void_p(ptr)

    def clear(self) -> None:
        self._lib.ratatui_terminal_clear(self._handle)

    # Raw/alt/cursor/viewport controls (present in v0.2.0+)
    def enable_raw(self) -> None:
        if hasattr(self._lib, 'ratatui_terminal_enable_raw'):
            self._lib.ratatui_terminal_enable_raw()

    def disable_raw(self) -> None:
        if hasattr(self._lib, 'ratatui_terminal_disable_raw'):
            self._lib.ratatui_terminal_disable_raw()

    def enter_alt(self) -> None:
        if hasattr(self._lib, 'ratatui_terminal_enter_alt'):
            self._lib.ratatui_terminal_enter_alt()

    def leave_alt(self) -> None:
        if hasattr(self._lib, 'ratatui_terminal_leave_alt'):
            self._lib.ratatui_terminal_leave_alt()

    def show_cursor(self) -> None:
        if hasattr(self._lib, 'ratatui_terminal_show_cursor'):
            self._lib.ratatui_terminal_show_cursor()

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

    # Clear region widget
    def draw_clear(self, rect: RectLike) -> bool:
        if not hasattr(self._lib, 'ratatui_clear_in'):
            return False
        r = _ffi_rect(rect)
        return bool(self._lib.ratatui_clear_in(self._handle, r))

    # Chart and batched frames
    def draw_chart(self, c: "Chart", rect: RectLike) -> bool:
        r = _ffi_rect(rect)
        return bool(self._lib.ratatui_terminal_draw_chart_in(self._handle, c._handle, r))

    def draw_canvas(self, canvas: "Canvas", rect: RectLike) -> bool:
        if not hasattr(self._lib, 'ratatui_terminal_draw_canvas_in'):
            return False
        r = _ffi_rect(rect)
        return bool(self._lib.ratatui_terminal_draw_canvas_in(self._handle, canvas._handle, r))

    def draw_logo(self, rect: RectLike) -> bool:
        if not hasattr(self._lib, 'ratatui_ratatuilogo_draw_in'):
            return False
        r = _ffi_rect(rect)
        return bool(self._lib.ratatui_ratatuilogo_draw_in(self._handle, r))

    def draw_logo_sized(self, rect: RectLike, size: int) -> bool:
        if not hasattr(self._lib, 'ratatui_ratatuilogo_draw_sized_in'):
            return False
        r = _ffi_rect(rect)
        return bool(self._lib.ratatui_ratatuilogo_draw_sized_in(self._handle, r, C.c_uint32(int(size))))

    def draw_frame(self, cmds: Sequence["DrawCmd"]) -> bool:
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

    def get_cursor_position(self) -> Tuple[int, int]:
        if not hasattr(self._lib, 'ratatui_terminal_get_cursor_position'):
            raise RuntimeError('cursor position not supported by FFI build')
        x = C.c_uint16(0)
        y = C.c_uint16(0)
        ok = self._lib.ratatui_terminal_get_cursor_position(C.byref(x), C.byref(y))
        if not ok:
            raise RuntimeError('ratatui_terminal_get_cursor_position failed')
        return (int(x.value), int(y.value))

    def set_cursor_position(self, x: int, y: int) -> None:
        if not hasattr(self._lib, 'ratatui_terminal_set_cursor_position'):
            raise RuntimeError('set cursor position not supported by FFI build')
        self._lib.ratatui_terminal_set_cursor_position(C.c_uint16(int(x)), C.c_uint16(int(y)))

    def get_viewport_area(self) -> Tuple[int, int, int, int]:
        if not hasattr(self._lib, 'ratatui_terminal_get_viewport_area'):
            raise RuntimeError('viewport area not supported by FFI build')
        r = FfiRect(0, 0, 0, 0)
        ok = self._lib.ratatui_terminal_get_viewport_area(C.byref(r))
        if not ok:
            raise RuntimeError('ratatui_terminal_get_viewport_area failed')
        return (int(r.x), int(r.y), int(r.width), int(r.height))

    def set_viewport_area(self, rect: RectLike) -> None:
        if not hasattr(self._lib, 'ratatui_terminal_set_viewport_area'):
            raise RuntimeError('set viewport area not supported by FFI build')
        r = _ffi_rect(rect)
        self._lib.ratatui_terminal_set_viewport_area(r)

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

    # Event injection (for tests/automation)
    def inject_key(self, code: int, ch: int = 0, mods: int = 0) -> None:
        if hasattr(self._lib, 'ratatui_inject_key'):
            self._lib.ratatui_inject_key(C.c_uint32(int(code)), C.c_uint32(int(ch)), C.c_uint8(int(mods)))

    def inject_resize(self, width: int, height: int) -> None:
        if hasattr(self._lib, 'ratatui_inject_resize'):
            self._lib.ratatui_inject_resize(C.c_uint16(int(width)), C.c_uint16(int(height)))

    def inject_mouse(self, kind: int, btn: int, x: int, y: int, mods: int = 0) -> None:
        if hasattr(self._lib, 'ratatui_inject_mouse'):
            self._lib.ratatui_inject_mouse(C.c_uint32(int(kind)), C.c_uint32(int(btn)), C.c_uint16(int(x)), C.c_uint16(int(y)), C.c_uint8(int(mods)))

    # Typed event API for better IDE hints and fewer stringly-typed checks
    def next_event_typed(self, timeout_ms: int):
        evt = FfiEvent()
        ok = self._lib.ratatui_next_event(C.c_uint64(timeout_ms), C.byref(evt))
        if not ok:
            return None
        if evt.kind == FFI_EVENT_KIND["KEY"]:
            return (
                __import__('ratatui_py.types', fromlist=['KeyEvt']).KeyEvt(
                    kind="key",
                    code=KeyCode(int(evt.key.code)),
                    ch=int(evt.key.ch),
                    mods=KeyMods(int(evt.key.mods)),
                )
            )
        if evt.kind == FFI_EVENT_KIND["RESIZE"]:
            return (
                __import__('ratatui_py.types', fromlist=['ResizeEvt']).ResizeEvt(
                    kind="resize",
                    width=int(evt.width),
                    height=int(evt.height),
                )
            )
        if evt.kind == FFI_EVENT_KIND["MOUSE"]:
            return (
                __import__('ratatui_py.types', fromlist=['MouseEvt']).MouseEvt(
                    kind="mouse",
                    x=int(evt.mouse_x),
                    y=int(evt.mouse_y),
                    mouse_kind=MouseKind(int(evt.mouse_kind)),
                    mouse_btn=MouseButton(int(evt.mouse_btn)),
                    mods=KeyMods(int(evt.mouse_mods)),
                )
            )
        return None

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

    def set_block_title_alignment(self, align: str | int) -> None:
        if hasattr(self._lib, 'ratatui_list_set_block_title_alignment'):
            self._lib.ratatui_list_set_block_title_alignment(self._handle, C.c_uint(_align_value(align)))

    def set_selected(self, idx: Optional[int]) -> None:
        self._lib.ratatui_list_set_selected(self._handle, -1 if idx is None else int(idx))

    def set_highlight_style(self, style: Style) -> None:
        self._lib.ratatui_list_set_highlight_style(self._handle, style.to_ffi())

    def set_highlight_symbol(self, sym: Optional[str]) -> None:
        s = None if sym is None else sym.encode("utf-8")
        self._lib.ratatui_list_set_highlight_symbol(self._handle, s)

    # Advanced list configuration (v0.2.0+)
    def set_direction(self, vertical: bool = True) -> None:
        if hasattr(self._lib, 'ratatui_list_set_direction'):
            self._lib.ratatui_list_set_direction(self._handle, 0 if vertical else 1)

    def set_scroll_offset(self, offset: int) -> None:
        if hasattr(self._lib, 'ratatui_list_set_scroll_offset'):
            self._lib.ratatui_list_set_scroll_offset(self._handle, C.c_uint16(int(offset)))

    def append_items_spans(self, items: Sequence[Sequence[tuple[str, "Style"]]]) -> None:
        if not hasattr(self._lib, 'ratatui_list_append_items_spans'):
            for spans in items:
                for text, style in spans:
                    self.append_item(text, style)
            return
        arr, _keep = _build_lines_spans(items)
        self._lib.ratatui_list_append_items_spans(self._handle, arr, len(arr))

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

    def set_block_title_alignment(self, align: str | int) -> None:
        if hasattr(self._lib, 'ratatui_table_set_block_title_alignment'):
            self._lib.ratatui_table_set_block_title_alignment(self._handle, C.c_uint(_align_value(align)))

    def set_selected(self, idx: Optional[int]) -> None:
        self._lib.ratatui_table_set_selected(self._handle, -1 if idx is None else int(idx))

    def set_row_highlight_style(self, style: Style) -> None:
        self._lib.ratatui_table_set_row_highlight_style(self._handle, style.to_ffi())

    def set_highlight_symbol(self, sym: Optional[str]) -> None:
        s = None if sym is None else sym.encode("utf-8")
        self._lib.ratatui_table_set_highlight_symbol(self._handle, s)

    # Advanced table configuration (v0.2.0+)
    def set_widths(self, widths: Iterable[int]) -> None:
        if hasattr(self._lib, 'ratatui_table_set_widths'):
            vals = list(widths)
            arr = (C.c_uint16 * len(vals))(*vals)
            self._lib.ratatui_table_set_widths(self._handle, arr, len(arr))

    def set_widths_percentages(self, percentages: Iterable[int]) -> None:
        if hasattr(self._lib, 'ratatui_table_set_widths_percentages'):
            vals = list(percentages)
            arr = (C.c_uint16 * len(vals))(*vals)
            self._lib.ratatui_table_set_widths_percentages(self._handle, arr, len(arr))

    def set_row_height(self, height: int) -> None:
        if hasattr(self._lib, 'ratatui_table_set_row_height'):
            self._lib.ratatui_table_set_row_height(self._handle, C.c_uint16(int(height)))

    def set_column_spacing(self, spacing: int) -> None:
        if hasattr(self._lib, 'ratatui_table_set_column_spacing'):
            self._lib.ratatui_table_set_column_spacing(self._handle, C.c_uint16(int(spacing)))

    def set_highlight_spacing(self, spacing_mode: int) -> None:
        if hasattr(self._lib, 'ratatui_table_set_highlight_spacing'):
            self._lib.ratatui_table_set_highlight_spacing(self._handle, C.c_uint(int(spacing_mode)))

    def set_headers_spans(self, headers: Sequence[Sequence[tuple[str, "Style"]]]) -> None:
        if not hasattr(self._lib, 'ratatui_table_set_headers_spans'):
            self.set_headers([''.join(text for text, _ in line) for line in headers])
            return
        arr, _keep = _build_lines_spans(headers)
        self._lib.ratatui_table_set_headers_spans(self._handle, arr, len(arr))

    def append_row_spans(self, cells: Sequence[Sequence[tuple[str, "Style"]]]) -> None:
        if not hasattr(self._lib, 'ratatui_table_append_row_spans'):
            self.append_row([''.join(text for text, _ in spans) for spans in cells])
            return
        arr, _keep = _build_lines_spans(cells)
        self._lib.ratatui_table_append_row_spans(self._handle, arr, len(arr))

    def append_row_cells_lines(self, row: Sequence[Sequence[Sequence[tuple[str, "Style"]]]]) -> None:
        if not hasattr(self._lib, 'ratatui_table_append_row_cells_lines'):
            # degrade to single-line cells by flattening each cell
            self.append_row([''.join(text for line in cell for text, _ in line) for cell in row])
            return
        # Build [FfiCellLines]
        FfiLineSpans = load_library().FfiLineSpans
        FfiCellLines = load_library().FfiCellLines
        cell_arrays = []
        keep: list[bytes] = []
        for cell in row:
            lines_arr, keep2 = _build_lines_spans(cell)
            cell_arrays.append((lines_arr, keep2))
            keep.extend(keep2)
        out = (FfiCellLines * len(row))()
        for i, (lines_arr, _k) in enumerate(cell_arrays):
            out[i] = FfiCellLines(lines_arr, len(lines_arr))
        self._lib.ratatui_table_append_row_cells_lines(self._handle, out, len(out))

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

    def set_block_title_alignment(self, align: str | int) -> None:
        if hasattr(self._lib, 'ratatui_gauge_set_block_title_alignment'):
            self._lib.ratatui_gauge_set_block_title_alignment(self._handle, C.c_uint(_align_value(align)))

    def set_styles(self, style: Style, label_style: Style, gauge_style: Style) -> None:
        if hasattr(self._lib, 'ratatui_gauge_set_styles'):
            self._lib.ratatui_gauge_set_styles(self._handle, style.to_ffi(), label_style.to_ffi(), gauge_style.to_ffi())

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

    def set_block_title_alignment(self, align: str | int) -> None:
        if hasattr(self._lib, 'ratatui_tabs_set_block_title_alignment'):
            self._lib.ratatui_tabs_set_block_title_alignment(self._handle, C.c_uint(_align_value(align)))

    def clear_titles(self) -> None:
        if hasattr(self._lib, 'ratatui_tabs_clear_titles'):
            self._lib.ratatui_tabs_clear_titles(self._handle)

    def set_divider(self, s: str) -> None:
        if hasattr(self._lib, 'ratatui_tabs_set_divider'):
            self._lib.ratatui_tabs_set_divider(self._handle, s.encode('utf-8'))

    def set_styles(self, unselected: Style, selected: Style) -> None:
        if hasattr(self._lib, 'ratatui_tabs_set_styles'):
            self._lib.ratatui_tabs_set_styles(self._handle, unselected.to_ffi(), selected.to_ffi())

    def set_titles_spans(self, titles: Sequence[Sequence[tuple[str, "Style"]]]) -> None:
        if not hasattr(self._lib, 'ratatui_tabs_set_titles_spans'):
            self.set_titles([''.join(text for text, _ in line) for line in titles])
            return
        arr, _keep = _build_lines_spans(titles)
        self._lib.ratatui_tabs_set_titles_spans(self._handle, arr, len(arr))

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

    def set_block_title_alignment(self, align: str | int) -> None:
        if hasattr(self._lib, 'ratatui_barchart_set_block_title_alignment'):
            self._lib.ratatui_barchart_set_block_title_alignment(self._handle, C.c_uint(_align_value(align)))

    def set_bar_width(self, width: int) -> None:
        if hasattr(self._lib, 'ratatui_barchart_set_bar_width'):
            self._lib.ratatui_barchart_set_bar_width(self._handle, C.c_uint16(int(width)))

    def set_bar_gap(self, gap: int) -> None:
        if hasattr(self._lib, 'ratatui_barchart_set_bar_gap'):
            self._lib.ratatui_barchart_set_bar_gap(self._handle, C.c_uint16(int(gap)))

    def set_styles(self, bar: Style, value: Style, label: Style) -> None:
        if hasattr(self._lib, 'ratatui_barchart_set_styles'):
            self._lib.ratatui_barchart_set_styles(self._handle, bar.to_ffi(), value.to_ffi(), label.to_ffi())

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

    def set_block_title_alignment(self, align: str | int) -> None:
        if hasattr(self._lib, 'ratatui_sparkline_set_block_title_alignment'):
            self._lib.ratatui_sparkline_set_block_title_alignment(self._handle, C.c_uint(_align_value(align)))

    def set_max(self, max_value: int) -> None:
        if hasattr(self._lib, 'ratatui_sparkline_set_max'):
            self._lib.ratatui_sparkline_set_max(self._handle, C.c_uint64(int(max_value)))

    def set_style(self, style: Style) -> None:
        if hasattr(self._lib, 'ratatui_sparkline_set_style'):
            self._lib.ratatui_sparkline_set_style(self._handle, style.to_ffi())

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

    def set_block_title_alignment(self, align: str | int) -> None:
        if hasattr(self._lib, 'ratatui_scrollbar_set_block_title_alignment'):
            self._lib.ratatui_scrollbar_set_block_title_alignment(self._handle, C.c_uint(_align_value(align)))

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

    def set_bounds(self, x_min: float, x_max: float, y_min: float, y_max: float) -> None:
        if hasattr(self._lib, 'ratatui_chart_set_bounds'):
            self._lib.ratatui_chart_set_bounds(self._handle, C.c_double(x_min), C.c_double(x_max), C.c_double(y_min), C.c_double(y_max))

    def set_style(self, style: Style) -> None:
        if hasattr(self._lib, 'ratatui_chart_set_style'):
            self._lib.ratatui_chart_set_style(self._handle, style.to_ffi())

    def set_axis_styles(self, x_style: Style, y_style: Style) -> None:
        if hasattr(self._lib, 'ratatui_chart_set_axis_styles'):
            self._lib.ratatui_chart_set_axis_styles(self._handle, x_style.to_ffi(), y_style.to_ffi())

    def set_legend_position(self, pos: int) -> None:
        if hasattr(self._lib, 'ratatui_chart_set_legend_position'):
            self._lib.ratatui_chart_set_legend_position(self._handle, C.c_uint(int(pos)))

    def set_hidden_legend_constraints(self, kinds2: Sequence[int], values2: Sequence[int]) -> None:
        if hasattr(self._lib, 'ratatui_chart_set_hidden_legend_constraints'):
            k = (C.c_uint32 * len(kinds2))(*[int(x) for x in kinds2])
            v = (C.c_uint16 * len(values2))(*[int(x) for x in values2])
            self._lib.ratatui_chart_set_hidden_legend_constraints(self._handle, k, v)

    def set_labels_alignment(self, x_align: str | int, y_align: str | int) -> None:
        if hasattr(self._lib, 'ratatui_chart_set_labels_alignment'):
            self._lib.ratatui_chart_set_labels_alignment(self._handle, C.c_uint(_align_value(x_align)), C.c_uint(_align_value(y_align)))

    def set_x_labels_spans(self, labels: Sequence[Sequence[tuple[str, "Style"]]]) -> None:
        if not hasattr(self._lib, 'ratatui_chart_set_x_labels_spans'):
            return
        arr, _keep = _build_lines_spans(labels)
        self._lib.ratatui_chart_set_x_labels_spans(self._handle, arr, len(arr))

    def set_y_labels_spans(self, labels: Sequence[Sequence[tuple[str, "Style"]]]) -> None:
        if not hasattr(self._lib, 'ratatui_chart_set_y_labels_spans'):
            return
        arr, _keep = _build_lines_spans(labels)
        self._lib.ratatui_chart_set_y_labels_spans(self._handle, arr, len(arr))

    def set_block_title(self, title: Optional[str], show_border: bool = True) -> None:
        t = None if title is None else title.encode("utf-8")
        self._lib.ratatui_chart_set_block_title(self._handle, t, bool(show_border))

    def set_block_title_alignment(self, align: str | int) -> None:
        if hasattr(self._lib, 'ratatui_chart_set_block_title_alignment'):
            self._lib.ratatui_chart_set_block_title_alignment(self._handle, C.c_uint(_align_value(align)))

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


def headless_render_logo(width: int, height: int) -> str:
    lib = load_library()
    if not hasattr(lib, 'ratatui_headless_render_ratatuilogo'):
        return ""
    out = C.c_char_p()
    ok = lib.ratatui_headless_render_ratatuilogo(C.c_uint16(width), C.c_uint16(height), C.byref(out))
    if not ok or not out:
        return ""
    try:
        return C.cast(out, C.c_char_p).value.decode('utf-8', errors='replace')
    finally:
        lib.ratatui_string_free(out)


def headless_render_logo_sized(width: int, height: int, size: int) -> str:
    lib = load_library()
    if not hasattr(lib, 'ratatui_headless_render_ratatuilogo_sized'):
        return ""
    out = C.c_char_p()
    ok = lib.ratatui_headless_render_ratatuilogo_sized(C.c_uint16(width), C.c_uint16(height), C.c_uint32(int(size)), C.byref(out))
    if not ok or not out:
        return ""
    try:
        return C.cast(out, C.c_char_p).value.decode('utf-8', errors='replace')
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


def _align_value(align: str | int) -> int:
    if isinstance(align, int):
        return align
    a = align.strip().lower()
    if a.startswith('l'):
        return FFI_ALIGN['Left']
    if a.startswith('c'):
        return FFI_ALIGN['Center']
    if a.startswith('r'):
        return FFI_ALIGN['Right']
    raise ValueError(f"invalid alignment: {align}")


class Frame:
    def __init__(self, term: Terminal):
        self._term = term
        self._cmds: _List[DrawCmd] = []
        self.ok: Optional[bool] = None

    # mirror DrawCmd helpers for convenience
    def paragraph(self, p: Paragraph, rect: RectLike) -> None:
        self._cmds.append(DrawCmd.paragraph(p, rect))

    def list(self, lst: "List", rect: RectLike) -> None:
        self._cmds.append(DrawCmd.list(lst, rect))

    def table(self, t: "Table", rect: RectLike) -> None:
        self._cmds.append(DrawCmd.table(t, rect))

    def gauge(self, g: "Gauge", rect: RectLike) -> None:
        self._cmds.append(DrawCmd.gauge(g, rect))

    def tabs(self, t: "Tabs", rect: RectLike) -> None:
        self._cmds.append(DrawCmd.tabs(t, rect))

    def barchart(self, b: "BarChart", rect: RectLike) -> None:
        self._cmds.append(DrawCmd.barchart(b, rect))

    def sparkline(self, s: "Sparkline", rect: RectLike) -> None:
        self._cmds.append(DrawCmd.sparkline(s, rect))

    def chart(self, c: "Chart", rect: RectLike) -> None:
        self._cmds.append(DrawCmd.chart(c, rect))

    def canvas(self, cv: "Canvas", rect: RectLike) -> None:
        self._cmds.append(DrawCmd(FFI_WIDGET_KIND.get("Canvas", 0), cv._handle, _ffi_rect(rect), owner=cv))


class Canvas:
    def __init__(self, x_min: float = 0.0, x_max: float = 1.0, y_min: float = 0.0, y_max: float = 1.0):
        self._lib = load_library()
        if not hasattr(self._lib, 'ratatui_canvas_new'):
            raise RuntimeError('ratatui_ffi lacks Canvas APIs')
        ptr = self._lib.ratatui_canvas_new(C.c_double(x_min), C.c_double(x_max), C.c_double(y_min), C.c_double(y_max))
        if not ptr:
            raise RuntimeError('ratatui_canvas_new failed')
        self._handle = C.c_void_p(ptr)

    def set_bounds(self, x_min: float, x_max: float, y_min: float, y_max: float) -> "Canvas":
        self._lib.ratatui_canvas_set_bounds(self._handle, C.c_double(x_min), C.c_double(x_max), C.c_double(y_min), C.c_double(y_max))
        return self

    def set_background_color(self, color: int) -> "Canvas":
        self._lib.ratatui_canvas_set_background_color(self._handle, C.c_uint32(int(color)))
        return self

    def set_block_title(self, title: Optional[str], show_border: bool = True) -> "Canvas":
        t = None if title is None else title.encode('utf-8')
        self._lib.ratatui_canvas_set_block_title(self._handle, t, bool(show_border))
        return self

    def set_block_title_alignment(self, align: str | int) -> "Canvas":
        if hasattr(self._lib, 'ratatui_canvas_set_block_title_alignment'):
            self._lib.ratatui_canvas_set_block_title_alignment(self._handle, C.c_uint(_align_value(align)))
        return self

    def set_marker(self, marker: int) -> "Canvas":
        self._lib.ratatui_canvas_set_marker(self._handle, C.c_uint32(int(marker)))
        return self

    def add_line(self, x1: float, y1: float, x2: float, y2: float, style: Optional[Style] = None) -> None:
        self._lib.ratatui_canvas_add_line(self._handle, C.c_double(x1), C.c_double(y1), C.c_double(x2), C.c_double(y2), (style or Style()).to_ffi())

    def add_rect(self, x: float, y: float, w: float, h: float, style: Optional[Style] = None, filled: bool = False) -> None:
        self._lib.ratatui_canvas_add_rect(self._handle, C.c_double(x), C.c_double(y), C.c_double(w), C.c_double(h), (style or Style()).to_ffi(), bool(filled))

    def add_points(self, points: Sequence[Tuple[float, float]], style: Optional[Style] = None, marker: int = 0) -> None:
        vals: list[float] = []
        for (x, y) in points:
            vals.extend([float(x), float(y)])
        arr = (C.c_double * len(vals))(*vals)
        self._lib.ratatui_canvas_add_points(self._handle, arr, len(points), (style or Style()).to_ffi(), C.c_uint32(int(marker)))

    def close(self) -> None:
        if getattr(self, '_handle', None):
            self._lib.ratatui_canvas_free(self._handle)
            self._handle = None

    def __del__(self):
        try:
            self.close()
        except Exception:
            pass


def headless_render_canvas(width: int, height: int, canvas: Canvas) -> str:
    lib = canvas._lib
    out = C.c_char_p()
    ok = lib.ratatui_headless_render_canvas(C.c_uint16(width), C.c_uint16(height), canvas._handle, C.byref(out))
    if not ok or not out:
        return ""
    try:
        return C.cast(out, C.c_char_p).value.decode('utf-8', errors='replace')
    finally:
        lib.ratatui_string_free(out)

    def extend(self, cmds: Sequence[DrawCmd]) -> None:
        self._cmds.extend(cmds)

    def __enter__(self) -> "Frame":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        if exc_type is None:
            self.ok = self._term.draw_frame(self._cmds)


# Headless frame helpers
def headless_render_frame(width: int, height: int, cmds: Sequence[DrawCmd]) -> str:
    lib = load_library()
    if not hasattr(lib, 'ratatui_headless_render_frame'):
        return ""
    FfiDrawCmd = lib.FfiDrawCmd
    arr = (FfiDrawCmd * len(cmds))()
    for i, cmd in enumerate(cmds):
        arr[i] = FfiDrawCmd(cmd.kind, cmd.handle, cmd.rect)
    out = C.c_char_p()
    ok = lib.ratatui_headless_render_frame(C.c_uint16(width), C.c_uint16(height), arr, len(cmds), C.byref(out))
    if not ok or not out:
        return ""
    try:
        return C.cast(out, C.c_char_p).value.decode('utf-8', errors='replace')
    finally:
        lib.ratatui_string_free(out)


def headless_render_frame_styles_ex(width: int, height: int, cmds: Sequence[DrawCmd]) -> str:
    lib = load_library()
    if not hasattr(lib, 'ratatui_headless_render_frame_styles_ex'):
        return ""
    FfiDrawCmd = lib.FfiDrawCmd
    arr = (FfiDrawCmd * len(cmds))()
    for i, cmd in enumerate(cmds):
        arr[i] = FfiDrawCmd(cmd.kind, cmd.handle, cmd.rect)
    out = C.c_char_p()
    ok = lib.ratatui_headless_render_frame_styles_ex(C.c_uint16(width), C.c_uint16(height), arr, len(cmds), C.byref(out))
    if not ok or not out:
        return ""
    try:
        return C.cast(out, C.c_char_p).value.decode('utf-8', errors='replace')
    finally:
        lib.ratatui_string_free(out)


def headless_render_frame_cells(width: int, height: int, cmds: Sequence[DrawCmd]):
    lib = load_library()
    if not hasattr(lib, 'ratatui_headless_render_frame_cells'):
        return []
    FfiDrawCmd = lib.FfiDrawCmd
    arr = (FfiDrawCmd * len(cmds))()
    for i, cmd in enumerate(cmds):
        arr[i] = FfiDrawCmd(cmd.kind, cmd.handle, cmd.rect)
    cap = int(width) * int(height)
    Cell = lib.FfiCellInfo
    buf = (Cell * cap)()
    n = int(lib.ratatui_headless_render_frame_cells(C.c_uint16(width), C.c_uint16(height), arr, len(cmds), buf, cap))
    out = []
    for i in range(min(n, cap)):
        c = buf[i]
        out.append({"ch": int(c.ch), "fg": int(c.fg), "bg": int(c.bg), "mods": int(c.mods)})
    return out


def _build_spans(spans: Sequence[tuple[str, "Style"]]):
    # Build an array[FfiSpan] and keep UTF-8 bytes alive across the call
    bufs = [text.encode('utf-8') for text, _ in spans]
    arr = (load_library().FfiSpan * len(spans))()
    for i, (buf, (_, style)) in enumerate(zip(bufs, spans)):
        arr[i] = load_library().FfiSpan(buf, style.to_ffi())
    return arr, bufs


def _build_lines_spans(lines: Sequence[Sequence[tuple[str, "Style"]]]):
    # Build nested arrays: [FfiLineSpans] where each has spans pointer + len
    span_arrays = []
    keep: list[bytes] = []
    FfiSpan = load_library().FfiSpan
    FfiLineSpans = load_library().FfiLineSpans
    for spans in lines:
        bufs = [text.encode('utf-8') for text, _ in spans]
        arr = (FfiSpan * len(spans))()
        for i, (buf, (_, style)) in enumerate(zip(bufs, spans)):
            arr[i] = FfiSpan(buf, style.to_ffi())
        span_arrays.append((arr, bufs))
        keep.extend(bufs)
    out = (FfiLineSpans * len(lines))()
    for i, (arr, _bufs) in enumerate(span_arrays):
        out[i] = FfiLineSpans(arr, len(arr))
    return out, keep


# Terminal context managers for raw and alt modes
class _RawMode:
    def __enter__(self):
        load_library().ratatui_terminal_enable_raw()
        return self
    def __exit__(self, exc_type, exc, tb):
        load_library().ratatui_terminal_disable_raw()


class _AltScreen:
    def __enter__(self):
        load_library().ratatui_terminal_enter_alt()
        return self
    def __exit__(self, exc_type, exc, tb):
        load_library().ratatui_terminal_leave_alt()


def raw_mode():
    return _RawMode()


def alt_screen():
    return _AltScreen()


# One-stop terminal session: creates Terminal, toggles raw/alt, cleans up.
class _TerminalSession:
    def __init__(self, *, raw: bool = True, alt: bool = True, clear: bool = False):
        self._raw = bool(raw)
        self._alt = bool(alt)
        self._clear = bool(clear)
        self.term: Optional[Terminal] = None

    def __enter__(self) -> Terminal:
        t = Terminal()
        # Enable modes if available; keep it minimal and fast.
        if self._raw and hasattr(t._lib, 'ratatui_terminal_enable_raw'):
            t.enable_raw()
        if self._alt and hasattr(t._lib, 'ratatui_terminal_enter_alt'):
            t.enter_alt()
        if self._clear:
            try:
                t.clear()
            except Exception:
                pass
        self.term = t
        return t

    def __exit__(self, exc_type, exc, tb):
        t = self.term
        if t is not None:
            try:
                if self._alt and hasattr(t._lib, 'ratatui_terminal_leave_alt'):
                    t.leave_alt()
            finally:
                try:
                    if self._raw and hasattr(t._lib, 'ratatui_terminal_disable_raw'):
                        t.disable_raw()
                finally:
                    t.close()


def terminal_session(*, raw: bool = True, alt: bool = True, clear: bool = False) -> _TerminalSession:
    return _TerminalSession(raw=raw, alt=alt, clear=clear)


# Color helpers (fast integer encoding; use FFI if available for parity)
def rgb(r: int, g: int, b: int) -> int:
    lib = load_library()
    if hasattr(lib, 'ratatui_color_rgb'):
        return int(lib.ratatui_color_rgb(C.c_uint8(int(r)), C.c_uint8(int(g)), C.c_uint8(int(b))))
    return (0x80000000 | ((int(r) & 0xFF) << 16) | ((int(g) & 0xFF) << 8) | (int(b) & 0xFF))


def color_indexed(i: int) -> int:
    lib = load_library()
    if hasattr(lib, 'ratatui_color_indexed'):
        return int(lib.ratatui_color_indexed(C.c_uint8(int(i))))
    return (0x40000000 | (int(i) & 0xFF))


# Stateful list and table
class ListState:
    def __init__(self):
        lib = load_library()
        if not hasattr(lib, 'ratatui_list_state_new'):
            raise RuntimeError('ratatui_ffi lacks ListState APIs')
        ptr = lib.ratatui_list_state_new()
        if not ptr:
            raise RuntimeError('ratatui_list_state_new failed')
        self._lib = lib
        self._handle = C.c_void_p(ptr)

    def set_selected(self, idx: Optional[int]) -> None:
        self._lib.ratatui_list_state_set_selected(self._handle, -1 if idx is None else int(idx))

    def set_offset(self, off: int) -> None:
        self._lib.ratatui_list_state_set_offset(self._handle, C.c_uint16(int(off)))

    def close(self) -> None:
        if getattr(self, '_handle', None):
            self._lib.ratatui_list_state_free(self._handle)
            self._handle = None

    def __del__(self):
        try:
            self.close()
        except Exception:
            pass


class TableState:
    def __init__(self):
        lib = load_library()
        if not hasattr(lib, 'ratatui_table_state_new'):
            raise RuntimeError('ratatui_ffi lacks TableState APIs')
        ptr = lib.ratatui_table_state_new()
        if not ptr:
            raise RuntimeError('ratatui_table_state_new failed')
        self._lib = lib
        self._handle = C.c_void_p(ptr)

    def set_selected(self, idx: Optional[int]) -> None:
        self._lib.ratatui_table_state_set_selected(self._handle, -1 if idx is None else int(idx))

    def set_offset(self, off: int) -> None:
        self._lib.ratatui_table_state_set_offset(self._handle, C.c_uint16(int(off)))

    def close(self) -> None:
        if getattr(self, '_handle', None):
            self._lib.ratatui_table_state_free(self._handle)
            self._handle = None

    def __del__(self):
        try:
            self.close()
        except Exception:
            pass


# Terminal helpers for stateful widgets
def headless_render_list_state(width: int, height: int, lst: List, state: ListState) -> str:
    lib = lst._lib
    out = C.c_char_p()
    ok = lib.ratatui_headless_render_list_state(C.c_uint16(width), C.c_uint16(height), lst._handle, state._handle, C.byref(out))
    if not ok or not out:
        return ""
    try:
        return C.cast(out, C.c_char_p).value.decode("utf-8", errors="replace")
    finally:
        lib.ratatui_string_free(out)


def _term_draw_list_state(term: Terminal, lst: List, state: ListState, rect: RectLike) -> bool:
    r = _ffi_rect(rect)
    return bool(term._lib.ratatui_terminal_draw_list_state_in(term._handle, lst._handle, state._handle, r))


def _term_draw_table_state(term: Terminal, tbl: Table, state: TableState, rect: RectLike) -> bool:
    r = _ffi_rect(rect)
    return bool(term._lib.ratatui_terminal_draw_table_state_in(term._handle, tbl._handle, state._handle, r))


# Attach methods to Terminal without breaking API surface
setattr(Terminal, 'draw_list_state', lambda self, lst, state, rect: _term_draw_list_state(self, lst, state, rect))
setattr(Terminal, 'draw_table_state', lambda self, tbl, state, rect: _term_draw_table_state(self, tbl, state, rect))
