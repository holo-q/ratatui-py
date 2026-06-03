# GENERATED from bindings.json by tools/gen_ffi.py — DO NOT EDIT. Regenerate with `just gen`. ffi=0.2.6 ratatui=0.30

import os
import sys
import ctypes as C
from typing import Optional
from ctypes.util import find_library
from pathlib import Path
import shutil
import tempfile
import subprocess

# ----- Value-struct layouts (C ABI, dependency-ordered) -----

class FfiAccentedPaletteU32(C.Structure):
    _fields_ = [
        ("c50", C.c_uint32),
        ("c100", C.c_uint32),
        ("c200", C.c_uint32),
        ("c300", C.c_uint32),
        ("c400", C.c_uint32),
        ("c500", C.c_uint32),
        ("c600", C.c_uint32),
        ("c700", C.c_uint32),
        ("c800", C.c_uint32),
        ("c900", C.c_uint32),
        ("a100", C.c_uint32),
        ("a200", C.c_uint32),
        ("a400", C.c_uint32),
        ("a700", C.c_uint32),
    ]

class FfiStyle(C.Structure):
    _fields_ = [
        ("fg", C.c_uint32),
        ("bg", C.c_uint32),
        ("mods", C.c_uint16),
    ]

class FfiCanvasLine(C.Structure):
    _fields_ = [
        ("x1", C.c_double),
        ("y1", C.c_double),
        ("x2", C.c_double),
        ("y2", C.c_double),
        ("style", FfiStyle),
    ]

class FfiCanvasPoints(C.Structure):
    _fields_ = [
        ("points_xy", C.c_void_p),
        ("len_pairs", C.c_size_t),
        ("style", FfiStyle),
        ("marker", C.c_uint32),
    ]

class FfiCanvasRect(C.Structure):
    _fields_ = [
        ("x", C.c_double),
        ("y", C.c_double),
        ("w", C.c_double),
        ("h", C.c_double),
        ("style", FfiStyle),
        ("filled", C.c_bool),
    ]

class FfiCellInfo(C.Structure):
    _fields_ = [
        ("ch", C.c_uint32),
        ("fg", C.c_uint32),
        ("bg", C.c_uint32),
        ("mods", C.c_uint16),
    ]

class FfiCellLines(C.Structure):
    _fields_ = [
        ("lines", C.c_void_p),
        ("len", C.c_size_t),
    ]

class FfiChartDatasetSpec(C.Structure):
    _fields_ = [
        ("name_utf8", C.c_char_p),
        ("points_xy", C.c_void_p),
        ("len_pairs", C.c_size_t),
        ("style", FfiStyle),
        ("kind", C.c_uint32),
    ]

class FfiRect(C.Structure):
    _fields_ = [
        ("x", C.c_uint16),
        ("y", C.c_uint16),
        ("width", C.c_uint16),
        ("height", C.c_uint16),
    ]

