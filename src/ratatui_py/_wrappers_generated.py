# GENERATED from bindings.json by tools/gen_wrappers.py — DO NOT EDIT. Regenerate with `just gen`.

"""Generated ergonomic wrappers (Stage 2 of the codegen pipeline).

Methods here ADD to the hand-written wrapper classes in `wrappers.py`. Call
`apply_generated()` once (done at import time by `wrappers.py`) to attach every
method onto its target class WHERE THE HAND CLASS LACKS THE NAME — hand-written
methods always win (collisions are skipped at generation time and reported in
tools/residue.txt). `LineGauge` is fully generated (no hand class exists).

Marshaling mirrors `wrappers.py` exactly: `_build_spans` / `_build_lines_spans`
for span arrays, `Style.to_ffi()` for styles, UTF-8 encode for char*, out-string
decode + `ratatui_string_free` for headless renders.
"""
from __future__ import annotations
import ctypes as C
from typing import Optional, Sequence, Tuple

from ._ffi import load_library
from .wrappers import (
    Style,
    Terminal,
    Paragraph,
    List,
    Table,
    Gauge,
    Tabs,
    BarChart,
    Sparkline,
    Scrollbar,
    Chart,
    Canvas,
    _build_spans,
    _build_lines_spans,
    _ffi_rect,
)
from .types import RectLike


# ----- LineGauge (fully generated; no hand class) -----

class LineGauge:
    """Generated ergonomic wrapper for the LineGauge widget."""

    def __init__(self):
        self._lib = load_library()
        if not hasattr(self._lib, 'ratatui_linegauge_new'):
            raise RuntimeError("ratatui_ffi lacks LineGauge APIs")
        ptr = self._lib.ratatui_linegauge_new()
        if not ptr:
            raise RuntimeError("ratatui_linegauge_new failed")
        self._handle = C.c_void_p(ptr)

    def set_block_adv(self, borders_bits, border_type, pad_l=0, pad_t=0, pad_r=0, pad_b=0, title_spans=()) -> "LineGauge":
        arr, _keep = _build_spans(title_spans)
        self._lib.ratatui_linegauge_set_block_adv(self._handle, C.c_uint8(int(borders_bits)), C.c_uint32(int(border_type)),
            C.c_uint16(int(pad_l)), C.c_uint16(int(pad_t)),
            C.c_uint16(int(pad_r)), C.c_uint16(int(pad_b)),
            arr, len(arr))
        return self

    def set_block_title(self, title_utf8, show_border=True) -> "LineGauge":
        _s = None if title_utf8 is None else title_utf8.encode('utf-8')
        self._lib.ratatui_linegauge_set_block_title(self._handle, _s, bool(show_border))
        return self

    def set_block_title_alignment(self, align) -> "LineGauge":
        self._lib.ratatui_linegauge_set_block_title_alignment(self._handle, C.c_uint32(int(align)))
        return self

    def set_block_title_spans(self, spans, show_border=True) -> "LineGauge":
        arr, _keep = _build_spans(spans)
        self._lib.ratatui_linegauge_set_block_title_spans(self._handle, arr, len(arr), bool(show_border))
        return self

    def set_label(self, label_utf8) -> "LineGauge":
        _s = None if label_utf8 is None else label_utf8.encode('utf-8')
        self._lib.ratatui_linegauge_set_label(self._handle, _s)
        return self

    def set_label_spans(self, spans) -> "LineGauge":
        arr, _keep = _build_spans(spans)
        self._lib.ratatui_linegauge_set_label_spans(self._handle, arr, len(arr))
        return self

    def set_ratio(self, ratio) -> "LineGauge":
        self._lib.ratatui_linegauge_set_ratio(self._handle, C.c_float(float(ratio)))
        return self

    def set_style(self, style) -> "LineGauge":
        self._lib.ratatui_linegauge_set_style(self._handle, style.to_ffi())
        return self

    def close(self) -> None:
        if getattr(self, '_handle', None):
            self._lib.ratatui_linegauge_free(self._handle)
            self._handle = None

    def __del__(self):
        try:
            self.close()
        except Exception:
            pass


# ----- Generated widget methods (bound onto hand classes) -----

def _gen_BarChart_set_block_adv(self, borders_bits, border_type, pad_l=0, pad_t=0, pad_r=0, pad_b=0, title_spans=()):
    arr, _keep = _build_spans(title_spans)
    self._lib.ratatui_barchart_set_block_adv(self._handle, C.c_uint8(int(borders_bits)), C.c_uint32(int(border_type)),
        C.c_uint16(int(pad_l)), C.c_uint16(int(pad_t)),
        C.c_uint16(int(pad_r)), C.c_uint16(int(pad_b)),
        arr, len(arr))
    return self

