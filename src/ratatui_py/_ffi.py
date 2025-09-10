import os
import sys
import ctypes as C
from typing import Optional
from ctypes.util import find_library
from pathlib import Path

# ----- Low-level FFI types -----

class FfiRect(C.Structure):
    _fields_ = [
        ("x", C.c_uint16),
        ("y", C.c_uint16),
        ("width", C.c_uint16),
        ("height", C.c_uint16),
    ]

class FfiStyle(C.Structure):
    _fields_ = [
        ("fg", C.c_uint32),
        ("bg", C.c_uint32),
        ("mods", C.c_uint16),
    ]

# Text span batching (v0.2.0+)
class FfiSpan(C.Structure):
    _fields_ = [
        ("text_utf8", C.c_char_p),
        ("style", FfiStyle),
    ]

class FfiLineSpans(C.Structure):
    _fields_ = [
        ("spans", C.POINTER(FfiSpan)),
        ("len", C.c_size_t),
    ]

class FfiKeyEvent(C.Structure):
    _fields_ = [
        ("code", C.c_uint32),
        ("ch", C.c_uint32),
        ("mods", C.c_uint8),
    ]

class FfiEvent(C.Structure):
    _fields_ = [
        ("kind", C.c_uint32),
        ("key", FfiKeyEvent),
        ("width", C.c_uint16),
        ("height", C.c_uint16),
        ("mouse_x", C.c_uint16),
        ("mouse_y", C.c_uint16),
        ("mouse_kind", C.c_uint32),
        ("mouse_btn", C.c_uint32),
        ("mouse_mods", C.c_uint8),
    ]

# Enums/constants mirrored from ratatui_ffi
FFI_EVENT_KIND = {
    "NONE": 0,
    "KEY": 1,
    "RESIZE": 2,
    "MOUSE": 3,
}

FFI_KEY_CODE = {
    "Char": 0,
    "Enter": 1,
    "Left": 2,
    "Right": 3,
    "Up": 4,
    "Down": 5,
    "Esc": 6,
    "Backspace": 7,
    "Tab": 8,
    "Delete": 9,
    "Home": 10,
    "End": 11,
    "PageUp": 12,
    "PageDown": 13,
    "Insert": 14,
    "F1": 100,
    "F2": 101,
    "F3": 102,
    "F4": 103,
    "F5": 104,
    "F6": 105,
    "F7": 106,
    "F8": 107,
    "F9": 108,
    "F10": 109,
    "F11": 110,
    "F12": 111,
}

FFI_KEY_MODS = {
    "NONE": 0,
    "SHIFT": 1 << 0,
    "ALT": 1 << 1,
    "CTRL": 1 << 2,
}

FFI_COLOR = {
    "Reset": 0,
    "Black": 1,
    "Red": 2,
    "Green": 3,
    "Yellow": 4,
    "Blue": 5,
    "Magenta": 6,
    "Cyan": 7,
    "Gray": 8,
    "DarkGray": 9,
    "LightRed": 10,
    "LightGreen": 11,
    "LightYellow": 12,
    "LightBlue": 13,
    "LightMagenta": 14,
    "LightCyan": 15,
    "White": 16,
}

# Widget kinds for batched frame drawing
FFI_WIDGET_KIND = {
    "Paragraph": 1,
    "List": 2,
    "Table": 3,
    "Gauge": 4,
    "Tabs": 5,
    "BarChart": 6,
    "Sparkline": 7,
    "Chart": 8,
    # 9 reserved for Scrollbar if feature-enabled
}

# Common enums exposed as ints (align with ratatui_ffi v0.2.0)
FFI_ALIGN = {"Left": 0, "Center": 1, "Right": 2}
FFI_LAYOUT_DIR = {"Vertical": 0, "Horizontal": 1}
FFI_BORDERS = {"LEFT": 1, "RIGHT": 2, "TOP": 4, "BOTTOM": 8}
FFI_BORDER_TYPE = {"Plain": 0, "Thick": 1, "Double": 2}

# ----- Library loader -----

def _default_names():
    if sys.platform.startswith("win"):
        return ["ratatui_ffi.dll"]
    elif sys.platform == "darwin":
        return ["libratatui_ffi.dylib"]
    else:
        return ["libratatui_ffi.so", "ratatui_ffi"]

_cached_lib = None