class FfiDrawCmd(C.Structure):
    _fields_ = [
        ("kind", C.c_uint32),
        ("handle", C.c_void_p),
        ("rect", FfiRect),
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

class FfiLineSpans(C.Structure):
    _fields_ = [
        ("spans", C.c_void_p),
        ("len", C.c_size_t),
    ]

class FfiMarginDto(C.Structure):
    _fields_ = [
        ("horizontal", C.c_uint16),
        ("vertical", C.c_uint16),
    ]

class FfiNonAccentedPaletteU32(C.Structure):
    _fields_ = [
        ("c50", C.c_uint32),
        ("c100", C.c_uint32),
        ("c200", C.c_uint32),
        ("c300", C.c_uint32),
        ("c400", C.c_uint32),
        ("c500", C.c_uint32),
        ("c600", C.c_uint32),
        ("c700", C.c_uint32),
        ("c800", C.c_uint32),
        ("c900", C.c_uint32),
    ]

class FfiOffsetDto(C.Structure):
    _fields_ = [
        ("x", C.c_int32),
        ("y", C.c_int32),
    ]

class FfiPositionDto(C.Structure):
    _fields_ = [
        ("x", C.c_uint16),
        ("y", C.c_uint16),
    ]

class FfiRowCellsLines(C.Structure):
    _fields_ = [
        ("cells", C.c_void_p),
        ("len", C.c_size_t),
    ]

class FfiSizeDto(C.Structure):
    _fields_ = [
        ("width", C.c_uint16),
        ("height", C.c_uint16),
    ]

class FfiSpan(C.Structure):
    _fields_ = [
        ("text_utf8", C.c_char_p),
        ("style", FfiStyle),
    ]

class FfiStr(C.Structure):
    _fields_ = [
        ("ptr", C.c_void_p),
        ("len", C.c_size_t),
    ]

class FfiSymbolsBarSet(C.Structure):
    _fields_ = [
        ("full", FfiStr),
        ("seven_eighths", FfiStr),
        ("three_quarters", FfiStr),
        ("five_eighths", FfiStr),
        ("half", FfiStr),
        ("three_eighths", FfiStr),
        ("one_quarter", FfiStr),
        ("one_eighth", FfiStr),
        ("empty", FfiStr),
    ]

class FfiSymbolsBlockSet(C.Structure):
    _fields_ = [
        ("full", FfiStr),
        ("seven_eighths", FfiStr),
        ("three_quarters", FfiStr),
        ("five_eighths", FfiStr),
        ("half", FfiStr),
        ("three_eighths", FfiStr),
        ("one_quarter", FfiStr),
        ("one_eighth", FfiStr),
        ("empty", FfiStr),
    ]

class FfiSymbolsBorderSet(C.Structure):
    _fields_ = [
        ("top_left", FfiStr),
        ("top_right", FfiStr),
        ("bottom_left", FfiStr),
        ("bottom_right", FfiStr),
        ("vertical_left", FfiStr),
        ("vertical_right", FfiStr),
        ("horizontal_top", FfiStr),
        ("horizontal_bottom", FfiStr),
    ]

class FfiSymbolsLineSet(C.Structure):
    _fields_ = [
        ("vertical", FfiStr),
        ("horizontal", FfiStr),
        ("top_right", FfiStr),
        ("top_left", FfiStr),
        ("bottom_right", FfiStr),
        ("bottom_left", FfiStr),
        ("vertical_left", FfiStr),
        ("vertical_right", FfiStr),
        ("horizontal_down", FfiStr),
        ("horizontal_up", FfiStr),
        ("cross", FfiStr),
    ]

class FfiSymbolsScrollbarSet(C.Structure):
    _fields_ = [
        ("track", FfiStr),
        ("thumb", FfiStr),
        ("begin", FfiStr),
        ("end", FfiStr),
    ]

class FfiTabsStyles(C.Structure):
    _fields_ = [
        ("unselected", FfiStyle),
        ("selected", FfiStyle),
    ]

class FfiTailwindPaletteU32(C.Structure):
    _fields_ = [
        ("c50", C.c_uint32),
        ("c100", C.c_uint32),
        ("c200", C.c_uint32),
        ("c300", C.c_uint32),
        ("c400", C.c_uint32),
        ("c500", C.c_uint32),
        ("c600", C.c_uint32),
        ("c700", C.c_uint32),
        ("c800", C.c_uint32),
        ("c900", C.c_uint32),
        ("c950", C.c_uint32),
    ]

class FfiU16Slice(C.Structure):
    _fields_ = [
        ("ptr", C.c_void_p),
        ("len", C.c_size_t),
    ]

# ----- Enums (named int constants) -----

FFI_ALIGN = {
    "Center": 0,
    "Left": 1,
    "Right": 2,
}

FFI_BORDER_TYPE = {
    "Double": 0,
    "Plain": 1,
    "QuadrantInside": 2,
    "QuadrantOutside": 3,
    "Rounded": 4,
    "Thick": 5,
}

FFI_CLEAR_TYPE = {
    "All": 0,
    "AfterCursor": 1,
    "BeforeCursor": 2,
    "CurrentLine": 3,
    "UntilNewLine": 4,
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
    "Indexed": 17,
    "Rgb": 18,
}

FFI_CONSTRAINT = {
    "Min": 0,
    "Max": 1,
    "Length": 2,
    "Percentage": 3,
    "Ratio": 4,
    "Fill": 5,
}

FFI_CONSTRAINT_KIND = {
    "Length": 0,
    "Percentage": 1,
    "Min": 2,
}

FFI_DIRECTION = {
    "Horizontal": 0,
    "Vertical": 1,
}

FFI_EVENT_KIND = {
    "None": 0,
    "Key": 1,
    "Resize": 2,
    "Mouse": 3,
}

FFI_FLEX = {
    "Center": 0,
    "End": 1,
    "Legacy": 2,
    "SpaceAround": 3,
    "SpaceBetween": 4,
    "Start": 5,
}

FFI_GRAPH_TYPE = {
    "Bar": 0,
    "Line": 1,
    "Scatter": 2,
}

FFI_HIGHLIGHT_SPACING = {
    "Always": 0,
    "Never": 1,
    "WhenSelected": 2,
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

FFI_LEGEND_POSITION = {
    "Bottom": 0,
    "BottomLeft": 1,
    "BottomRight": 2,
    "Left": 3,
    "Right": 4,
    "Top": 5,
    "TopLeft": 6,
    "TopRight": 7,
}

FFI_LIST_DIRECTION = {
    "BottomToTop": 0,
    "TopToBottom": 1,
}

FFI_MAP_RESOLUTION = {
    "Low": 0,
    "High": 1,
}

FFI_MARKER = {
    "Bar": 0,
    "Block": 1,
    "Braille": 2,
    "Dot": 3,
    "HalfBlock": 4,
}

FFI_MASCOT_EYE = {
    "Default": 0,
    "Red": 1,
}

FFI_MOUSE_BUTTON = {
    "Left": 1,
    "Right": 2,
    "Middle": 3,
    "None": 0,
}

FFI_MOUSE_KIND = {
    "Down": 1,
    "Up": 2,
    "Drag": 3,
    "Moved": 4,
    "ScrollUp": 5,
    "ScrollDown": 6,
}

FFI_POSITION = {
    "Bottom": 0,
    "Top": 1,
}

FFI_RENDER_DIRECTION = {
    "LeftToRight": 0,
    "RightToLeft": 1,
}

FFI_SCROLL_DIRECTION = {
    "Forward": 0,
    "Backward": 1,
}

FFI_SCROLLBAR_ORIENT = {
    "Vertical": 0,
    "Horizontal": 1,
}

FFI_SCROLLBAR_ORIENTATION = {
    "VerticalRight": 0,
    "VerticalLeft": 1,
    "HorizontalBottom": 2,
    "HorizontalTop": 3,
}

FFI_SIZE = {
    "Tiny": 0,
    "Small": 1,
}

FFI_SPACING = {
    "Space": 0,
    "Overlap": 1,
}

FFI_VIEWPORT = {
    "Fullscreen": 0,
    "Inline": 1,
    "Fixed": 2,
}

FFI_WIDGET_KIND = {
    "Paragraph": 1,
    "List": 2,
    "Table": 3,
    "Gauge": 4,
    "Tabs": 5,
    "BarChart": 6,
    "Sparkline": 7,
    "Chart": 8,
    "Scrollbar": 9,
    "LineGauge": 10,
    "Clear": 11,
    "RatatuiLogo": 12,
    "Canvas": 13,
}

# ----- Bitflags (named int constants) -----

FFI_BORDERS = {
    "NONE": 0,
    "LEFT": 1,
    "RIGHT": 2,
    "TOP": 4,
    "BOTTOM": 8,
}

FFI_FEATURES = {
    "SCROLLBAR": 1,
    "CANVAS": 2,
    "STYLE_DUMP_EX": 4,
    "BATCH_TABLE_ROWS": 8,
    "BATCH_LIST_ITEMS": 16,
    "COLOR_HELPERS": 32,
    "AXIS_LABELS": 64,
    "SPAN_SETTERS": 128,
}

FFI_KEY_MODS = {
    "NONE": 0,
    "SHIFT": 1,
    "ALT": 2,
    "CTRL": 4,
}

FFI_STYLE_MODS = {
    "NONE": 0,
    "BOLD": 1,
    "ITALIC": 2,
    "UNDERLINE": 4,
    "DIM": 8,
    "CROSSED": 16,
    "REVERSED": 32,
    "RAPIDBLINK": 64,
    "SLOWBLINK": 128,
    "HIDDEN": 256,
}

# Layout direction is passed as a raw c_uint to ratatui_layout_split*; the IR
# does not model it as an enum, but the ergonomic layer (layout.py) imports it.
FFI_LAYOUT_DIR = {"Vertical": 0, "Horizontal": 1}

# ----- Library loader / resolver -----

def _default_names():
    if sys.platform.startswith("win"):
        return ["ratatui_ffi.dll"]
    elif sys.platform == "darwin":
        return ["libratatui_ffi.dylib"]
    else:
        return ["libratatui_ffi.so", "ratatui_ffi"]


_cached_lib = None


def _resolve_library(explicit: Optional[str] = None) -> C.CDLL:
    path = explicit or os.getenv("RATATUI_FFI_LIB")
    if path and os.path.exists(path):
        return C.CDLL(path)
    pkg_dir = Path(__file__).resolve().parent
    bundled = pkg_dir / "_bundled"
    plat = (
        "ratatui_ffi.dll"
        if sys.platform.startswith("win")
        else ("libratatui_ffi.dylib" if sys.platform == "darwin" else "libratatui_ffi.so")
    )
    candidate = bundled / plat
    if candidate.exists():
        try:
            return C.CDLL(str(candidate))
        except OSError:
            pass
    libname = find_library("ratatui_ffi")
    if libname:
        try:
            return C.CDLL(libname)
        except OSError:
            pass
    last_err = None
    for name in _default_names():
        try:
            return C.CDLL(name)
        except OSError as e:
            last_err = e
    auto = os.getenv("RATATUI_FFI_AUTO_BUILD", "1")
    if auto != "0" and shutil.which("cargo"):
        try:
            git_url = os.getenv("RATATUI_FFI_GIT", "https://github.com/holo-q/ratatui-ffi.git")
            tag = os.getenv("RATATUI_FFI_TAG", "v0.2.1")
            cache_dir = Path(os.getenv("XDG_CACHE_HOME", Path.home() / ".cache")) / "ratatui-py" / "ffi" / tag
            cache_dir.mkdir(parents=True, exist_ok=True)
            dst = cache_dir / plat
            if not dst.exists():
                if os.getenv("RATATUI_FFI_PROGRESS", "1") not in ("0", "false", "False", ""):
                    sys.stderr.write(f"ratatui-py: building ratatui_ffi {tag} (first run) ...\n")
                    sys.stderr.flush()
                with tempfile.TemporaryDirectory() as td:
                    subprocess.check_call(["git", "init"], cwd=td)
                    subprocess.check_call(["git", "remote", "add", "origin", git_url], cwd=td)
                    subprocess.check_call(["git", "fetch", "--depth", "1", "origin", tag], cwd=td)
                    subprocess.check_call(["git", "checkout", "FETCH_HEAD"], cwd=td)
                    subprocess.check_call(["cargo", "build", "--release"], cwd=td)
                    built = Path(td) / "target" / "release" / dst.name
                    if not built.exists():
                        raise FileNotFoundError(str(built))
                    shutil.copy2(built, dst)
            return C.CDLL(str(dst))
        except Exception as e:
            raise RuntimeError(
                "Failed to auto-build ratatui_ffi; install Rust/cargo, set RATATUI_FFI_LIB "
                "to a prebuilt library, or disable auto-build with RATATUI_FFI_AUTO_BUILD=0."
            ) from e
    raise RuntimeError(
        "No bundled or system ratatui_ffi found. Set RATATUI_FFI_LIB to a prebuilt "
        ".so/.dylib/.dll, or install Rust (cargo) and enable auto-build via RATATUI_FFI_AUTO_BUILD=1."
    ) from last_err


def load_library(explicit: Optional[str] = None) -> C.CDLL:
    global _cached_lib
    if _cached_lib is not None:
        return _cached_lib
    lib = _resolve_library(explicit)
    _bind_prototypes(lib)
    _cached_lib = lib
    return lib


def _bind_prototypes(lib: C.CDLL) -> None:
    # All 350 exports — argtypes/restype per the FFI ABI manifest.
    lib.ratatui_bar_get_nine_levels.argtypes = []
    lib.ratatui_bar_get_nine_levels.restype = FfiSymbolsBarSet
    lib.ratatui_bar_get_three_levels.argtypes = []
    lib.ratatui_bar_get_three_levels.restype = FfiSymbolsBarSet
    lib.ratatui_barchart_free.argtypes = [C.c_void_p]
    lib.ratatui_barchart_new.argtypes = []
    lib.ratatui_barchart_new.restype = C.c_void_p
    lib.ratatui_barchart_set_bar_gap.argtypes = [C.c_void_p, C.c_uint16]
    lib.ratatui_barchart_set_bar_width.argtypes = [C.c_void_p, C.c_uint16]
    lib.ratatui_barchart_set_block_adv.argtypes = [C.c_void_p, C.c_uint8, C.c_uint32, C.c_uint16, C.c_uint16, C.c_uint16, C.c_uint16, C.c_void_p, C.c_size_t]
    lib.ratatui_barchart_set_block_title.argtypes = [C.c_void_p, C.c_char_p, C.c_bool]
    lib.ratatui_barchart_set_block_title_spans.argtypes = [C.c_void_p, C.c_void_p, C.c_size_t, C.c_bool]
    lib.ratatui_barchart_set_labels.argtypes = [C.c_void_p, C.c_char_p]
    lib.ratatui_barchart_set_labels_spans.argtypes = [C.c_void_p, C.c_void_p, C.c_size_t]
    lib.ratatui_barchart_set_styles.argtypes = [C.c_void_p, FfiStyle, FfiStyle, FfiStyle]
    lib.ratatui_barchart_set_values.argtypes = [C.c_void_p, C.c_void_p, C.c_size_t]
    lib.ratatui_block_get_nine_levels.argtypes = []
    lib.ratatui_block_get_nine_levels.restype = FfiSymbolsBlockSet
    lib.ratatui_block_get_three_levels.argtypes = []
    lib.ratatui_block_get_three_levels.restype = FfiSymbolsBlockSet
    lib.ratatui_border_get_double.argtypes = []
    lib.ratatui_border_get_double.restype = FfiSymbolsBorderSet
    lib.ratatui_border_get_empty.argtypes = []
    lib.ratatui_border_get_empty.restype = FfiSymbolsBorderSet
    lib.ratatui_border_get_full.argtypes = []
    lib.ratatui_border_get_full.restype = FfiSymbolsBorderSet
    lib.ratatui_border_get_one_eighth_bottom_eight.argtypes = []
    lib.ratatui_border_get_one_eighth_bottom_eight.restype = FfiStr
    lib.ratatui_border_get_one_eighth_left_eight.argtypes = []
    lib.ratatui_border_get_one_eighth_left_eight.restype = FfiStr
    lib.ratatui_border_get_one_eighth_right_eight.argtypes = []
    lib.ratatui_border_get_one_eighth_right_eight.restype = FfiStr
    lib.ratatui_border_get_one_eighth_tall.argtypes = []
    lib.ratatui_border_get_one_eighth_tall.restype = FfiSymbolsBorderSet
    lib.ratatui_border_get_one_eighth_top_eight.argtypes = []
    lib.ratatui_border_get_one_eighth_top_eight.restype = FfiStr
    lib.ratatui_border_get_one_eighth_wide.argtypes = []
    lib.ratatui_border_get_one_eighth_wide.restype = FfiSymbolsBorderSet
    lib.ratatui_border_get_plain.argtypes = []
    lib.ratatui_border_get_plain.restype = FfiSymbolsBorderSet
    lib.ratatui_border_get_proportional_tall.argtypes = []
    lib.ratatui_border_get_proportional_tall.restype = FfiSymbolsBorderSet
    lib.ratatui_border_get_proportional_wide.argtypes = []
    lib.ratatui_border_get_proportional_wide.restype = FfiSymbolsBorderSet
    lib.ratatui_border_get_quadrant_block.argtypes = []
    lib.ratatui_border_get_quadrant_block.restype = FfiStr
    lib.ratatui_border_get_quadrant_bottom_half.argtypes = []
    lib.ratatui_border_get_quadrant_bottom_half.restype = FfiStr
    lib.ratatui_border_get_quadrant_bottom_left.argtypes = []
    lib.ratatui_border_get_quadrant_bottom_left.restype = FfiStr
    lib.ratatui_border_get_quadrant_bottom_right.argtypes = []
    lib.ratatui_border_get_quadrant_bottom_right.restype = FfiStr
    lib.ratatui_border_get_quadrant_inside.argtypes = []
    lib.ratatui_border_get_quadrant_inside.restype = FfiSymbolsBorderSet
    lib.ratatui_border_get_quadrant_left_half.argtypes = []
    lib.ratatui_border_get_quadrant_left_half.restype = FfiStr
    lib.ratatui_border_get_quadrant_outside.argtypes = []
    lib.ratatui_border_get_quadrant_outside.restype = FfiSymbolsBorderSet
    lib.ratatui_border_get_quadrant_right_half.argtypes = []
    lib.ratatui_border_get_quadrant_right_half.restype = FfiStr
    lib.ratatui_border_get_quadrant_top_half.argtypes = []
    lib.ratatui_border_get_quadrant_top_half.restype = FfiStr
    lib.ratatui_border_get_quadrant_top_left.argtypes = []
    lib.ratatui_border_get_quadrant_top_left.restype = FfiStr
    lib.ratatui_border_get_quadrant_top_left_bottom_left_bottom_right.argtypes = []
    lib.ratatui_border_get_quadrant_top_left_bottom_left_bottom_right.restype = FfiStr
    lib.ratatui_border_get_quadrant_top_left_bottom_right.argtypes = []
    lib.ratatui_border_get_quadrant_top_left_bottom_right.restype = FfiStr
    lib.ratatui_border_get_quadrant_top_left_top_right_bottom_left.argtypes = []
    lib.ratatui_border_get_quadrant_top_left_top_right_bottom_left.restype = FfiStr
    lib.ratatui_border_get_quadrant_top_left_top_right_bottom_right.argtypes = []
    lib.ratatui_border_get_quadrant_top_left_top_right_bottom_right.restype = FfiStr
    lib.ratatui_border_get_quadrant_top_right.argtypes = []
    lib.ratatui_border_get_quadrant_top_right.restype = FfiStr
    lib.ratatui_border_get_quadrant_top_right_bottom_left.argtypes = []
    lib.ratatui_border_get_quadrant_top_right_bottom_left.restype = FfiStr
    lib.ratatui_border_get_quadrant_top_right_bottom_left_bottom_right.argtypes = []
    lib.ratatui_border_get_quadrant_top_right_bottom_left_bottom_right.restype = FfiStr
    lib.ratatui_border_get_rounded.argtypes = []
    lib.ratatui_border_get_rounded.restype = FfiSymbolsBorderSet
    lib.ratatui_border_get_thick.argtypes = []
    lib.ratatui_border_get_thick.restype = FfiSymbolsBorderSet
    lib.ratatui_canvas_add_line.argtypes = [C.c_void_p, C.c_double, C.c_double, C.c_double, C.c_double, FfiStyle]
    lib.ratatui_canvas_add_points.argtypes = [C.c_void_p, C.c_void_p, C.c_size_t, FfiStyle, C.c_uint32]
    lib.ratatui_canvas_add_rect.argtypes = [C.c_void_p, C.c_double, C.c_double, C.c_double, C.c_double, FfiStyle, C.c_bool]
    lib.ratatui_canvas_free.argtypes = [C.c_void_p]
    lib.ratatui_canvas_new.argtypes = [C.c_double, C.c_double, C.c_double, C.c_double]
    lib.ratatui_canvas_new.restype = C.c_void_p
    lib.ratatui_canvas_set_background_color.argtypes = [C.c_void_p, C.c_uint32]
    lib.ratatui_canvas_set_block_adv.argtypes = [C.c_void_p, C.c_uint8, C.c_uint32, C.c_uint16, C.c_uint16, C.c_uint16, C.c_uint16, C.c_void_p, C.c_size_t]
    lib.ratatui_canvas_set_block_title.argtypes = [C.c_void_p, C.c_char_p, C.c_bool]
    lib.ratatui_canvas_set_block_title_alignment.argtypes = [C.c_void_p, C.c_uint32]
    lib.ratatui_canvas_set_block_title_spans.argtypes = [C.c_void_p, C.c_void_p, C.c_size_t, C.c_bool]
    lib.ratatui_canvas_set_bounds.argtypes = [C.c_void_p, C.c_double, C.c_double, C.c_double, C.c_double]
    lib.ratatui_canvas_set_marker.argtypes = [C.c_void_p, C.c_uint32]
    lib.ratatui_chart_add_dataset_with_type.argtypes = [C.c_void_p, C.c_char_p, C.c_void_p, C.c_size_t, FfiStyle, C.c_uint32]
    lib.ratatui_chart_add_datasets.argtypes = [C.c_void_p, C.c_void_p, C.c_size_t]
    lib.ratatui_chart_add_line.argtypes = [C.c_void_p, C.c_char_p, C.c_void_p, C.c_size_t, FfiStyle]
    lib.ratatui_chart_free.argtypes = [C.c_void_p]
    lib.ratatui_chart_new.argtypes = []
    lib.ratatui_chart_new.restype = C.c_void_p
    lib.ratatui_chart_set_axes_titles.argtypes = [C.c_void_p, C.c_char_p, C.c_char_p]
    lib.ratatui_chart_set_axis_styles.argtypes = [C.c_void_p, FfiStyle, FfiStyle]
    lib.ratatui_chart_set_block_adv.argtypes = [C.c_void_p, C.c_uint8, C.c_uint32, C.c_uint16, C.c_uint16, C.c_uint16, C.c_uint16, C.c_void_p, C.c_size_t]
    lib.ratatui_chart_set_block_title.argtypes = [C.c_void_p, C.c_char_p, C.c_bool]
    lib.ratatui_chart_set_block_title_spans.argtypes = [C.c_void_p, C.c_void_p, C.c_size_t, C.c_bool]
    lib.ratatui_chart_set_bounds.argtypes = [C.c_void_p, C.c_double, C.c_double, C.c_double, C.c_double]
    lib.ratatui_chart_set_hidden_legend_constraints.argtypes = [C.c_void_p, C.c_void_p, C.c_void_p]
    lib.ratatui_chart_set_labels_alignment.argtypes = [C.c_void_p, C.c_uint32, C.c_uint32]
    lib.ratatui_chart_set_legend_position.argtypes = [C.c_void_p, C.c_uint32]
    lib.ratatui_chart_set_style.argtypes = [C.c_void_p, FfiStyle]
    lib.ratatui_chart_set_x_labels_spans.argtypes = [C.c_void_p, C.c_void_p, C.c_size_t]
    lib.ratatui_chart_set_y_labels_spans.argtypes = [C.c_void_p, C.c_void_p, C.c_size_t]
    lib.ratatui_clear_in.argtypes = [C.c_void_p, FfiRect]
    lib.ratatui_clear_in.restype = C.c_bool
    lib.ratatui_color_indexed.argtypes = [C.c_uint8]
    lib.ratatui_color_indexed.restype = C.c_uint32
    lib.ratatui_color_rgb.argtypes = [C.c_uint8, C.c_uint8, C.c_uint8]
    lib.ratatui_color_rgb.restype = C.c_uint32
    lib.ratatui_ffi_feature_bits.argtypes = []
    lib.ratatui_ffi_feature_bits.restype = C.c_uint32
    lib.ratatui_ffi_version.argtypes = [C.c_void_p, C.c_void_p, C.c_void_p]
    lib.ratatui_ffi_version.restype = C.c_bool
    lib.ratatui_gauge_free.argtypes = [C.c_void_p]
    lib.ratatui_gauge_new.argtypes = []
    lib.ratatui_gauge_new.restype = C.c_void_p
    lib.ratatui_gauge_set_block_adv.argtypes = [C.c_void_p, C.c_uint8, C.c_uint32, C.c_uint16, C.c_uint16, C.c_uint16, C.c_uint16, C.c_void_p, C.c_size_t]
    lib.ratatui_gauge_set_block_title.argtypes = [C.c_void_p, C.c_char_p, C.c_bool]
    lib.ratatui_gauge_set_block_title_alignment.argtypes = [C.c_void_p, C.c_uint32]
    lib.ratatui_gauge_set_block_title_spans.argtypes = [C.c_void_p, C.c_void_p, C.c_size_t, C.c_bool]
    lib.ratatui_gauge_set_label.argtypes = [C.c_void_p, C.c_char_p]
    lib.ratatui_gauge_set_label_spans.argtypes = [C.c_void_p, C.c_void_p, C.c_size_t]
    lib.ratatui_gauge_set_ratio.argtypes = [C.c_void_p, C.c_float]
    lib.ratatui_gauge_set_styles.argtypes = [C.c_void_p, FfiStyle, FfiStyle, FfiStyle]
    lib.ratatui_half_block_get_full.argtypes = []
    lib.ratatui_half_block_get_full.restype = C.c_uint32
    lib.ratatui_half_block_get_lower.argtypes = []
    lib.ratatui_half_block_get_lower.restype = C.c_uint32
    lib.ratatui_half_block_get_upper.argtypes = []
    lib.ratatui_half_block_get_upper.restype = C.c_uint32
    lib.ratatui_headless_render_barchart.argtypes = [C.c_uint16, C.c_uint16, C.c_void_p, C.c_void_p]
    lib.ratatui_headless_render_barchart.restype = C.c_bool
    lib.ratatui_headless_render_canvas.argtypes = [C.c_uint16, C.c_uint16, C.c_void_p, C.c_void_p]
    lib.ratatui_headless_render_canvas.restype = C.c_bool
    lib.ratatui_headless_render_chart.argtypes = [C.c_uint16, C.c_uint16, C.c_void_p, C.c_void_p]
    lib.ratatui_headless_render_chart.restype = C.c_bool
    lib.ratatui_headless_render_clear.argtypes = [C.c_uint16, C.c_uint16, C.c_void_p]
    lib.ratatui_headless_render_clear.restype = C.c_bool
    lib.ratatui_headless_render_frame.argtypes = [C.c_uint16, C.c_uint16, C.c_void_p, C.c_size_t, C.c_void_p]
    lib.ratatui_headless_render_frame.restype = C.c_bool
    lib.ratatui_headless_render_frame_cells.argtypes = [C.c_uint16, C.c_uint16, C.c_void_p, C.c_size_t, C.c_void_p, C.c_size_t]
    lib.ratatui_headless_render_frame_cells.restype = C.c_size_t
    lib.ratatui_headless_render_frame_styles.argtypes = [C.c_uint16, C.c_uint16, C.c_void_p, C.c_size_t, C.c_void_p]
    lib.ratatui_headless_render_frame_styles.restype = C.c_bool
    lib.ratatui_headless_render_frame_styles_ex.argtypes = [C.c_uint16, C.c_uint16, C.c_void_p, C.c_size_t, C.c_void_p]
    lib.ratatui_headless_render_frame_styles_ex.restype = C.c_bool
    lib.ratatui_headless_render_gauge.argtypes = [C.c_uint16, C.c_uint16, C.c_void_p, C.c_void_p]
    lib.ratatui_headless_render_gauge.restype = C.c_bool
    lib.ratatui_headless_render_linegauge.argtypes = [C.c_uint16, C.c_uint16, C.c_void_p, C.c_void_p]
    lib.ratatui_headless_render_linegauge.restype = C.c_bool
    lib.ratatui_headless_render_list.argtypes = [C.c_uint16, C.c_uint16, C.c_void_p, C.c_void_p]
    lib.ratatui_headless_render_list.restype = C.c_bool
    lib.ratatui_headless_render_list_state.argtypes = [C.c_uint16, C.c_uint16, C.c_void_p, C.c_void_p, C.c_void_p]
    lib.ratatui_headless_render_list_state.restype = C.c_bool
    lib.ratatui_headless_render_paragraph.argtypes = [C.c_uint16, C.c_uint16, C.c_void_p, C.c_void_p]
    lib.ratatui_headless_render_paragraph.restype = C.c_bool
    lib.ratatui_headless_render_ratatuilogo.argtypes = [C.c_uint16, C.c_uint16, C.c_void_p]
    lib.ratatui_headless_render_ratatuilogo.restype = C.c_bool
    lib.ratatui_headless_render_ratatuilogo_sized.argtypes = [C.c_uint16, C.c_uint16, C.c_uint32, C.c_void_p]
    lib.ratatui_headless_render_ratatuilogo_sized.restype = C.c_bool
    lib.ratatui_headless_render_ratatuimascot.argtypes = [C.c_uint16, C.c_uint16, C.c_uint32, C.c_void_p]
    lib.ratatui_headless_render_ratatuimascot.restype = C.c_bool
    lib.ratatui_headless_render_scrollbar.argtypes = [C.c_uint16, C.c_uint16, C.c_void_p, C.c_void_p]
    lib.ratatui_headless_render_scrollbar.restype = C.c_bool
    lib.ratatui_headless_render_sparkline.argtypes = [C.c_uint16, C.c_uint16, C.c_void_p, C.c_void_p]
    lib.ratatui_headless_render_sparkline.restype = C.c_bool
    lib.ratatui_headless_render_table.argtypes = [C.c_uint16, C.c_uint16, C.c_void_p, C.c_void_p]
    lib.ratatui_headless_render_table.restype = C.c_bool
    lib.ratatui_headless_render_tabs.argtypes = [C.c_uint16, C.c_uint16, C.c_void_p, C.c_void_p]
    lib.ratatui_headless_render_tabs.restype = C.c_bool
    lib.ratatui_init_terminal.argtypes = []
    lib.ratatui_init_terminal.restype = C.c_void_p
    lib.ratatui_inject_key.argtypes = [C.c_uint32, C.c_uint32, C.c_uint8]
    lib.ratatui_inject_mouse.argtypes = [C.c_uint32, C.c_uint32, C.c_uint16, C.c_uint16, C.c_uint8]
    lib.ratatui_inject_resize.argtypes = [C.c_uint16, C.c_uint16]
    lib.ratatui_layout_split.argtypes = [C.c_uint16, C.c_uint16, C.c_uint32, C.c_void_p, C.c_void_p, C.c_size_t, C.c_uint16, C.c_uint16, C.c_uint16, C.c_uint16, C.c_void_p, C.c_size_t]
    lib.ratatui_layout_split.restype = C.c_size_t
    lib.ratatui_layout_split_ex.argtypes = [C.c_uint16, C.c_uint16, C.c_uint32, C.c_void_p, C.c_void_p, C.c_size_t, C.c_uint16, C.c_uint16, C.c_uint16, C.c_uint16, C.c_uint16, C.c_void_p, C.c_size_t]
    lib.ratatui_layout_split_ex.restype = C.c_size_t
    lib.ratatui_layout_split_ex2.argtypes = [C.c_uint16, C.c_uint16, C.c_uint32, C.c_void_p, C.c_void_p, C.c_void_p, C.c_size_t, C.c_uint16, C.c_uint16, C.c_uint16, C.c_uint16, C.c_uint16, C.c_void_p, C.c_size_t]
    lib.ratatui_layout_split_ex2.restype = C.c_size_t
    lib.ratatui_line_get_bottom_left.argtypes = []
    lib.ratatui_line_get_bottom_left.restype = FfiStr
    lib.ratatui_line_get_bottom_right.argtypes = []
    lib.ratatui_line_get_bottom_right.restype = FfiStr
    lib.ratatui_line_get_cross.argtypes = []
    lib.ratatui_line_get_cross.restype = FfiStr
    lib.ratatui_line_get_double.argtypes = []
    lib.ratatui_line_get_double.restype = FfiSymbolsLineSet
    lib.ratatui_line_get_double_bottom_left.argtypes = []
    lib.ratatui_line_get_double_bottom_left.restype = FfiStr
    lib.ratatui_line_get_double_bottom_right.argtypes = []
    lib.ratatui_line_get_double_bottom_right.restype = FfiStr
    lib.ratatui_line_get_double_cross.argtypes = []
    lib.ratatui_line_get_double_cross.restype = FfiStr
    lib.ratatui_line_get_double_horizontal.argtypes = []
    lib.ratatui_line_get_double_horizontal.restype = FfiStr
    lib.ratatui_line_get_double_horizontal_down.argtypes = []
    lib.ratatui_line_get_double_horizontal_down.restype = FfiStr
    lib.ratatui_line_get_double_horizontal_up.argtypes = []
    lib.ratatui_line_get_double_horizontal_up.restype = FfiStr
    lib.ratatui_line_get_double_top_left.argtypes = []
    lib.ratatui_line_get_double_top_left.restype = FfiStr
    lib.ratatui_line_get_double_top_right.argtypes = []
    lib.ratatui_line_get_double_top_right.restype = FfiStr
    lib.ratatui_line_get_double_vertical.argtypes = []
    lib.ratatui_line_get_double_vertical.restype = FfiStr
    lib.ratatui_line_get_double_vertical_left.argtypes = []
    lib.ratatui_line_get_double_vertical_left.restype = FfiStr
    lib.ratatui_line_get_double_vertical_right.argtypes = []
    lib.ratatui_line_get_double_vertical_right.restype = FfiStr
    lib.ratatui_line_get_horizontal.argtypes = []
    lib.ratatui_line_get_horizontal.restype = FfiStr
    lib.ratatui_line_get_horizontal_down.argtypes = []
    lib.ratatui_line_get_horizontal_down.restype = FfiStr
    lib.ratatui_line_get_horizontal_up.argtypes = []
    lib.ratatui_line_get_horizontal_up.restype = FfiStr
    lib.ratatui_line_get_normal.argtypes = []
    lib.ratatui_line_get_normal.restype = FfiSymbolsLineSet
    lib.ratatui_line_get_rounded.argtypes = []
    lib.ratatui_line_get_rounded.restype = FfiSymbolsLineSet
    lib.ratatui_line_get_rounded_bottom_left.argtypes = []
    lib.ratatui_line_get_rounded_bottom_left.restype = FfiStr
    lib.ratatui_line_get_rounded_bottom_right.argtypes = []
    lib.ratatui_line_get_rounded_bottom_right.restype = FfiStr
    lib.ratatui_line_get_rounded_top_left.argtypes = []
    lib.ratatui_line_get_rounded_top_left.restype = FfiStr
    lib.ratatui_line_get_rounded_top_right.argtypes = []
    lib.ratatui_line_get_rounded_top_right.restype = FfiStr
    lib.ratatui_line_get_thick.argtypes = []
    lib.ratatui_line_get_thick.restype = FfiSymbolsLineSet
    lib.ratatui_line_get_thick_bottom_left.argtypes = []
    lib.ratatui_line_get_thick_bottom_left.restype = FfiStr
    lib.ratatui_line_get_thick_bottom_right.argtypes = []
    lib.ratatui_line_get_thick_bottom_right.restype = FfiStr
    lib.ratatui_line_get_thick_cross.argtypes = []
    lib.ratatui_line_get_thick_cross.restype = FfiStr
    lib.ratatui_line_get_thick_horizontal.argtypes = []
    lib.ratatui_line_get_thick_horizontal.restype = FfiStr
    lib.ratatui_line_get_thick_horizontal_down.argtypes = []
    lib.ratatui_line_get_thick_horizontal_down.restype = FfiStr
    lib.ratatui_line_get_thick_horizontal_up.argtypes = []
    lib.ratatui_line_get_thick_horizontal_up.restype = FfiStr
    lib.ratatui_line_get_thick_top_left.argtypes = []
    lib.ratatui_line_get_thick_top_left.restype = FfiStr
    lib.ratatui_line_get_thick_top_right.argtypes = []
    lib.ratatui_line_get_thick_top_right.restype = FfiStr
    lib.ratatui_line_get_thick_vertical.argtypes = []
    lib.ratatui_line_get_thick_vertical.restype = FfiStr
    lib.ratatui_line_get_thick_vertical_left.argtypes = []
    lib.ratatui_line_get_thick_vertical_left.restype = FfiStr
    lib.ratatui_line_get_thick_vertical_right.argtypes = []
    lib.ratatui_line_get_thick_vertical_right.restype = FfiStr
    lib.ratatui_line_get_top_left.argtypes = []
    lib.ratatui_line_get_top_left.restype = FfiStr
    lib.ratatui_line_get_top_right.argtypes = []
    lib.ratatui_line_get_top_right.restype = FfiStr
    lib.ratatui_line_get_vertical.argtypes = []
    lib.ratatui_line_get_vertical.restype = FfiStr
    lib.ratatui_line_get_vertical_left.argtypes = []
    lib.ratatui_line_get_vertical_left.restype = FfiStr
    lib.ratatui_line_get_vertical_right.argtypes = []
    lib.ratatui_line_get_vertical_right.restype = FfiStr
    lib.ratatui_linegauge_free.argtypes = [C.c_void_p]
    lib.ratatui_linegauge_new.argtypes = []
    lib.ratatui_linegauge_new.restype = C.c_void_p
    lib.ratatui_linegauge_set_block_adv.argtypes = [C.c_void_p, C.c_uint8, C.c_uint32, C.c_uint16, C.c_uint16, C.c_uint16, C.c_uint16, C.c_void_p, C.c_size_t]
    lib.ratatui_linegauge_set_block_title.argtypes = [C.c_void_p, C.c_char_p, C.c_bool]
    lib.ratatui_linegauge_set_block_title_alignment.argtypes = [C.c_void_p, C.c_uint32]
    lib.ratatui_linegauge_set_block_title_spans.argtypes = [C.c_void_p, C.c_void_p, C.c_size_t, C.c_bool]
    lib.ratatui_linegauge_set_label.argtypes = [C.c_void_p, C.c_char_p]
    lib.ratatui_linegauge_set_label_spans.argtypes = [C.c_void_p, C.c_void_p, C.c_size_t]
    lib.ratatui_linegauge_set_ratio.argtypes = [C.c_void_p, C.c_float]
    lib.ratatui_linegauge_set_style.argtypes = [C.c_void_p, FfiStyle]
    lib.ratatui_list_append_item.argtypes = [C.c_void_p, C.c_char_p, FfiStyle]
    lib.ratatui_list_append_item_spans.argtypes = [C.c_void_p, C.c_void_p, C.c_size_t]
    lib.ratatui_list_append_items_spans.argtypes = [C.c_void_p, C.c_void_p, C.c_size_t]
    lib.ratatui_list_free.argtypes = [C.c_void_p]
    lib.ratatui_list_new.argtypes = []
    lib.ratatui_list_new.restype = C.c_void_p
    lib.ratatui_list_reserve_items.argtypes = [C.c_void_p, C.c_size_t]
    lib.ratatui_list_set_block_adv.argtypes = [C.c_void_p, C.c_uint8, C.c_uint32, C.c_uint16, C.c_uint16, C.c_uint16, C.c_uint16, C.c_void_p, C.c_size_t]
    lib.ratatui_list_set_block_title.argtypes = [C.c_void_p, C.c_char_p, C.c_bool]
    lib.ratatui_list_set_block_title_alignment.argtypes = [C.c_void_p, C.c_uint32]
    lib.ratatui_list_set_block_title_spans.argtypes = [C.c_void_p, C.c_void_p, C.c_size_t, C.c_bool]
    lib.ratatui_list_set_direction.argtypes = [C.c_void_p, C.c_uint32]
    lib.ratatui_list_set_highlight_spacing.argtypes = [C.c_void_p, C.c_uint32]
    lib.ratatui_list_set_highlight_style.argtypes = [C.c_void_p, FfiStyle]
    lib.ratatui_list_set_highlight_symbol.argtypes = [C.c_void_p, C.c_char_p]
    lib.ratatui_list_set_scroll_offset.argtypes = [C.c_void_p, C.c_size_t]
    lib.ratatui_list_set_selected.argtypes = [C.c_void_p, C.c_int32]
    lib.ratatui_list_state_free.argtypes = [C.c_void_p]
    lib.ratatui_list_state_new.argtypes = []
    lib.ratatui_list_state_new.restype = C.c_void_p
    lib.ratatui_list_state_set_offset.argtypes = [C.c_void_p, C.c_size_t]
    lib.ratatui_list_state_set_selected.argtypes = [C.c_void_p, C.c_int32]
    lib.ratatui_next_event.argtypes = [C.c_uint64, C.c_void_p]
    lib.ratatui_next_event.restype = C.c_bool
    lib.ratatui_palette_material_get_amber.argtypes = []
    lib.ratatui_palette_material_get_amber.restype = FfiAccentedPaletteU32
    lib.ratatui_palette_material_get_black.argtypes = []
    lib.ratatui_palette_material_get_black.restype = C.c_uint32
    lib.ratatui_palette_material_get_blue.argtypes = []
    lib.ratatui_palette_material_get_blue.restype = FfiAccentedPaletteU32
    lib.ratatui_palette_material_get_blue_gray.argtypes = []
    lib.ratatui_palette_material_get_blue_gray.restype = FfiNonAccentedPaletteU32
    lib.ratatui_palette_material_get_brown.argtypes = []
    lib.ratatui_palette_material_get_brown.restype = FfiNonAccentedPaletteU32
    lib.ratatui_palette_material_get_cyan.argtypes = []
    lib.ratatui_palette_material_get_cyan.restype = FfiAccentedPaletteU32
    lib.ratatui_palette_material_get_deep_orange.argtypes = []
    lib.ratatui_palette_material_get_deep_orange.restype = FfiAccentedPaletteU32
    lib.ratatui_palette_material_get_deep_purple.argtypes = []
    lib.ratatui_palette_material_get_deep_purple.restype = FfiAccentedPaletteU32
    lib.ratatui_palette_material_get_gray.argtypes = []
    lib.ratatui_palette_material_get_gray.restype = FfiNonAccentedPaletteU32
    lib.ratatui_palette_material_get_green.argtypes = []
    lib.ratatui_palette_material_get_green.restype = FfiAccentedPaletteU32
    lib.ratatui_palette_material_get_indigo.argtypes = []
    lib.ratatui_palette_material_get_indigo.restype = FfiAccentedPaletteU32
    lib.ratatui_palette_material_get_light_blue.argtypes = []
    lib.ratatui_palette_material_get_light_blue.restype = FfiAccentedPaletteU32
    lib.ratatui_palette_material_get_light_green.argtypes = []
    lib.ratatui_palette_material_get_light_green.restype = FfiAccentedPaletteU32
    lib.ratatui_palette_material_get_lime.argtypes = []
    lib.ratatui_palette_material_get_lime.restype = FfiAccentedPaletteU32
    lib.ratatui_palette_material_get_orange.argtypes = []
    lib.ratatui_palette_material_get_orange.restype = FfiAccentedPaletteU32
    lib.ratatui_palette_material_get_pink.argtypes = []
    lib.ratatui_palette_material_get_pink.restype = FfiAccentedPaletteU32
    lib.ratatui_palette_material_get_purple.argtypes = []
    lib.ratatui_palette_material_get_purple.restype = FfiAccentedPaletteU32
    lib.ratatui_palette_material_get_red.argtypes = []
    lib.ratatui_palette_material_get_red.restype = FfiAccentedPaletteU32
    lib.ratatui_palette_material_get_teal.argtypes = []
    lib.ratatui_palette_material_get_teal.restype = FfiAccentedPaletteU32
    lib.ratatui_palette_material_get_white.argtypes = []
    lib.ratatui_palette_material_get_white.restype = C.c_uint32
    lib.ratatui_palette_material_get_yellow.argtypes = []
    lib.ratatui_palette_material_get_yellow.restype = FfiAccentedPaletteU32
    lib.ratatui_palette_tailwind_get_amber.argtypes = []
    lib.ratatui_palette_tailwind_get_amber.restype = FfiTailwindPaletteU32
    lib.ratatui_palette_tailwind_get_black.argtypes = []
    lib.ratatui_palette_tailwind_get_black.restype = C.c_uint32
    lib.ratatui_palette_tailwind_get_blue.argtypes = []
    lib.ratatui_palette_tailwind_get_blue.restype = FfiTailwindPaletteU32
    lib.ratatui_palette_tailwind_get_cyan.argtypes = []
    lib.ratatui_palette_tailwind_get_cyan.restype = FfiTailwindPaletteU32
    lib.ratatui_palette_tailwind_get_emerald.argtypes = []
    lib.ratatui_palette_tailwind_get_emerald.restype = FfiTailwindPaletteU32
    lib.ratatui_palette_tailwind_get_fuchsia.argtypes = []
    lib.ratatui_palette_tailwind_get_fuchsia.restype = FfiTailwindPaletteU32
    lib.ratatui_palette_tailwind_get_gray.argtypes = []
    lib.ratatui_palette_tailwind_get_gray.restype = FfiTailwindPaletteU32
    lib.ratatui_palette_tailwind_get_green.argtypes = []
    lib.ratatui_palette_tailwind_get_green.restype = FfiTailwindPaletteU32
    lib.ratatui_palette_tailwind_get_indigo.argtypes = []
    lib.ratatui_palette_tailwind_get_indigo.restype = FfiTailwindPaletteU32
    lib.ratatui_palette_tailwind_get_lime.argtypes = []
    lib.ratatui_palette_tailwind_get_lime.restype = FfiTailwindPaletteU32
    lib.ratatui_palette_tailwind_get_neutral.argtypes = []
    lib.ratatui_palette_tailwind_get_neutral.restype = FfiTailwindPaletteU32
    lib.ratatui_palette_tailwind_get_orange.argtypes = []
    lib.ratatui_palette_tailwind_get_orange.restype = FfiTailwindPaletteU32
    lib.ratatui_palette_tailwind_get_pink.argtypes = []
    lib.ratatui_palette_tailwind_get_pink.restype = FfiTailwindPaletteU32
    lib.ratatui_palette_tailwind_get_purple.argtypes = []
    lib.ratatui_palette_tailwind_get_purple.restype = FfiTailwindPaletteU32
    lib.ratatui_palette_tailwind_get_red.argtypes = []
    lib.ratatui_palette_tailwind_get_red.restype = FfiTailwindPaletteU32
    lib.ratatui_palette_tailwind_get_rose.argtypes = []
    lib.ratatui_palette_tailwind_get_rose.restype = FfiTailwindPaletteU32
    lib.ratatui_palette_tailwind_get_sky.argtypes = []
    lib.ratatui_palette_tailwind_get_sky.restype = FfiTailwindPaletteU32
    lib.ratatui_palette_tailwind_get_slate.argtypes = []
    lib.ratatui_palette_tailwind_get_slate.restype = FfiTailwindPaletteU32
    lib.ratatui_palette_tailwind_get_stone.argtypes = []
    lib.ratatui_palette_tailwind_get_stone.restype = FfiTailwindPaletteU32
    lib.ratatui_palette_tailwind_get_teal.argtypes = []
    lib.ratatui_palette_tailwind_get_teal.restype = FfiTailwindPaletteU32
    lib.ratatui_palette_tailwind_get_violet.argtypes = []
    lib.ratatui_palette_tailwind_get_violet.restype = FfiTailwindPaletteU32
    lib.ratatui_palette_tailwind_get_white.argtypes = []
    lib.ratatui_palette_tailwind_get_white.restype = C.c_uint32
    lib.ratatui_palette_tailwind_get_yellow.argtypes = []
    lib.ratatui_palette_tailwind_get_yellow.restype = FfiTailwindPaletteU32
    lib.ratatui_palette_tailwind_get_zinc.argtypes = []
    lib.ratatui_palette_tailwind_get_zinc.restype = FfiTailwindPaletteU32
    lib.ratatui_paragraph_append_line.argtypes = [C.c_void_p, C.c_char_p, FfiStyle]
    lib.ratatui_paragraph_append_line_spans.argtypes = [C.c_void_p, C.c_void_p, C.c_size_t]
    lib.ratatui_paragraph_append_lines_spans.argtypes = [C.c_void_p, C.c_void_p, C.c_size_t]
    lib.ratatui_paragraph_append_span.argtypes = [C.c_void_p, C.c_char_p, FfiStyle]
    lib.ratatui_paragraph_append_spans.argtypes = [C.c_void_p, C.c_void_p, C.c_size_t]
    lib.ratatui_paragraph_free.argtypes = [C.c_void_p]
    lib.ratatui_paragraph_line_break.argtypes = [C.c_void_p]
    lib.ratatui_paragraph_new.argtypes = [C.c_char_p]
    lib.ratatui_paragraph_new.restype = C.c_void_p
    lib.ratatui_paragraph_new_empty.argtypes = []
    lib.ratatui_paragraph_new_empty.restype = C.c_void_p
    lib.ratatui_paragraph_reserve_lines.argtypes = [C.c_void_p, C.c_size_t]
    lib.ratatui_paragraph_set_alignment.argtypes = [C.c_void_p, C.c_uint32]
    lib.ratatui_paragraph_set_block_adv.argtypes = [C.c_void_p, C.c_uint8, C.c_uint32, C.c_uint16, C.c_uint16, C.c_uint16, C.c_uint16, C.c_void_p, C.c_size_t]
    lib.ratatui_paragraph_set_block_title.argtypes = [C.c_void_p, C.c_char_p, C.c_bool]
    lib.ratatui_paragraph_set_block_title_alignment.argtypes = [C.c_void_p, C.c_uint32]
    lib.ratatui_paragraph_set_block_title_spans.argtypes = [C.c_void_p, C.c_void_p, C.c_size_t, C.c_bool]
    lib.ratatui_paragraph_set_scroll.argtypes = [C.c_void_p, C.c_uint16, C.c_uint16]
    lib.ratatui_paragraph_set_style.argtypes = [C.c_void_p, FfiStyle]
    lib.ratatui_paragraph_set_wrap.argtypes = [C.c_void_p, C.c_bool]
    lib.ratatui_ratatuilogo_draw_in.argtypes = [C.c_void_p, FfiRect]
    lib.ratatui_ratatuilogo_draw_in.restype = C.c_bool
    lib.ratatui_ratatuilogo_draw_sized_in.argtypes = [C.c_void_p, FfiRect, C.c_uint32]
    lib.ratatui_ratatuilogo_draw_sized_in.restype = C.c_bool
    lib.ratatui_ratatuimascot_draw_in.argtypes = [C.c_void_p, FfiRect, C.c_uint32]
    lib.ratatui_ratatuimascot_draw_in.restype = C.c_bool
    lib.ratatui_scrollbar_configure.argtypes = [C.c_void_p, C.c_uint32, C.c_uint16, C.c_uint16, C.c_uint16]
    lib.ratatui_scrollbar_free.argtypes = [C.c_void_p]
    lib.ratatui_scrollbar_get_double_horizontal.argtypes = []
    lib.ratatui_scrollbar_get_double_horizontal.restype = FfiSymbolsScrollbarSet
    lib.ratatui_scrollbar_get_double_vertical.argtypes = []
    lib.ratatui_scrollbar_get_double_vertical.restype = FfiSymbolsScrollbarSet
    lib.ratatui_scrollbar_get_horizontal.argtypes = []
    lib.ratatui_scrollbar_get_horizontal.restype = FfiSymbolsScrollbarSet
    lib.ratatui_scrollbar_get_vertical.argtypes = []
    lib.ratatui_scrollbar_get_vertical.restype = FfiSymbolsScrollbarSet
    lib.ratatui_scrollbar_new.argtypes = []
    lib.ratatui_scrollbar_new.restype = C.c_void_p
    lib.ratatui_scrollbar_set_block_adv.argtypes = [C.c_void_p, C.c_uint8, C.c_uint32, C.c_uint16, C.c_uint16, C.c_uint16, C.c_uint16, C.c_void_p, C.c_size_t]
    lib.ratatui_scrollbar_set_block_title.argtypes = [C.c_void_p, C.c_char_p, C.c_bool]
    lib.ratatui_scrollbar_set_block_title_alignment.argtypes = [C.c_void_p, C.c_uint32]
    lib.ratatui_scrollbar_set_block_title_spans.argtypes = [C.c_void_p, C.c_void_p, C.c_size_t, C.c_bool]
    lib.ratatui_scrollbar_set_orientation_side.argtypes = [C.c_void_p, C.c_uint32]
    lib.ratatui_sparkline_free.argtypes = [C.c_void_p]
    lib.ratatui_sparkline_new.argtypes = []
    lib.ratatui_sparkline_new.restype = C.c_void_p
    lib.ratatui_sparkline_set_block_adv.argtypes = [C.c_void_p, C.c_uint8, C.c_uint32, C.c_uint16, C.c_uint16, C.c_uint16, C.c_uint16, C.c_void_p, C.c_size_t]
    lib.ratatui_sparkline_set_block_title.argtypes = [C.c_void_p, C.c_char_p, C.c_bool]
    lib.ratatui_sparkline_set_block_title_spans.argtypes = [C.c_void_p, C.c_void_p, C.c_size_t, C.c_bool]
    lib.ratatui_sparkline_set_max.argtypes = [C.c_void_p, C.c_uint64]
    lib.ratatui_sparkline_set_style.argtypes = [C.c_void_p, FfiStyle]
    lib.ratatui_sparkline_set_values.argtypes = [C.c_void_p, C.c_void_p, C.c_size_t]
    lib.ratatui_string_free.argtypes = [C.c_char_p]
    lib.ratatui_symbols_get_braille_dots_flat.argtypes = []
    lib.ratatui_symbols_get_braille_dots_flat.restype = FfiU16Slice
    lib.ratatui_table_append_row.argtypes = [C.c_void_p, C.c_char_p]
    lib.ratatui_table_append_row_cells_lines.argtypes = [C.c_void_p, C.c_void_p, C.c_size_t]
    lib.ratatui_table_append_row_spans.argtypes = [C.c_void_p, C.c_void_p, C.c_size_t]
    lib.ratatui_table_append_rows_cells_lines.argtypes = [C.c_void_p, C.c_void_p, C.c_size_t]
    lib.ratatui_table_free.argtypes = [C.c_void_p]
    lib.ratatui_table_new.argtypes = []
    lib.ratatui_table_new.restype = C.c_void_p
    lib.ratatui_table_reserve_rows.argtypes = [C.c_void_p, C.c_size_t]
    lib.ratatui_table_set_block_adv.argtypes = [C.c_void_p, C.c_uint8, C.c_uint32, C.c_uint16, C.c_uint16, C.c_uint16, C.c_uint16, C.c_void_p, C.c_size_t]
    lib.ratatui_table_set_block_title.argtypes = [C.c_void_p, C.c_char_p, C.c_bool]
    lib.ratatui_table_set_block_title_alignment.argtypes = [C.c_void_p, C.c_uint32]
    lib.ratatui_table_set_block_title_spans.argtypes = [C.c_void_p, C.c_void_p, C.c_size_t, C.c_bool]
    lib.ratatui_table_set_cell_highlight_style.argtypes = [C.c_void_p, FfiStyle]
    lib.ratatui_table_set_column_highlight_style.argtypes = [C.c_void_p, FfiStyle]
    lib.ratatui_table_set_column_spacing.argtypes = [C.c_void_p, C.c_uint16]
    lib.ratatui_table_set_header_style.argtypes = [C.c_void_p, FfiStyle]
    lib.ratatui_table_set_headers.argtypes = [C.c_void_p, C.c_char_p]
    lib.ratatui_table_set_headers_spans.argtypes = [C.c_void_p, C.c_void_p, C.c_size_t]
    lib.ratatui_table_set_highlight_spacing.argtypes = [C.c_void_p, C.c_uint32]
    lib.ratatui_table_set_highlight_symbol.argtypes = [C.c_void_p, C.c_char_p]
    lib.ratatui_table_set_row_height.argtypes = [C.c_void_p, C.c_uint16]
    lib.ratatui_table_set_row_highlight_style.argtypes = [C.c_void_p, FfiStyle]
    lib.ratatui_table_set_selected.argtypes = [C.c_void_p, C.c_int32]
    lib.ratatui_table_set_widths.argtypes = [C.c_void_p, C.c_void_p, C.c_void_p, C.c_size_t]
    lib.ratatui_table_set_widths_percentages.argtypes = [C.c_void_p, C.c_void_p, C.c_size_t]
    lib.ratatui_table_state_free.argtypes = [C.c_void_p]
    lib.ratatui_table_state_new.argtypes = []
    lib.ratatui_table_state_new.restype = C.c_void_p
    lib.ratatui_table_state_set_offset.argtypes = [C.c_void_p, C.c_size_t]
    lib.ratatui_table_state_set_selected.argtypes = [C.c_void_p, C.c_int32]
    lib.ratatui_tabs_add_title_spans.argtypes = [C.c_void_p, C.c_void_p, C.c_size_t]
    lib.ratatui_tabs_clear_titles.argtypes = [C.c_void_p]
    lib.ratatui_tabs_free.argtypes = [C.c_void_p]
    lib.ratatui_tabs_new.argtypes = []
    lib.ratatui_tabs_new.restype = C.c_void_p
    lib.ratatui_tabs_set_block_adv.argtypes = [C.c_void_p, C.c_uint8, C.c_uint32, C.c_uint16, C.c_uint16, C.c_uint16, C.c_uint16, C.c_void_p, C.c_size_t]
    lib.ratatui_tabs_set_block_title.argtypes = [C.c_void_p, C.c_char_p, C.c_bool]
    lib.ratatui_tabs_set_block_title_alignment.argtypes = [C.c_void_p, C.c_uint32]
    lib.ratatui_tabs_set_block_title_spans.argtypes = [C.c_void_p, C.c_void_p, C.c_size_t, C.c_bool]
    lib.ratatui_tabs_set_divider.argtypes = [C.c_void_p, C.c_char_p]
    lib.ratatui_tabs_set_divider_spans.argtypes = [C.c_void_p, C.c_void_p, C.c_size_t]
    lib.ratatui_tabs_set_selected.argtypes = [C.c_void_p, C.c_uint16]
    lib.ratatui_tabs_set_styles.argtypes = [C.c_void_p, FfiStyle, FfiStyle]
    lib.ratatui_tabs_set_titles.argtypes = [C.c_void_p, C.c_char_p]
    lib.ratatui_tabs_set_titles_spans.argtypes = [C.c_void_p, C.c_void_p, C.c_size_t]
    lib.ratatui_terminal_clear.argtypes = [C.c_void_p]
    lib.ratatui_terminal_disable_raw.argtypes = [C.c_void_p]
    lib.ratatui_terminal_disable_raw.restype = C.c_bool
    lib.ratatui_terminal_draw_barchart_in.argtypes = [C.c_void_p, C.c_void_p, FfiRect]
    lib.ratatui_terminal_draw_barchart_in.restype = C.c_bool
    lib.ratatui_terminal_draw_canvas_in.argtypes = [C.c_void_p, C.c_void_p, FfiRect]
    lib.ratatui_terminal_draw_canvas_in.restype = C.c_bool
    lib.ratatui_terminal_draw_cells_in.argtypes = [C.c_void_p, C.c_void_p, C.c_uint16, C.c_uint16, FfiRect]
    lib.ratatui_terminal_draw_cells_in.restype = C.c_bool
    lib.ratatui_terminal_draw_chart_in.argtypes = [C.c_void_p, C.c_void_p, FfiRect]
    lib.ratatui_terminal_draw_chart_in.restype = C.c_bool
    lib.ratatui_terminal_draw_frame.argtypes = [C.c_void_p, C.c_void_p, C.c_size_t]
    lib.ratatui_terminal_draw_frame.restype = C.c_bool
    lib.ratatui_terminal_draw_gauge_in.argtypes = [C.c_void_p, C.c_void_p, FfiRect]
    lib.ratatui_terminal_draw_gauge_in.restype = C.c_bool
    lib.ratatui_terminal_draw_linegauge_in.argtypes = [C.c_void_p, C.c_void_p, FfiRect]
    lib.ratatui_terminal_draw_linegauge_in.restype = C.c_bool
    lib.ratatui_terminal_draw_list_in.argtypes = [C.c_void_p, C.c_void_p, FfiRect]
    lib.ratatui_terminal_draw_list_in.restype = C.c_bool
    lib.ratatui_terminal_draw_list_state_in.argtypes = [C.c_void_p, C.c_void_p, FfiRect, C.c_void_p]
    lib.ratatui_terminal_draw_list_state_in.restype = C.c_bool
    lib.ratatui_terminal_draw_paragraph.argtypes = [C.c_void_p, C.c_void_p]
    lib.ratatui_terminal_draw_paragraph.restype = C.c_bool
    lib.ratatui_terminal_draw_paragraph_in.argtypes = [C.c_void_p, C.c_void_p, FfiRect]
    lib.ratatui_terminal_draw_paragraph_in.restype = C.c_bool
    lib.ratatui_terminal_draw_scrollbar_in.argtypes = [C.c_void_p, C.c_void_p, FfiRect]
    lib.ratatui_terminal_draw_scrollbar_in.restype = C.c_bool
    lib.ratatui_terminal_draw_sparkline_in.argtypes = [C.c_void_p, C.c_void_p, FfiRect]
    lib.ratatui_terminal_draw_sparkline_in.restype = C.c_bool
    lib.ratatui_terminal_draw_table_in.argtypes = [C.c_void_p, C.c_void_p, FfiRect]
    lib.ratatui_terminal_draw_table_in.restype = C.c_bool
    lib.ratatui_terminal_draw_table_state_in.argtypes = [C.c_void_p, C.c_void_p, FfiRect, C.c_void_p]
    lib.ratatui_terminal_draw_table_state_in.restype = C.c_bool
    lib.ratatui_terminal_draw_tabs_in.argtypes = [C.c_void_p, C.c_void_p, FfiRect]
    lib.ratatui_terminal_draw_tabs_in.restype = C.c_bool
    lib.ratatui_terminal_enable_raw.argtypes = [C.c_void_p]
    lib.ratatui_terminal_enable_raw.restype = C.c_bool
    lib.ratatui_terminal_enter_alt.argtypes = [C.c_void_p]
    lib.ratatui_terminal_enter_alt.restype = C.c_bool
    lib.ratatui_terminal_free.argtypes = [C.c_void_p]
    lib.ratatui_terminal_get_cursor_position.argtypes = [C.c_void_p, C.c_void_p, C.c_void_p]
    lib.ratatui_terminal_get_cursor_position.restype = C.c_bool
    lib.ratatui_terminal_get_viewport_area.argtypes = [C.c_void_p, C.c_void_p]
    lib.ratatui_terminal_get_viewport_area.restype = C.c_bool
    lib.ratatui_terminal_leave_alt.argtypes = [C.c_void_p]
    lib.ratatui_terminal_leave_alt.restype = C.c_bool
    lib.ratatui_terminal_set_cursor_position.argtypes = [C.c_void_p, C.c_uint16, C.c_uint16]
    lib.ratatui_terminal_set_cursor_position.restype = C.c_bool
    lib.ratatui_terminal_set_viewport_area.argtypes = [C.c_void_p, FfiRect]
    lib.ratatui_terminal_set_viewport_area.restype = C.c_bool
    lib.ratatui_terminal_show_cursor.argtypes = [C.c_void_p, C.c_bool]
    lib.ratatui_terminal_show_cursor.restype = C.c_bool
    lib.ratatui_terminal_size.argtypes = [C.c_void_p, C.c_void_p]
    lib.ratatui_terminal_size.restype = C.c_bool

    # Expose value-struct types on the lib object for the ergonomic layer.
    lib.FfiAccentedPaletteU32 = FfiAccentedPaletteU32
    lib.FfiCanvasLine = FfiCanvasLine
    lib.FfiCanvasPoints = FfiCanvasPoints
    lib.FfiCanvasRect = FfiCanvasRect
    lib.FfiCellInfo = FfiCellInfo
    lib.FfiCellLines = FfiCellLines
    lib.FfiChartDatasetSpec = FfiChartDatasetSpec
    lib.FfiDrawCmd = FfiDrawCmd
    lib.FfiEvent = FfiEvent
    lib.FfiKeyEvent = FfiKeyEvent
    lib.FfiLineSpans = FfiLineSpans
    lib.FfiMarginDto = FfiMarginDto
    lib.FfiNonAccentedPaletteU32 = FfiNonAccentedPaletteU32
    lib.FfiOffsetDto = FfiOffsetDto
    lib.FfiPositionDto = FfiPositionDto
    lib.FfiRect = FfiRect
    lib.FfiRowCellsLines = FfiRowCellsLines
    lib.FfiSizeDto = FfiSizeDto
    lib.FfiSpan = FfiSpan
    lib.FfiStr = FfiStr
    lib.FfiStyle = FfiStyle
    lib.FfiSymbolsBarSet = FfiSymbolsBarSet
    lib.FfiSymbolsBlockSet = FfiSymbolsBlockSet
    lib.FfiSymbolsBorderSet = FfiSymbolsBorderSet
    lib.FfiSymbolsLineSet = FfiSymbolsLineSet
    lib.FfiSymbolsScrollbarSet = FfiSymbolsScrollbarSet
    lib.FfiTabsStyles = FfiTabsStyles
    lib.FfiTailwindPaletteU32 = FfiTailwindPaletteU32
    lib.FfiU16Slice = FfiU16Slice