def _gen_BarChart_set_block_title_spans(self, spans, show_border=True):
    arr, _keep = _build_spans(spans)
    self._lib.ratatui_barchart_set_block_title_spans(self._handle, arr, len(arr), bool(show_border))
    return self

def _gen_BarChart_set_labels_spans(self, lines):
    arr, _keep = _build_lines_spans(lines)
    self._lib.ratatui_barchart_set_labels_spans(self._handle, arr, len(arr))
    return self

def _gen_Canvas_set_block_adv(self, borders_bits, border_type, pad_l=0, pad_t=0, pad_r=0, pad_b=0, title_spans=()):
    arr, _keep = _build_spans(title_spans)
    self._lib.ratatui_canvas_set_block_adv(self._handle, C.c_uint8(int(borders_bits)), C.c_uint32(int(border_type)),
        C.c_uint16(int(pad_l)), C.c_uint16(int(pad_t)),
        C.c_uint16(int(pad_r)), C.c_uint16(int(pad_b)),
        arr, len(arr))
    return self

def _gen_Canvas_set_block_title_spans(self, spans, show_border=True):
    arr, _keep = _build_spans(spans)
    self._lib.ratatui_canvas_set_block_title_spans(self._handle, arr, len(arr), bool(show_border))
    return self

def _gen_Chart_add_dataset_with_type(self, name, points, kind, style=None):
    n = name.encode('utf-8')
    flat = []
    for (x, y) in points:
        flat.extend([float(x), float(y)])
    arr = (C.c_double * len(flat))(*flat)
    self._lib.ratatui_chart_add_dataset_with_type(self._handle, n, arr, len(points), (style or Style()).to_ffi(), C.c_uint32(int(kind)))

def _gen_Chart_add_datasets(self, specs):
    FfiChartDatasetSpec = self._lib.FfiChartDatasetSpec
    keep = []
    arr = (FfiChartDatasetSpec * len(specs))()
    for i, (name, points, kind, style) in enumerate(specs):
        n = name.encode('utf-8')
        keep.append(n)
        flat = []
        for (x, y) in points:
            flat.extend([float(x), float(y)])
        pts = (C.c_double * len(flat))(*flat)
        keep.append(pts)
        st = (style or Style()).to_ffi()
        arr[i] = FfiChartDatasetSpec(n, pts, len(points), st, C.c_uint32(int(kind)))
    self._lib.ratatui_chart_add_datasets(self._handle, arr, len(arr))

def _gen_Chart_set_block_adv(self, borders_bits, border_type, pad_l=0, pad_t=0, pad_r=0, pad_b=0, title_spans=()):
    arr, _keep = _build_spans(title_spans)
    self._lib.ratatui_chart_set_block_adv(self._handle, C.c_uint8(int(borders_bits)), C.c_uint32(int(border_type)),
        C.c_uint16(int(pad_l)), C.c_uint16(int(pad_t)),
        C.c_uint16(int(pad_r)), C.c_uint16(int(pad_b)),
        arr, len(arr))
    return self

def _gen_Chart_set_block_title_spans(self, spans, show_border=True):
    arr, _keep = _build_spans(spans)
    self._lib.ratatui_chart_set_block_title_spans(self._handle, arr, len(arr), bool(show_border))
    return self

def _gen_Gauge_set_block_adv(self, borders_bits, border_type, pad_l=0, pad_t=0, pad_r=0, pad_b=0, title_spans=()):
    arr, _keep = _build_spans(title_spans)
    self._lib.ratatui_gauge_set_block_adv(self._handle, C.c_uint8(int(borders_bits)), C.c_uint32(int(border_type)),
        C.c_uint16(int(pad_l)), C.c_uint16(int(pad_t)),
        C.c_uint16(int(pad_r)), C.c_uint16(int(pad_b)),
        arr, len(arr))
    return self

def _gen_Gauge_set_block_title_spans(self, spans, show_border=True):
    arr, _keep = _build_spans(spans)
    self._lib.ratatui_gauge_set_block_title_spans(self._handle, arr, len(arr), bool(show_border))
    return self

def _gen_Gauge_set_label(self, label):
    _s = None if label is None else label.encode('utf-8')
    self._lib.ratatui_gauge_set_label(self._handle, _s)
    return self

