import os
import sys
import ctypes as C
from ctypes.util import find_library

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

    _cached_lib = lib
    return lib
