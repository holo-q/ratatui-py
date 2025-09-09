import os
import sys
import ctypes as C
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

# ----- Library loader -----

def _default_names():
    if sys.platform.startswith("win"):
        return ["ratatui_ffi.dll"]
    elif sys.platform == "darwin":
        return ["libratatui_ffi.dylib"]
    else:
        return ["libratatui_ffi.so", "ratatui_ffi"]

_cached_lib = None

def load_library(explicit: str | None = None) -> C.CDLL:
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
    lib.ratatui_init_terminal.restype = C.c_void_p
    lib.ratatui_terminal_clear.argtypes = [C.c_void_p]
    lib.ratatui_terminal_free.argtypes = [C.c_void_p]

    lib.ratatui_paragraph_new.argtypes = [C.c_char_p]
    lib.ratatui_paragraph_new.restype = C.c_void_p
    lib.ratatui_paragraph_set_block_title.argtypes = [C.c_void_p, C.c_char_p, C.c_bool]
    lib.ratatui_paragraph_free.argtypes = [C.c_void_p]
    lib.ratatui_paragraph_append_line.argtypes = [C.c_void_p, C.c_char_p, FfiStyle]

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

    # Gauge
    lib.ratatui_gauge_new.restype = C.c_void_p
    lib.ratatui_gauge_free.argtypes = [C.c_void_p]
    lib.ratatui_gauge_set_ratio.argtypes = [C.c_void_p, C.c_float]
    lib.ratatui_gauge_set_label.argtypes = [C.c_void_p, C.c_char_p]
    lib.ratatui_gauge_set_block_title.argtypes = [C.c_void_p, C.c_char_p, C.c_bool]
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