def _gen_Gauge_set_label_spans(self, spans):
    arr, _keep = _build_spans(spans)
    self._lib.ratatui_gauge_set_label_spans(self._handle, arr, len(arr))
    return self

def _gen_Gauge_set_ratio(self, ratio):
    self._lib.ratatui_gauge_set_ratio(self._handle, C.c_float(float(ratio)))
    return self

def _gen_List_append_item_spans(self, spans):
    arr, _keep = _build_spans(spans)
    self._lib.ratatui_list_append_item_spans(self._handle, arr, len(arr))

def _gen_List_set_block_adv(self, borders_bits, border_type, pad_l=0, pad_t=0, pad_r=0, pad_b=0, title_spans=()):
    arr, _keep = _build_spans(title_spans)
    self._lib.ratatui_list_set_block_adv(self._handle, C.c_uint8(int(borders_bits)), C.c_uint32(int(border_type)),
        C.c_uint16(int(pad_l)), C.c_uint16(int(pad_t)),
        C.c_uint16(int(pad_r)), C.c_uint16(int(pad_b)),
        arr, len(arr))
    return self

def _gen_List_set_block_title_spans(self, spans, show_border=True):
    arr, _keep = _build_spans(spans)
    self._lib.ratatui_list_set_block_title_spans(self._handle, arr, len(arr), bool(show_border))
    return self

def _gen_List_set_highlight_spacing(self, spacing):
    self._lib.ratatui_list_set_highlight_spacing(self._handle, C.c_uint32(int(spacing)))
    return self

def _gen_Paragraph_set_block_adv(self, borders_bits, border_type, pad_l=0, pad_t=0, pad_r=0, pad_b=0, title_spans=()):
    arr, _keep = _build_spans(title_spans)
    self._lib.ratatui_paragraph_set_block_adv(self._handle, C.c_uint8(int(borders_bits)), C.c_uint32(int(border_type)),
        C.c_uint16(int(pad_l)), C.c_uint16(int(pad_t)),
        C.c_uint16(int(pad_r)), C.c_uint16(int(pad_b)),
        arr, len(arr))
    return self

def _gen_Paragraph_set_block_title_spans(self, spans, show_border=True):
    arr, _keep = _build_spans(spans)
    self._lib.ratatui_paragraph_set_block_title_spans(self._handle, arr, len(arr), bool(show_border))
    return self

def _gen_Scrollbar_set_block_adv(self, borders_bits, border_type, pad_l=0, pad_t=0, pad_r=0, pad_b=0, title_spans=()):
    arr, _keep = _build_spans(title_spans)
    self._lib.ratatui_scrollbar_set_block_adv(self._handle, C.c_uint8(int(borders_bits)), C.c_uint32(int(border_type)),
        C.c_uint16(int(pad_l)), C.c_uint16(int(pad_t)),
        C.c_uint16(int(pad_r)), C.c_uint16(int(pad_b)),
        arr, len(arr))
    return self

def _gen_Scrollbar_set_block_title_spans(self, spans, show_border=True):
    arr, _keep = _build_spans(spans)
    self._lib.ratatui_scrollbar_set_block_title_spans(self._handle, arr, len(arr), bool(show_border))
    return self

def _gen_Scrollbar_set_orientation_side(self, side):
    self._lib.ratatui_scrollbar_set_orientation_side(self._handle, C.c_uint32(int(side)))
    return self

def _gen_Sparkline_set_block_adv(self, borders_bits, border_type, pad_l=0, pad_t=0, pad_r=0, pad_b=0, title_spans=()):
    arr, _keep = _build_spans(title_spans)
    self._lib.ratatui_sparkline_set_block_adv(self._handle, C.c_uint8(int(borders_bits)), C.c_uint32(int(border_type)),
        C.c_uint16(int(pad_l)), C.c_uint16(int(pad_t)),
        C.c_uint16(int(pad_r)), C.c_uint16(int(pad_b)),
        arr, len(arr))
    return self

def _gen_Sparkline_set_block_title_spans(self, spans, show_border=True):
    arr, _keep = _build_spans(spans)
    self._lib.ratatui_sparkline_set_block_title_spans(self._handle, arr, len(arr), bool(show_border))
    return self