def load_library(explicit: Optional[str] = None) -> C.CDLL:
    global _cached_lib
    if _cached_lib is not None:
        return _cached_lib

    path = explicit or os.getenv("RATATUI_FFI_LIB")
    if path and os.path.exists(path):
        lib = C.CDLL(path)
    else:
        # 2) look for a bundled library shipped within the package
        from pathlib import Path
        pkg_dir = Path(__file__).resolve().parent
        bundled = pkg_dir / "_bundled"
        lib = None
        for candidate in [bundled / ("ratatui_ffi.dll" if sys.platform.startswith("win") else ("libratatui_ffi.dylib" if sys.platform == "darwin" else "libratatui_ffi.so"))]:
            if candidate.exists():
                try:
                    lib = C.CDLL(str(candidate))
                    break
                except OSError:
                    pass
        if lib is None:
            # Try system search first
            libname = find_library("ratatui_ffi")
            if libname:
                try:
                    lib = C.CDLL(libname)
                except OSError:
                    lib = None
            else:
                lib = None
        # 4) fallback to default names in cwd/LD path
        if lib is None:
            last_err = None
            for name in _default_names():
                try:
                    lib = C.CDLL(name)
                    break
                except OSError as e:
                    last_err = e
            if lib is None and last_err:
                raise last_err

    # Configure signatures
    # Version and feature detection (v0.2.0+)
    if hasattr(lib, 'ratatui_ffi_version'):
        lib.ratatui_ffi_version.argtypes = [C.POINTER(C.c_uint16), C.POINTER(C.c_uint16), C.POINTER(C.c_uint16)]
    if hasattr(lib, 'ratatui_ffi_feature_bits'):
        lib.ratatui_ffi_feature_bits.restype = C.c_uint32
    lib.ratatui_init_terminal.restype = C.c_void_p
    lib.ratatui_terminal_clear.argtypes = [C.c_void_p]
    lib.ratatui_terminal_free.argtypes = [C.c_void_p]

    lib.ratatui_paragraph_new.argtypes = [C.c_char_p]
    lib.ratatui_paragraph_new.restype = C.c_void_p
    lib.ratatui_paragraph_set_block_title.argtypes = [C.c_void_p, C.c_char_p, C.c_bool]
    lib.ratatui_paragraph_free.argtypes = [C.c_void_p]
    lib.ratatui_paragraph_append_line.argtypes = [C.c_void_p, C.c_char_p, FfiStyle]
    # New: fine-grained span building
    lib.ratatui_paragraph_new_empty.restype = C.c_void_p
    lib.ratatui_paragraph_append_span.argtypes = [C.c_void_p, C.c_char_p, FfiStyle]
    lib.ratatui_paragraph_line_break.argtypes = [C.c_void_p]
    # v0.2.0 batching: spans and alignment controls
    if hasattr(lib, 'ratatui_paragraph_append_spans'):
        lib.ratatui_paragraph_append_spans.argtypes = [C.c_void_p, C.POINTER(FfiSpan), C.c_size_t]
    if hasattr(lib, 'ratatui_paragraph_append_line_spans'):
        lib.ratatui_paragraph_append_line_spans.argtypes = [C.c_void_p, C.POINTER(FfiSpan), C.c_size_t]
    if hasattr(lib, 'ratatui_paragraph_append_lines_spans'):
        lib.ratatui_paragraph_append_lines_spans.argtypes = [C.c_void_p, C.POINTER(FfiLineSpans), C.c_size_t]
    if hasattr(lib, 'ratatui_paragraph_set_alignment'):
        lib.ratatui_paragraph_set_alignment.argtypes = [C.c_void_p, C.c_uint]
    if hasattr(lib, 'ratatui_paragraph_set_block_title_alignment'):
        lib.ratatui_paragraph_set_block_title_alignment.argtypes = [C.c_void_p, C.c_uint]

    lib.ratatui_terminal_draw_paragraph.argtypes = [C.c_void_p, C.c_void_p]
    lib.ratatui_terminal_draw_paragraph.restype = C.c_bool
    lib.ratatui_terminal_draw_paragraph_in.argtypes = [C.c_void_p, C.c_void_p, FfiRect]
    lib.ratatui_terminal_draw_paragraph_in.restype = C.c_bool

    lib.ratatui_headless_render_paragraph.argtypes = [C.c_uint16, C.c_uint16, C.c_void_p, C.POINTER(C.c_char_p)]
    lib.ratatui_headless_render_paragraph.restype = C.c_bool
    lib.ratatui_string_free.argtypes = [C.c_char_p]

    lib.ratatui_terminal_size.argtypes = [C.POINTER(C.c_uint16), C.POINTER(C.c_uint16)]
    lib.ratatui_terminal_size.restype = C.c_bool

    lib.ratatui_next_event.argtypes = [C.c_uint64, C.POINTER(FfiEvent)]
    lib.ratatui_next_event.restype = C.c_bool

    # Event injection (for tests/automation)
    lib.ratatui_inject_key.argtypes = [C.c_uint32, C.c_uint32, C.c_uint8]
    lib.ratatui_inject_resize.argtypes = [C.c_uint16, C.c_uint16]
    lib.ratatui_inject_mouse.argtypes = [C.c_uint32, C.c_uint32, C.c_uint16, C.c_uint16, C.c_uint8]

    # List
    lib.ratatui_list_new.restype = C.c_void_p
    lib.ratatui_list_free.argtypes = [C.c_void_p]
    lib.ratatui_list_append_item.argtypes = [C.c_void_p, C.c_char_p, FfiStyle]
    lib.ratatui_list_set_block_title.argtypes = [C.c_void_p, C.c_char_p, C.c_bool]
    lib.ratatui_list_set_selected.argtypes = [C.c_void_p, C.c_int]
    lib.ratatui_list_set_highlight_style.argtypes = [C.c_void_p, FfiStyle]
    lib.ratatui_list_set_highlight_symbol.argtypes = [C.c_void_p, C.c_char_p]
    if hasattr(lib, 'ratatui_list_append_items_spans'):
        lib.ratatui_list_append_items_spans.argtypes = [C.c_void_p, C.POINTER(FfiLineSpans), C.c_size_t]
    if hasattr(lib, 'ratatui_list_append_item_spans'):
        lib.ratatui_list_append_item_spans.argtypes = [C.c_void_p, C.POINTER(FfiSpan), C.c_size_t]
    if hasattr(lib, 'ratatui_list_set_highlight_spacing'):
        lib.ratatui_list_set_highlight_spacing.argtypes = [C.c_void_p, C.c_uint]
    if hasattr(lib, 'ratatui_list_set_direction'):
        lib.ratatui_list_set_direction.argtypes = [C.c_void_p, C.c_uint]
    if hasattr(lib, 'ratatui_list_set_scroll_offset'):
        lib.ratatui_list_set_scroll_offset.argtypes = [C.c_void_p, C.c_uint16]
    if hasattr(lib, 'ratatui_list_set_block_title_alignment'):
        lib.ratatui_list_set_block_title_alignment.argtypes = [C.c_void_p, C.c_uint]
    lib.ratatui_terminal_draw_list_in.argtypes = [C.c_void_p, C.c_void_p, FfiRect]
    lib.ratatui_terminal_draw_list_in.restype = C.c_bool
    lib.ratatui_headless_render_list.argtypes = [C.c_uint16, C.c_uint16, C.c_void_p, C.POINTER(C.c_char_p)]
    lib.ratatui_headless_render_list.restype = C.c_bool

    # Table
    lib.ratatui_table_new.restype = C.c_void_p
    lib.ratatui_table_free.argtypes = [C.c_void_p]
    lib.ratatui_table_set_headers.argtypes = [C.c_void_p, C.c_char_p]
    lib.ratatui_table_append_row.argtypes = [C.c_void_p, C.c_char_p]
    lib.ratatui_table_set_block_title.argtypes = [C.c_void_p, C.c_char_p, C.c_bool]
    lib.ratatui_table_set_selected.argtypes = [C.c_void_p, C.c_int]
    lib.ratatui_table_set_row_highlight_style.argtypes = [C.c_void_p, FfiStyle]
    lib.ratatui_table_set_highlight_symbol.argtypes = [C.c_void_p, C.c_char_p]
    lib.ratatui_terminal_draw_table_in.argtypes = [C.c_void_p, C.c_void_p, FfiRect]
    lib.ratatui_terminal_draw_table_in.restype = C.c_bool
    lib.ratatui_headless_render_table.argtypes = [C.c_uint16, C.c_uint16, C.c_void_p, C.POINTER(C.c_char_p)]
    lib.ratatui_headless_render_table.restype = C.c_bool
    # v0.2.0 batching: headers/items/cells via spans/lines
    if hasattr(lib, 'ratatui_table_set_headers_spans'):
        lib.ratatui_table_set_headers_spans.argtypes = [C.c_void_p, C.POINTER(FfiLineSpans), C.c_size_t]
    if hasattr(lib, 'ratatui_table_append_row_spans'):
        lib.ratatui_table_append_row_spans.argtypes = [C.c_void_p, C.POINTER(FfiLineSpans), C.c_size_t]
    # FfiCellLines and FfiRowCellsLines are used for multiline cells
    class FfiCellLines(C.Structure):
        _fields_ = [
            ("lines", C.POINTER(FfiLineSpans)),
            ("len", C.c_size_t),
        ]
    class FfiRowCellsLines(C.Structure):
        _fields_ = [
            ("cells", C.POINTER(FfiCellLines)),
            ("len", C.c_size_t),
        ]
    lib.FfiCellLines = FfiCellLines
    lib.FfiRowCellsLines = FfiRowCellsLines
    if hasattr(lib, 'ratatui_table_append_row_cells_lines'):
        lib.ratatui_table_append_row_cells_lines.argtypes = [C.c_void_p, C.POINTER(FfiCellLines), C.c_size_t]
    if hasattr(lib, 'ratatui_table_set_widths'):
        lib.ratatui_table_set_widths.argtypes = [C.c_void_p, C.POINTER(C.c_uint16), C.c_size_t]
    if hasattr(lib, 'ratatui_table_set_widths_percentages'):
        lib.ratatui_table_set_widths_percentages.argtypes = [C.c_void_p, C.POINTER(C.c_uint16), C.c_size_t]
    if hasattr(lib, 'ratatui_table_set_row_height'):
        lib.ratatui_table_set_row_height.argtypes = [C.c_void_p, C.c_uint16]
    if hasattr(lib, 'ratatui_table_set_column_spacing'):
        lib.ratatui_table_set_column_spacing.argtypes = [C.c_void_p, C.c_uint16]
    if hasattr(lib, 'ratatui_table_set_highlight_spacing'):
        lib.ratatui_table_set_highlight_spacing.argtypes = [C.c_void_p, C.c_uint]
    if hasattr(lib, 'ratatui_table_set_block_title_alignment'):
        lib.ratatui_table_set_block_title_alignment.argtypes = [C.c_void_p, C.c_uint]

    # Gauge
    lib.ratatui_gauge_new.restype = C.c_void_p
    lib.ratatui_gauge_free.argtypes = [C.c_void_p]
    lib.ratatui_gauge_set_ratio.argtypes = [C.c_void_p, C.c_float]
    lib.ratatui_gauge_set_label.argtypes = [C.c_void_p, C.c_char_p]
    lib.ratatui_gauge_set_block_title.argtypes = [C.c_void_p, C.c_char_p, C.c_bool]
    _gauge_label_spans = getattr(lib, 'ratatui_gauge_set_label_spans', None)
    if _gauge_label_spans is not None:
        _gauge_label_spans.argtypes = [C.c_void_p, C.POINTER(FfiSpan), C.c_size_t]
    lib.ratatui_terminal_draw_gauge_in.argtypes = [C.c_void_p, C.c_void_p, FfiRect]
    lib.ratatui_terminal_draw_gauge_in.restype = C.c_bool
    lib.ratatui_headless_render_gauge.argtypes = [C.c_uint16, C.c_uint16, C.c_void_p, C.POINTER(C.c_char_p)]
    lib.ratatui_headless_render_gauge.restype = C.c_bool

    # Tabs
    lib.ratatui_tabs_new.restype = C.c_void_p
    lib.ratatui_tabs_free.argtypes = [C.c_void_p]
    lib.ratatui_tabs_set_titles.argtypes = [C.c_void_p, C.c_char_p]
    lib.ratatui_tabs_set_selected.argtypes = [C.c_void_p, C.c_uint16]
    lib.ratatui_tabs_set_block_title.argtypes = [C.c_void_p, C.c_char_p, C.c_bool]
    if hasattr(lib, 'ratatui_tabs_set_titles_spans'):
        lib.ratatui_tabs_set_titles_spans.argtypes = [C.c_void_p, C.POINTER(FfiLineSpans), C.c_size_t]
    if hasattr(lib, 'ratatui_tabs_set_block_title_alignment'):
        lib.ratatui_tabs_set_block_title_alignment.argtypes = [C.c_void_p, C.c_uint]
    if hasattr(lib, 'ratatui_tabs_set_divider'):
        lib.ratatui_tabs_set_divider.argtypes = [C.c_void_p, C.c_char_p]
    if hasattr(lib, 'ratatui_tabs_clear_titles'):
        lib.ratatui_tabs_clear_titles.argtypes = [C.c_void_p]
    lib.ratatui_terminal_draw_tabs_in.argtypes = [C.c_void_p, C.c_void_p, FfiRect]
    lib.ratatui_terminal_draw_tabs_in.restype = C.c_bool
    lib.ratatui_headless_render_tabs.argtypes = [C.c_uint16, C.c_uint16, C.c_void_p, C.POINTER(C.c_char_p)]
    lib.ratatui_headless_render_tabs.restype = C.c_bool

    # Bar chart
    lib.ratatui_barchart_new.restype = C.c_void_p
    lib.ratatui_barchart_free.argtypes = [C.c_void_p]
    lib.ratatui_barchart_set_values.argtypes = [C.c_void_p, C.POINTER(C.c_uint64), C.c_size_t]
    lib.ratatui_barchart_set_labels.argtypes = [C.c_void_p, C.c_char_p]
    lib.ratatui_barchart_set_block_title.argtypes = [C.c_void_p, C.c_char_p, C.c_bool]
    lib.ratatui_terminal_draw_barchart_in.argtypes = [C.c_void_p, C.c_void_p, FfiRect]
    lib.ratatui_terminal_draw_barchart_in.restype = C.c_bool
    lib.ratatui_headless_render_barchart.argtypes = [C.c_uint16, C.c_uint16, C.c_void_p, C.POINTER(C.c_char_p)]
    lib.ratatui_headless_render_barchart.restype = C.c_bool
    if hasattr(lib, 'ratatui_barchart_set_block_title_alignment'):
        lib.ratatui_barchart_set_block_title_alignment.argtypes = [C.c_void_p, C.c_uint]

    # Chart
    lib.ratatui_chart_new.restype = C.c_void_p
    lib.ratatui_chart_free.argtypes = [C.c_void_p]
    lib.ratatui_chart_add_line.argtypes = [C.c_void_p, C.c_char_p, C.POINTER(C.c_double), C.c_size_t, FfiStyle]
    lib.ratatui_chart_set_axes_titles.argtypes = [C.c_void_p, C.c_char_p, C.c_char_p]
    lib.ratatui_chart_set_block_title.argtypes = [C.c_void_p, C.c_char_p, C.c_bool]
    if hasattr(lib, 'ratatui_chart_set_block_title_alignment'):
        lib.ratatui_chart_set_block_title_alignment.argtypes = [C.c_void_p, C.c_uint]
    lib.ratatui_terminal_draw_chart_in.argtypes = [C.c_void_p, C.c_void_p, FfiRect]
    lib.ratatui_terminal_draw_chart_in.restype = C.c_bool
    lib.ratatui_headless_render_chart.argtypes = [C.c_uint16, C.c_uint16, C.c_void_p, C.POINTER(C.c_char_p)]
    lib.ratatui_headless_render_chart.restype = C.c_bool
    if hasattr(lib, 'ratatui_chart_set_bounds'):
        lib.ratatui_chart_set_bounds.argtypes = [C.c_void_p, C.c_double, C.c_double, C.c_double, C.c_double]
    if hasattr(lib, 'ratatui_chart_set_style'):
        lib.ratatui_chart_set_style.argtypes = [C.c_void_p, FfiStyle]
    if hasattr(lib, 'ratatui_chart_set_axis_styles'):
        lib.ratatui_chart_set_axis_styles.argtypes = [C.c_void_p, FfiStyle, FfiStyle]
    if hasattr(lib, 'ratatui_chart_set_legend_position'):
        lib.ratatui_chart_set_legend_position.argtypes = [C.c_void_p, C.c_uint]
    if hasattr(lib, 'ratatui_chart_set_hidden_legend_constraints'):
        lib.ratatui_chart_set_hidden_legend_constraints.argtypes = [C.c_void_p, C.POINTER(C.c_uint32), C.POINTER(C.c_uint16)]
    if hasattr(lib, 'ratatui_chart_set_labels_alignment'):
        lib.ratatui_chart_set_labels_alignment.argtypes = [C.c_void_p, C.c_uint, C.c_uint]

    # Sparkline
    lib.ratatui_sparkline_new.restype = C.c_void_p
    lib.ratatui_sparkline_free.argtypes = [C.c_void_p]
    lib.ratatui_sparkline_set_values.argtypes = [C.c_void_p, C.POINTER(C.c_uint64), C.c_size_t]
    lib.ratatui_sparkline_set_block_title.argtypes = [C.c_void_p, C.c_char_p, C.c_bool]
    lib.ratatui_terminal_draw_sparkline_in.argtypes = [C.c_void_p, C.c_void_p, FfiRect]
    lib.ratatui_terminal_draw_sparkline_in.restype = C.c_bool
    lib.ratatui_headless_render_sparkline.argtypes = [C.c_uint16, C.c_uint16, C.c_void_p, C.POINTER(C.c_char_p)]
    lib.ratatui_headless_render_sparkline.restype = C.c_bool
    if hasattr(lib, 'ratatui_sparkline_set_block_title_alignment'):
        lib.ratatui_sparkline_set_block_title_alignment.argtypes = [C.c_void_p, C.c_uint]
    if hasattr(lib, 'ratatui_sparkline_set_max'):
        lib.ratatui_sparkline_set_max.argtypes = [C.c_void_p, C.c_uint64]
    if hasattr(lib, 'ratatui_sparkline_set_style'):
        lib.ratatui_sparkline_set_style.argtypes = [C.c_void_p, FfiStyle]

    # Optional scrollbar (if built with feature)
    if hasattr(lib, 'ratatui_scrollbar_new'):
        lib.ratatui_scrollbar_new.restype = C.c_void_p
        lib.ratatui_scrollbar_free.argtypes = [C.c_void_p]
        lib.ratatui_scrollbar_configure.argtypes = [C.c_void_p, C.c_uint32, C.c_uint16, C.c_uint16, C.c_uint16]
        lib.ratatui_scrollbar_set_block_title.argtypes = [C.c_void_p, C.c_char_p, C.c_bool]
        lib.ratatui_terminal_draw_scrollbar_in.argtypes = [C.c_void_p, C.c_void_p, FfiRect]
        lib.ratatui_terminal_draw_scrollbar_in.restype = C.c_bool
        lib.ratatui_headless_render_scrollbar.argtypes = [C.c_uint16, C.c_uint16, C.c_void_p, C.POINTER(C.c_char_p)]
        lib.ratatui_headless_render_scrollbar.restype = C.c_bool
        if hasattr(lib, 'ratatui_scrollbar_set_block_title_alignment'):
            lib.ratatui_scrollbar_set_block_title_alignment.argtypes = [C.c_void_p, C.c_uint]

    # Batched frame drawing
    class FfiDrawCmd(C.Structure):
        _fields_ = [
            ("kind", C.c_uint32),
            ("handle", C.c_void_p),
            ("rect", FfiRect),
        ]

    lib.FfiDrawCmd = FfiDrawCmd  # expose for importers
    lib.ratatui_terminal_draw_frame.argtypes = [C.c_void_p, C.POINTER(FfiDrawCmd), C.c_size_t]
    lib.ratatui_terminal_draw_frame.restype = C.c_bool

    # Layout helpers (v0.2.0+)
    if hasattr(lib, 'ratatui_layout_split_ex'):
        lib.ratatui_layout_split_ex.argtypes = [
            C.c_uint16, C.c_uint16, C.c_uint,  # w, h, dir
            C.POINTER(C.c_uint), C.POINTER(C.c_uint16), C.POINTER(C.c_uint16), C.c_size_t,  # kinds, valsA, valsB, len
            C.c_uint16, C.c_uint16, C.c_uint16, C.c_uint16, C.c_uint16,  # spacing, ml, mt, mr, mb
            C.POINTER(FfiRect), C.c_size_t,  # out rects, cap
        ]
    if hasattr(lib, 'ratatui_layout_split_ex2'):
        lib.ratatui_layout_split_ex2.argtypes = [
            C.c_uint16, C.c_uint16, C.c_uint,  # w, h, dir
            C.POINTER(C.c_uint), C.POINTER(C.c_uint16), C.POINTER(C.c_uint16), C.c_size_t,  # kinds, valsA, valsB, len
            C.c_uint16, C.c_uint16, C.c_uint16, C.c_uint16, C.c_uint16,  # spacing, ml, mt, mr, mb
            C.POINTER(FfiRect), C.c_size_t,  # out rects, cap
        ]

    # Headless frame render (for testing composites)
    if hasattr(lib, 'ratatui_headless_render_frame'):
        lib.ratatui_headless_render_frame.argtypes = [C.c_uint16, C.c_uint16, C.POINTER(FfiDrawCmd), C.c_size_t, C.POINTER(C.c_char_p)]
        lib.ratatui_headless_render_frame.restype = C.c_bool
    # Extended headless outputs (v0.2.0+)
    if hasattr(lib, 'ratatui_headless_render_frame_styles_ex'):
        # Keep types permissive; function fills style dump via char** similar to text
        lib.ratatui_headless_render_frame_styles_ex.argtypes = [C.c_uint16, C.c_uint16, C.POINTER(FfiDrawCmd), C.c_size_t, C.POINTER(C.c_char_p)]
        lib.ratatui_headless_render_frame_styles_ex.restype = C.c_bool
    if hasattr(lib, 'ratatui_headless_render_frame_cells'):
        # Returns number of cells written (width*height) into provided buffer
        class FfiCellInfo(C.Structure):
            _fields_ = [
                ("ch", C.c_uint32),
                ("fg", C.c_uint32),
                ("bg", C.c_uint32),
                ("mods", C.c_uint16),
            ]
        lib.FfiCellInfo = FfiCellInfo
        lib.ratatui_headless_render_frame_cells.argtypes = [C.c_uint16, C.c_uint16, C.POINTER(FfiDrawCmd), C.c_size_t, C.POINTER(FfiCellInfo), C.c_size_t]
        lib.ratatui_headless_render_frame_cells.restype = C.c_size_t

    # Color helpers (v0.2.0+)
    if hasattr(lib, 'ratatui_color_rgb'):
        lib.ratatui_color_rgb.argtypes = [C.c_uint8, C.c_uint8, C.c_uint8]
        lib.ratatui_color_rgb.restype = C.c_uint32
    if hasattr(lib, 'ratatui_color_indexed'):
        lib.ratatui_color_indexed.argtypes = [C.c_uint8]
        lib.ratatui_color_indexed.restype = C.c_uint32
    # Clear widget
    if hasattr(lib, 'ratatui_clear_in'):
        lib.ratatui_clear_in.argtypes = [C.c_void_p, FfiRect]
        lib.ratatui_clear_in.restype = C.c_bool
    # Canvas widget
    if hasattr(lib, 'ratatui_canvas_new'):
        lib.ratatui_canvas_new.argtypes = [C.c_double, C.c_double, C.c_double, C.c_double]
        lib.ratatui_canvas_new.restype = C.c_void_p
    if hasattr(lib, 'ratatui_canvas_free'):
        lib.ratatui_canvas_free.argtypes = [C.c_void_p]
    if hasattr(lib, 'ratatui_canvas_set_bounds'):
        lib.ratatui_canvas_set_bounds.argtypes = [C.c_void_p, C.c_double, C.c_double, C.c_double, C.c_double]
    if hasattr(lib, 'ratatui_canvas_set_background_color'):
        lib.ratatui_canvas_set_background_color.argtypes = [C.c_void_p, C.c_uint32]
    if hasattr(lib, 'ratatui_canvas_set_block_title'):
        lib.ratatui_canvas_set_block_title.argtypes = [C.c_void_p, C.c_char_p, C.c_bool]
    if hasattr(lib, 'ratatui_canvas_set_block_title_alignment'):
        lib.ratatui_canvas_set_block_title_alignment.argtypes = [C.c_void_p, C.c_uint]
    if hasattr(lib, 'ratatui_canvas_set_block_adv'):
        lib.ratatui_canvas_set_block_adv.argtypes = [C.c_void_p, C.c_uint8, C.c_uint32, C.c_uint16, C.c_uint16, C.c_uint16, C.c_uint16, C.POINTER(FfiSpan), C.c_size_t]
    if hasattr(lib, 'ratatui_canvas_set_marker'):
        lib.ratatui_canvas_set_marker.argtypes = [C.c_void_p, C.c_uint32]
    if hasattr(lib, 'ratatui_canvas_add_line'):
        lib.ratatui_canvas_add_line.argtypes = [C.c_void_p, C.c_double, C.c_double, C.c_double, C.c_double, FfiStyle]
    if hasattr(lib, 'ratatui_canvas_add_rect'):
        lib.ratatui_canvas_add_rect.argtypes = [C.c_void_p, C.c_double, C.c_double, C.c_double, C.c_double, FfiStyle, C.c_bool]
    if hasattr(lib, 'ratatui_canvas_add_points'):
        lib.ratatui_canvas_add_points.argtypes = [C.c_void_p, C.POINTER(C.c_double), C.c_size_t, FfiStyle, C.c_uint32]
    if hasattr(lib, 'ratatui_terminal_draw_canvas_in'):
        lib.ratatui_terminal_draw_canvas_in.argtypes = [C.c_void_p, C.c_void_p, FfiRect]
        lib.ratatui_terminal_draw_canvas_in.restype = C.c_bool
    if hasattr(lib, 'ratatui_headless_render_canvas'):
        lib.ratatui_headless_render_canvas.argtypes = [C.c_uint16, C.c_uint16, C.c_void_p, C.POINTER(C.c_char_p)]
        lib.ratatui_headless_render_canvas.restype = C.c_bool
    # Ratatui logo
    if hasattr(lib, 'ratatui_ratatuilogo_draw_in'):
        lib.ratatui_ratatuilogo_draw_in.argtypes = [C.c_void_p, FfiRect]
        lib.ratatui_ratatuilogo_draw_in.restype = C.c_bool
    if hasattr(lib, 'ratatui_ratatuilogo_draw_sized_in'):
        lib.ratatui_ratatuilogo_draw_sized_in.argtypes = [C.c_void_p, FfiRect, C.c_uint32]
        lib.ratatui_ratatuilogo_draw_sized_in.restype = C.c_bool
    if hasattr(lib, 'ratatui_headless_render_ratatuilogo'):
        lib.ratatui_headless_render_ratatuilogo.argtypes = [C.c_uint16, C.c_uint16, C.POINTER(C.c_char_p)]
        lib.ratatui_headless_render_ratatuilogo.restype = C.c_bool
    if hasattr(lib, 'ratatui_headless_render_ratatuilogo_sized'):
        lib.ratatui_headless_render_ratatuilogo_sized.argtypes = [C.c_uint16, C.c_uint16, C.c_uint32, C.POINTER(C.c_char_p)]
        lib.ratatui_headless_render_ratatuilogo_sized.restype = C.c_bool

    # Block advanced for common widgets
    for name in [
        'ratatui_paragraph_set_block_adv',
        'ratatui_list_set_block_adv',
        'ratatui_table_set_block_adv',
        'ratatui_gauge_set_block_adv',
        'ratatui_linegauge_set_block_adv',
        'ratatui_tabs_set_block_adv',
        'ratatui_barchart_set_block_adv',
        'ratatui_chart_set_block_adv',
        'ratatui_sparkline_set_block_adv',
        'ratatui_scrollbar_set_block_adv',
    ]:
        if hasattr(lib, name):
            getattr(lib, name).argtypes = [C.c_void_p, C.c_uint8, C.c_uint32, C.c_uint16, C.c_uint16, C.c_uint16, C.c_uint16, C.POINTER(FfiSpan), C.c_size_t]

    # ---- Additional v0.2.0 exports (ensure discovery and link-through) ----
    # Terminal raw/alt + cursor/viewport
    if hasattr(lib, 'ratatui_terminal_enable_raw'):
        lib.ratatui_terminal_enable_raw.argtypes = []
        lib.ratatui_terminal_enable_raw.restype = None
    if hasattr(lib, 'ratatui_terminal_disable_raw'):
        lib.ratatui_terminal_disable_raw.argtypes = []
        lib.ratatui_terminal_disable_raw.restype = None
    if hasattr(lib, 'ratatui_terminal_enter_alt'):
        lib.ratatui_terminal_enter_alt.argtypes = []
        lib.ratatui_terminal_enter_alt.restype = None
    if hasattr(lib, 'ratatui_terminal_leave_alt'):
        lib.ratatui_terminal_leave_alt.argtypes = []
        lib.ratatui_terminal_leave_alt.restype = None
    if hasattr(lib, 'ratatui_terminal_show_cursor'):
        lib.ratatui_terminal_show_cursor.argtypes = []
        lib.ratatui_terminal_show_cursor.restype = None
    if hasattr(lib, 'ratatui_terminal_get_cursor_position'):
        lib.ratatui_terminal_get_cursor_position.argtypes = [C.POINTER(C.c_uint16), C.POINTER(C.c_uint16)]
        lib.ratatui_terminal_get_cursor_position.restype = C.c_bool
    if hasattr(lib, 'ratatui_terminal_set_cursor_position'):
        lib.ratatui_terminal_set_cursor_position.argtypes = [C.c_uint16, C.c_uint16]
        lib.ratatui_terminal_set_cursor_position.restype = None
    if hasattr(lib, 'ratatui_terminal_get_viewport_area'):
        lib.ratatui_terminal_get_viewport_area.argtypes = [C.POINTER(FfiRect)]
        lib.ratatui_terminal_get_viewport_area.restype = C.c_bool
    if hasattr(lib, 'ratatui_terminal_set_viewport_area'):
        lib.ratatui_terminal_set_viewport_area.argtypes = [FfiRect]
        lib.ratatui_terminal_set_viewport_area.restype = None

    # Layout base split
    if hasattr(lib, 'ratatui_layout_split'):
        lib.ratatui_layout_split.argtypes = [
            C.c_uint16, C.c_uint16, C.c_uint,  # w, h, dir
            C.POINTER(C.c_uint), C.POINTER(C.c_uint16), C.POINTER(C.c_uint16), C.c_size_t,  # kinds, valsA, valsB, len
            C.POINTER(FfiRect), C.c_size_t,  # out rects, cap
        ]

    # Paragraph advanced
    for name in [
        'ratatui_paragraph_set_style',
        'ratatui_paragraph_set_wrap',
        'ratatui_paragraph_set_scroll',
        'ratatui_paragraph_reserve_lines',
        'ratatui_paragraph_append_line_spans',
        'ratatui_paragraph_append_lines_spans',
        'ratatui_paragraph_set_block_adv',
    ]:
        if hasattr(lib, name):
            if name == 'ratatui_paragraph_set_style':
                lib.ratatui_paragraph_set_style.argtypes = [C.c_void_p, FfiStyle]
            elif name == 'ratatui_paragraph_set_wrap':
                lib.ratatui_paragraph_set_wrap.argtypes = [C.c_void_p, C.c_bool]
            elif name == 'ratatui_paragraph_set_scroll':
                lib.ratatui_paragraph_set_scroll.argtypes = [C.c_void_p, C.c_uint16]
            elif name == 'ratatui_paragraph_reserve_lines':
                lib.ratatui_paragraph_reserve_lines.argtypes = [C.c_void_p, C.c_size_t]
            else:
                getattr(lib, name)

    # List items/state and advanced
    for name in [
        'ratatui_list_append_item_spans',
        'ratatui_list_reserve_items',
        'ratatui_list_set_direction',
        'ratatui_list_set_scroll_offset',
        'ratatui_list_set_block_adv',
        'ratatui_list_set_block_title_alignment',
        'ratatui_headless_render_list_state',
        'ratatui_terminal_draw_list_state_in',
        'ratatui_list_state_new',
        'ratatui_list_state_free',
        'ratatui_list_state_set_selected',
        'ratatui_list_state_set_offset',
    ]:
        if hasattr(lib, name):
            if name == 'ratatui_list_state_new':
                lib.ratatui_list_state_new.restype = C.c_void_p
            elif name == 'ratatui_list_state_free':
                lib.ratatui_list_state_free.argtypes = [C.c_void_p]
            elif name == 'ratatui_list_state_set_selected':
                lib.ratatui_list_state_set_selected.argtypes = [C.c_void_p, C.c_int]
            elif name == 'ratatui_list_state_set_offset':
                lib.ratatui_list_state_set_offset.argtypes = [C.c_void_p, C.c_uint16]
            elif name == 'ratatui_terminal_draw_list_state_in':
                lib.ratatui_terminal_draw_list_state_in.argtypes = [C.c_void_p, C.c_void_p, C.c_void_p, FfiRect]
                lib.ratatui_terminal_draw_list_state_in.restype = C.c_bool
            elif name == 'ratatui_headless_render_list_state':
                lib.ratatui_headless_render_list_state.argtypes = [C.c_uint16, C.c_uint16, C.c_void_p, C.c_void_p, C.POINTER(C.c_char_p)]
                lib.ratatui_headless_render_list_state.restype = C.c_bool
            else:
                getattr(lib, name)

    # Table columns/state and advanced
    for name in [
        'ratatui_table_set_widths',
        'ratatui_table_set_widths_percentages',
        'ratatui_table_set_row_height',
        'ratatui_table_set_column_spacing',
        'ratatui_table_set_highlight_spacing',
        'ratatui_table_set_header_style',
        'ratatui_table_set_cell_highlight_style',
        'ratatui_table_set_column_highlight_style',
        'ratatui_table_append_row_spans',
        'ratatui_table_append_rows_cells_lines',
        'ratatui_table_reserve_rows',
        'ratatui_table_set_block_adv',
        'ratatui_table_set_block_title_alignment',
        'ratatui_table_state_new',
        'ratatui_table_state_free',
        'ratatui_table_state_set_selected',
        'ratatui_table_state_set_offset',
        'ratatui_terminal_draw_table_state_in',
    ]:
        if hasattr(lib, name):
            if name == 'ratatui_table_state_new':
                lib.ratatui_table_state_new.restype = C.c_void_p
            elif name == 'ratatui_table_state_free':
                lib.ratatui_table_state_free.argtypes = [C.c_void_p]
            elif name == 'ratatui_table_state_set_selected':
                lib.ratatui_table_state_set_selected.argtypes = [C.c_void_p, C.c_int]
            elif name == 'ratatui_table_state_set_offset':
                lib.ratatui_table_state_set_offset.argtypes = [C.c_void_p, C.c_uint16]
            elif name == 'ratatui_terminal_draw_table_state_in':
                lib.ratatui_terminal_draw_table_state_in.argtypes = [C.c_void_p, C.c_void_p, C.c_void_p, FfiRect]
                lib.ratatui_terminal_draw_table_state_in.restype = C.c_bool
            else:
                getattr(lib, name)

    # Tabs advanced
    for name in [
        'ratatui_tabs_add_title_spans',
        'ratatui_tabs_clear_titles',
        'ratatui_tabs_set_styles',
        'ratatui_tabs_set_divider',
        'ratatui_tabs_set_block_adv',
        'ratatui_tabs_set_block_title_alignment',
    ]:
        if hasattr(lib, name):
            getattr(lib, name)

    # Gauge/LineGauge advanced
    for name in [
        'ratatui_gauge_set_styles',
        'ratatui_gauge_set_block_adv',
        'ratatui_gauge_set_block_title_alignment',
        'ratatui_linegauge_new',
        'ratatui_linegauge_free',
        'ratatui_linegauge_set_ratio',
        'ratatui_linegauge_set_label',
        'ratatui_linegauge_set_style',
        'ratatui_linegauge_set_block_title',
        'ratatui_linegauge_set_block_title_alignment',
        'ratatui_linegauge_set_block_adv',
        'ratatui_headless_render_linegauge',
        'ratatui_terminal_draw_linegauge_in',
    ]:
        if hasattr(lib, name):
            getattr(lib, name)

    # Chart advanced
    for name in [
        'ratatui_chart_set_style',
        'ratatui_chart_set_bounds',
        'ratatui_chart_set_axis_styles',
        'ratatui_chart_set_labels_alignment',
        'ratatui_chart_set_legend_position',
        'ratatui_chart_set_hidden_legend_constraints',
        'ratatui_chart_set_block_adv',
        'ratatui_chart_set_block_title_alignment',
        'ratatui_chart_add_datasets',
        'ratatui_chart_add_dataset_with_type',
        'ratatui_chart_reserve_datasets',
        'ratatui_chart_set_x_labels_spans',
        'ratatui_chart_set_y_labels_spans',
    ]:
        if hasattr(lib, name):
            getattr(lib, name)

    # Bar chart advanced
    for name in [
        'ratatui_barchart_set_bar_width',
        'ratatui_barchart_set_bar_gap',
        'ratatui_barchart_set_styles',
        'ratatui_barchart_set_block_adv',
        'ratatui_barchart_set_block_title_alignment',
    ]:
        if hasattr(lib, name):
            getattr(lib, name)

    # Sparkline advanced
    for name in [
        'ratatui_sparkline_set_style',
        'ratatui_sparkline_set_max',
        'ratatui_sparkline_set_block_adv',
        'ratatui_sparkline_set_block_title_alignment',
    ]:
        if hasattr(lib, name):
            getattr(lib, name)

    # Scrollbar extras
    for name in [
        'ratatui_scrollbar_set_block_adv',
        'ratatui_scrollbar_set_block_title_alignment',
        'ratatui_scrollbar_set_orientation_side',
    ]:
        if hasattr(lib, name):
            getattr(lib, name)

    # Canvas / Clear / Logo widgets + headless
    if hasattr(lib, 'ratatui_canvas_new'): lib.ratatui_canvas_new
    if hasattr(lib, 'ratatui_canvas_free'): lib.ratatui_canvas_free
    if hasattr(lib, 'ratatui_canvas_set_bounds'): lib.ratatui_canvas_set_bounds
    if hasattr(lib, 'ratatui_canvas_set_background_color'): lib.ratatui_canvas_set_background_color
    if hasattr(lib, 'ratatui_canvas_set_marker'): lib.ratatui_canvas_set_marker
    if hasattr(lib, 'ratatui_canvas_set_block_title'): lib.ratatui_canvas_set_block_title
    if hasattr(lib, 'ratatui_canvas_set_block_title_alignment'): lib.ratatui_canvas_set_block_title_alignment
    if hasattr(lib, 'ratatui_canvas_set_block_adv'): lib.ratatui_canvas_set_block_adv
    if hasattr(lib, 'ratatui_canvas_add_line'): lib.ratatui_canvas_add_line
    if hasattr(lib, 'ratatui_canvas_add_rect'): lib.ratatui_canvas_add_rect
    if hasattr(lib, 'ratatui_canvas_add_points'): lib.ratatui_canvas_add_points
    if hasattr(lib, 'ratatui_terminal_draw_canvas_in'): lib.ratatui_terminal_draw_canvas_in
    if hasattr(lib, 'ratatui_headless_render_canvas'): lib.ratatui_headless_render_canvas
    if hasattr(lib, 'ratatui_clear_in'): lib.ratatui_clear_in
    if hasattr(lib, 'ratatui_headless_render_clear'): lib.ratatui_headless_render_clear
    if hasattr(lib, 'ratatui_ratatuilogo_draw_in'): lib.ratatui_ratatuilogo_draw_in
    if hasattr(lib, 'ratatui_ratatuilogo_draw_sized_in'): lib.ratatui_ratatuilogo_draw_sized_in
    if hasattr(lib, 'ratatui_headless_render_ratatuilogo'): lib.ratatui_headless_render_ratatuilogo
    if hasattr(lib, 'ratatui_headless_render_ratatuilogo_sized'): lib.ratatui_headless_render_ratatuilogo_sized
    if hasattr(lib, 'ratatui_headless_render_frame_styles'): lib.ratatui_headless_render_frame_styles

    # Ensure explicit attribute references for remaining advanced exports
    if hasattr(lib, 'ratatui_barchart_set_bar_gap'): lib.ratatui_barchart_set_bar_gap
    if hasattr(lib, 'ratatui_barchart_set_bar_width'): lib.ratatui_barchart_set_bar_width
    if hasattr(lib, 'ratatui_barchart_set_styles'): lib.ratatui_barchart_set_styles
    if hasattr(lib, 'ratatui_barchart_set_block_adv'): lib.ratatui_barchart_set_block_adv
    if hasattr(lib, 'ratatui_barchart_set_block_title_alignment'): lib.ratatui_barchart_set_block_title_alignment
    if hasattr(lib, 'ratatui_chart_add_dataset_with_type'): lib.ratatui_chart_add_dataset_with_type
    if hasattr(lib, 'ratatui_chart_add_datasets'): lib.ratatui_chart_add_datasets
    if hasattr(lib, 'ratatui_chart_reserve_datasets'): lib.ratatui_chart_reserve_datasets
    if hasattr(lib, 'ratatui_chart_set_axis_styles'): lib.ratatui_chart_set_axis_styles
    if hasattr(lib, 'ratatui_chart_set_block_adv'): lib.ratatui_chart_set_block_adv
    if hasattr(lib, 'ratatui_chart_set_block_title_alignment'): lib.ratatui_chart_set_block_title_alignment
    if hasattr(lib, 'ratatui_chart_set_bounds'): lib.ratatui_chart_set_bounds
    if hasattr(lib, 'ratatui_chart_set_hidden_legend_constraints'): lib.ratatui_chart_set_hidden_legend_constraints
    if hasattr(lib, 'ratatui_chart_set_labels_alignment'): lib.ratatui_chart_set_labels_alignment
    if hasattr(lib, 'ratatui_chart_set_legend_position'): lib.ratatui_chart_set_legend_position
    if hasattr(lib, 'ratatui_chart_set_style'): lib.ratatui_chart_set_style
    if hasattr(lib, 'ratatui_chart_set_x_labels_spans'):
        lib.ratatui_chart_set_x_labels_spans.argtypes = [C.c_void_p, C.POINTER(FfiLineSpans), C.c_size_t]
    if hasattr(lib, 'ratatui_chart_set_y_labels_spans'):
        lib.ratatui_chart_set_y_labels_spans.argtypes = [C.c_void_p, C.POINTER(FfiLineSpans), C.c_size_t]
    if hasattr(lib, 'ratatui_headless_render_list_state'): lib.ratatui_headless_render_list_state
    if hasattr(lib, 'ratatui_linegauge_new'): lib.ratatui_linegauge_new
    if hasattr(lib, 'ratatui_linegauge_free'): lib.ratatui_linegauge_free
    if hasattr(lib, 'ratatui_linegauge_set_block_adv'): lib.ratatui_linegauge_set_block_adv
    if hasattr(lib, 'ratatui_linegauge_set_block_title'): lib.ratatui_linegauge_set_block_title
    if hasattr(lib, 'ratatui_linegauge_set_block_title_alignment'): lib.ratatui_linegauge_set_block_title_alignment
    if hasattr(lib, 'ratatui_linegauge_set_label'): lib.ratatui_linegauge_set_label
    if hasattr(lib, 'ratatui_linegauge_set_ratio'): lib.ratatui_linegauge_set_ratio
    if hasattr(lib, 'ratatui_linegauge_set_style'): lib.ratatui_linegauge_set_style
    if hasattr(lib, 'ratatui_list_append_item_spans'): lib.ratatui_list_append_item_spans
    if hasattr(lib, 'ratatui_list_reserve_items'): lib.ratatui_list_reserve_items
    if hasattr(lib, 'ratatui_list_set_block_adv'): lib.ratatui_list_set_block_adv
    if hasattr(lib, 'ratatui_list_set_block_title_alignment'): lib.ratatui_list_set_block_title_alignment
    if hasattr(lib, 'ratatui_list_set_direction'): lib.ratatui_list_set_direction
    if hasattr(lib, 'ratatui_list_set_scroll_offset'): lib.ratatui_list_set_scroll_offset
    if hasattr(lib, 'ratatui_list_state_new'): lib.ratatui_list_state_new
    if hasattr(lib, 'ratatui_list_state_free'): lib.ratatui_list_state_free
    if hasattr(lib, 'ratatui_list_state_set_offset'): lib.ratatui_list_state_set_offset
    if hasattr(lib, 'ratatui_list_state_set_selected'): lib.ratatui_list_state_set_selected
    if hasattr(lib, 'ratatui_paragraph_append_line_spans'): lib.ratatui_paragraph_append_line_spans
    if hasattr(lib, 'ratatui_paragraph_append_lines_spans'): lib.ratatui_paragraph_append_lines_spans
    if hasattr(lib, 'ratatui_paragraph_reserve_lines'): lib.ratatui_paragraph_reserve_lines
    if hasattr(lib, 'ratatui_paragraph_set_block_adv'): lib.ratatui_paragraph_set_block_adv
    if hasattr(lib, 'ratatui_paragraph_set_scroll'): lib.ratatui_paragraph_set_scroll
    if hasattr(lib, 'ratatui_paragraph_set_style'): lib.ratatui_paragraph_set_style
    if hasattr(lib, 'ratatui_paragraph_set_wrap'): lib.ratatui_paragraph_set_wrap
    if hasattr(lib, 'ratatui_scrollbar_set_block_adv'): lib.ratatui_scrollbar_set_block_adv
    if hasattr(lib, 'ratatui_scrollbar_set_block_title_alignment'): lib.ratatui_scrollbar_set_block_title_alignment
    if hasattr(lib, 'ratatui_scrollbar_set_orientation_side'): lib.ratatui_scrollbar_set_orientation_side
    if hasattr(lib, 'ratatui_sparkline_set_block_adv'): lib.ratatui_sparkline_set_block_adv
    if hasattr(lib, 'ratatui_sparkline_set_block_title_alignment'): lib.ratatui_sparkline_set_block_title_alignment
    if hasattr(lib, 'ratatui_sparkline_set_max'): lib.ratatui_sparkline_set_max
    if hasattr(lib, 'ratatui_sparkline_set_style'): lib.ratatui_sparkline_set_style
    if hasattr(lib, 'ratatui_table_append_row_spans'): lib.ratatui_table_append_row_spans
    if hasattr(lib, 'ratatui_table_append_rows_cells_lines'): lib.ratatui_table_append_rows_cells_lines
    if hasattr(lib, 'ratatui_table_reserve_rows'): lib.ratatui_table_reserve_rows
    if hasattr(lib, 'ratatui_table_set_block_adv'): lib.ratatui_table_set_block_adv
    if hasattr(lib, 'ratatui_table_set_block_title_alignment'): lib.ratatui_table_set_block_title_alignment
    if hasattr(lib, 'ratatui_table_set_cell_highlight_style'): lib.ratatui_table_set_cell_highlight_style
    if hasattr(lib, 'ratatui_table_set_column_highlight_style'): lib.ratatui_table_set_column_highlight_style
    if hasattr(lib, 'ratatui_table_set_column_spacing'): lib.ratatui_table_set_column_spacing
    if hasattr(lib, 'ratatui_table_set_header_style'): lib.ratatui_table_set_header_style
    if hasattr(lib, 'ratatui_table_set_highlight_spacing'): lib.ratatui_table_set_highlight_spacing
    if hasattr(lib, 'ratatui_table_set_row_height'): lib.ratatui_table_set_row_height
    if hasattr(lib, 'ratatui_table_set_widths'): lib.ratatui_table_set_widths
    if hasattr(lib, 'ratatui_table_set_widths_percentages'): lib.ratatui_table_set_widths_percentages
    if hasattr(lib, 'ratatui_table_state_new'): lib.ratatui_table_state_new
    if hasattr(lib, 'ratatui_table_state_free'): lib.ratatui_table_state_free
    if hasattr(lib, 'ratatui_table_state_set_offset'): lib.ratatui_table_state_set_offset
    if hasattr(lib, 'ratatui_table_state_set_selected'): lib.ratatui_table_state_set_selected
    if hasattr(lib, 'ratatui_tabs_add_title_spans'): lib.ratatui_tabs_add_title_spans
    if hasattr(lib, 'ratatui_tabs_clear_titles'): lib.ratatui_tabs_clear_titles
    if hasattr(lib, 'ratatui_tabs_set_block_adv'): lib.ratatui_tabs_set_block_adv
    if hasattr(lib, 'ratatui_tabs_set_block_title_alignment'): lib.ratatui_tabs_set_block_title_alignment
    if hasattr(lib, 'ratatui_tabs_set_divider'): lib.ratatui_tabs_set_divider
    if hasattr(lib, 'ratatui_tabs_set_styles'): lib.ratatui_tabs_set_styles
    if hasattr(lib, 'ratatui_terminal_draw_linegauge_in'): lib.ratatui_terminal_draw_linegauge_in
    if hasattr(lib, 'ratatui_headless_render_linegauge'): lib.ratatui_headless_render_linegauge
    if hasattr(lib, 'ratatui_gauge_set_styles'): lib.ratatui_gauge_set_styles
    if hasattr(lib, 'ratatui_gauge_set_block_adv'): lib.ratatui_gauge_set_block_adv
    if hasattr(lib, 'ratatui_gauge_set_block_title_alignment'): lib.ratatui_gauge_set_block_title_alignment
    if hasattr(lib, 'ratatui_terminal_draw_list_state_in'): lib.ratatui_terminal_draw_list_state_in
    if hasattr(lib, 'ratatui_terminal_draw_table_state_in'): lib.ratatui_terminal_draw_table_state_in

    _cached_lib = lib
    return lib

# ----- Additional enums for input/mouse/scrollbar -----

FFI_MOUSE_KIND = {
    "Down": 1,
    "Up": 2,
    "Drag": 3,
    "Moved": 4,
    "ScrollUp": 5,
    "ScrollDown": 6,
}

FFI_MOUSE_BUTTON = {
    "None": 0,
    "Left": 1,
    "Right": 2,
    "Middle": 3,
}

# Orientation for optional scrollbar feature; presence depends on build features
FFI_SCROLLBAR_ORIENT = {
    "Vertical": 0,
    "Horizontal": 1,
}
