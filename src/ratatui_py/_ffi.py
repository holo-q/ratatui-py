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
    if hasattr(lib, 'ratatui_list_set_highlight_spacing'):
        lib.ratatui_list_set_highlight_spacing.argtypes = [C.c_void_p, C.c_uint]
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

    # Chart
    lib.ratatui_chart_new.restype = C.c_void_p
    lib.ratatui_chart_free.argtypes = [C.c_void_p]
    lib.ratatui_chart_add_line.argtypes = [C.c_void_p, C.c_char_p, C.POINTER(C.c_double), C.c_size_t, FfiStyle]
    lib.ratatui_chart_set_axes_titles.argtypes = [C.c_void_p, C.c_char_p, C.c_char_p]
    lib.ratatui_chart_set_block_title.argtypes = [C.c_void_p, C.c_char_p, C.c_bool]
    lib.ratatui_terminal_draw_chart_in.argtypes = [C.c_void_p, C.c_void_p, FfiRect]
    lib.ratatui_terminal_draw_chart_in.restype = C.c_bool
    lib.ratatui_headless_render_chart.argtypes = [C.c_uint16, C.c_uint16, C.c_void_p, C.POINTER(C.c_char_p)]
    lib.ratatui_headless_render_chart.restype = C.c_bool

    # Sparkline
    lib.ratatui_sparkline_new.restype = C.c_void_p
    lib.ratatui_sparkline_free.argtypes = [C.c_void_p]
    lib.ratatui_sparkline_set_values.argtypes = [C.c_void_p, C.POINTER(C.c_uint64), C.c_size_t]
    lib.ratatui_sparkline_set_block_title.argtypes = [C.c_void_p, C.c_char_p, C.c_bool]
    lib.ratatui_terminal_draw_sparkline_in.argtypes = [C.c_void_p, C.c_void_p, FfiRect]
    lib.ratatui_terminal_draw_sparkline_in.restype = C.c_bool
    lib.ratatui_headless_render_sparkline.argtypes = [C.c_uint16, C.c_uint16, C.c_void_p, C.POINTER(C.c_char_p)]
    lib.ratatui_headless_render_sparkline.restype = C.c_bool

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