def _gen_Table_append_rows_cells_lines(self, rows):
    FfiLineSpans = self._lib.FfiLineSpans
    FfiCellLines = self._lib.FfiCellLines
    FfiRowCellsLines = self._lib.FfiRowCellsLines
    keep = []
    row_structs = (FfiRowCellsLines * len(rows))()
    cell_buffers = []
    for ri, row in enumerate(rows):
        cell_arr = (FfiCellLines * len(row))()
        for ci, cell in enumerate(row):
            lines_arr, k = _build_lines_spans(cell)
            keep.append(lines_arr)
            keep.extend(k)
            cell_arr[ci] = FfiCellLines(lines_arr, len(lines_arr))
        cell_buffers.append(cell_arr)
        row_structs[ri] = FfiRowCellsLines(cell_arr, len(cell_arr))
    self._lib.ratatui_table_append_rows_cells_lines(self._handle, row_structs, len(row_structs))

def _gen_Table_set_block_adv(self, borders_bits, border_type, pad_l=0, pad_t=0, pad_r=0, pad_b=0, title_spans=()):
    arr, _keep = _build_spans(title_spans)
    self._lib.ratatui_table_set_block_adv(self._handle, C.c_uint8(int(borders_bits)), C.c_uint32(int(border_type)),
        C.c_uint16(int(pad_l)), C.c_uint16(int(pad_t)),
        C.c_uint16(int(pad_r)), C.c_uint16(int(pad_b)),
        arr, len(arr))
    return self

def _gen_Table_set_block_title_spans(self, spans, show_border=True):
    arr, _keep = _build_spans(spans)
    self._lib.ratatui_table_set_block_title_spans(self._handle, arr, len(arr), bool(show_border))
    return self

def _gen_Table_set_cell_highlight_style(self, style):
    self._lib.ratatui_table_set_cell_highlight_style(self._handle, style.to_ffi())
    return self

def _gen_Table_set_column_highlight_style(self, style):
    self._lib.ratatui_table_set_column_highlight_style(self._handle, style.to_ffi())
    return self

def _gen_Table_set_header_style(self, style):
    self._lib.ratatui_table_set_header_style(self._handle, style.to_ffi())
    return self

def _gen_Tabs_add_title_spans(self, spans):
    arr, _keep = _build_spans(spans)
    self._lib.ratatui_tabs_add_title_spans(self._handle, arr, len(arr))

def _gen_Tabs_set_block_adv(self, borders_bits, border_type, pad_l=0, pad_t=0, pad_r=0, pad_b=0, title_spans=()):
    arr, _keep = _build_spans(title_spans)
    self._lib.ratatui_tabs_set_block_adv(self._handle, C.c_uint8(int(borders_bits)), C.c_uint32(int(border_type)),
        C.c_uint16(int(pad_l)), C.c_uint16(int(pad_t)),
        C.c_uint16(int(pad_r)), C.c_uint16(int(pad_b)),
        arr, len(arr))
    return self

def _gen_Tabs_set_block_title_spans(self, spans, show_border=True):
    arr, _keep = _build_spans(spans)
    self._lib.ratatui_tabs_set_block_title_spans(self._handle, arr, len(arr), bool(show_border))
    return self

def _gen_Tabs_set_divider_spans(self, spans):
    arr, _keep = _build_spans(spans)
    self._lib.ratatui_tabs_set_divider_spans(self._handle, arr, len(arr))
    return self


# ----- Terminal draw_*_in helpers -----

def _gen_Terminal_draw_linegauge(self, widget, rect):
    if not hasattr(self._lib, 'ratatui_terminal_draw_linegauge_in'):
        return False
    r = _ffi_rect(rect)
    return bool(self._lib.ratatui_terminal_draw_linegauge_in(self._handle, widget._handle, r))

def _gen_Terminal_draw_scrollbar(self, widget, rect):
    if not hasattr(self._lib, 'ratatui_terminal_draw_scrollbar_in'):
        return False
    r = _ffi_rect(rect)
    return bool(self._lib.ratatui_terminal_draw_scrollbar_in(self._handle, widget._handle, r))


# ----- Module-level headless render helpers -----

def headless_render_clear(width: int, height: int) -> str:
    lib = load_library()
    if not hasattr(lib, 'ratatui_headless_render_clear'):
        return ""
    out = C.c_char_p()
    ok = lib.ratatui_headless_render_clear(C.c_uint16(width), C.c_uint16(height), C.byref(out))
    if not ok or not out:
        return ""
    try:
        return C.cast(out, C.c_char_p).value.decode('utf-8', errors='replace')
    finally:
        lib.ratatui_string_free(out)

def headless_render_linegauge(width: int, height: int, widget) -> str:
    lib = widget._lib
    if not hasattr(lib, 'ratatui_headless_render_linegauge'):
        return ""
    out = C.c_char_p()
    ok = lib.ratatui_headless_render_linegauge(C.c_uint16(width), C.c_uint16(height), widget._handle, C.byref(out))
    if not ok or not out:
        return ""
    try:
        return C.cast(out, C.c_char_p).value.decode('utf-8', errors='replace')
    finally:
        lib.ratatui_string_free(out)

def headless_render_scrollbar(width: int, height: int, widget) -> str:
    lib = widget._lib
    if not hasattr(lib, 'ratatui_headless_render_scrollbar'):
        return ""
    out = C.c_char_p()
    ok = lib.ratatui_headless_render_scrollbar(C.c_uint16(width), C.c_uint16(height), widget._handle, C.byref(out))
    if not ok or not out:
        return ""
    try:
        return C.cast(out, C.c_char_p).value.decode('utf-8', errors='replace')
    finally:
        lib.ratatui_string_free(out)


# ----- Binder: attach generated methods where the hand class lacks them -----

_GENERATED_METHODS = [
    (BarChart, 'set_block_adv', _gen_BarChart_set_block_adv),
    (BarChart, 'set_block_title_spans', _gen_BarChart_set_block_title_spans),
    (BarChart, 'set_labels_spans', _gen_BarChart_set_labels_spans),
    (Canvas, 'set_block_adv', _gen_Canvas_set_block_adv),
    (Canvas, 'set_block_title_spans', _gen_Canvas_set_block_title_spans),
    (Chart, 'add_dataset_with_type', _gen_Chart_add_dataset_with_type),
    (Chart, 'add_datasets', _gen_Chart_add_datasets),
    (Chart, 'set_block_adv', _gen_Chart_set_block_adv),
    (Chart, 'set_block_title_spans', _gen_Chart_set_block_title_spans),
    (Gauge, 'set_block_adv', _gen_Gauge_set_block_adv),
    (Gauge, 'set_block_title_spans', _gen_Gauge_set_block_title_spans),
    (Gauge, 'set_label', _gen_Gauge_set_label),
    (Gauge, 'set_label_spans', _gen_Gauge_set_label_spans),
    (Gauge, 'set_ratio', _gen_Gauge_set_ratio),
    (List, 'append_item_spans', _gen_List_append_item_spans),
    (List, 'set_block_adv', _gen_List_set_block_adv),
    (List, 'set_block_title_spans', _gen_List_set_block_title_spans),
    (List, 'set_highlight_spacing', _gen_List_set_highlight_spacing),
    (Paragraph, 'set_block_adv', _gen_Paragraph_set_block_adv),
    (Paragraph, 'set_block_title_spans', _gen_Paragraph_set_block_title_spans),
    (Scrollbar, 'set_block_adv', _gen_Scrollbar_set_block_adv),
    (Scrollbar, 'set_block_title_spans', _gen_Scrollbar_set_block_title_spans),
    (Scrollbar, 'set_orientation_side', _gen_Scrollbar_set_orientation_side),
    (Sparkline, 'set_block_adv', _gen_Sparkline_set_block_adv),
    (Sparkline, 'set_block_title_spans', _gen_Sparkline_set_block_title_spans),
    (Table, 'append_rows_cells_lines', _gen_Table_append_rows_cells_lines),
    (Table, 'set_block_adv', _gen_Table_set_block_adv),
    (Table, 'set_block_title_spans', _gen_Table_set_block_title_spans),
    (Table, 'set_cell_highlight_style', _gen_Table_set_cell_highlight_style),
    (Table, 'set_column_highlight_style', _gen_Table_set_column_highlight_style),
    (Table, 'set_header_style', _gen_Table_set_header_style),
    (Tabs, 'add_title_spans', _gen_Tabs_add_title_spans),
    (Tabs, 'set_block_adv', _gen_Tabs_set_block_adv),
    (Tabs, 'set_block_title_spans', _gen_Tabs_set_block_title_spans),
    (Tabs, 'set_divider_spans', _gen_Tabs_set_divider_spans),
    (Terminal, 'draw_linegauge', _gen_Terminal_draw_linegauge),
    (Terminal, 'draw_scrollbar', _gen_Terminal_draw_scrollbar),
]


def apply_generated() -> None:
    """Attach every generated method onto its target hand class, but only
    where the hand class does not already define the name (hand wins).
    Idempotent."""
    for cls, name, func in _GENERATED_METHODS:
        if name not in cls.__dict__:
            setattr(cls, name, func)
