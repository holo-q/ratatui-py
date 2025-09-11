from __future__ import annotations

from typing import Tuple, Optional, Sequence
import ctypes as C
from .types import Rect as _Rect, RectLike
from ._ffi import load_library, FFI_LAYOUT_DIR, FfiRect

Rect = Tuple[int, int, int, int]  # x, y, w, h (kept for backward-compat)


def margin(rect: Rect, *, all: Optional[int] = None, x: int = 0, y: int = 0) -> Rect:
    if all is not None:
        x = y = int(all)
    rx, ry, rw, rh = rect
    nx = rx + x
    ny = ry + y
    nw = max(0, rw - 2 * x)
    nh = max(0, rh - 2 * y)
    return (nx, ny, nw, nh)


def split_h(rect: Rect, *fractions: float, gap: int = 0) -> tuple[Rect, ...]:
    """Split horizontally (stacked vertically) by fractions.

    Example: split_h((0,0,80,24), 0.7, 0.3, gap=1)
    """
    x, y, w, h = rect
    total_gap = max(0, (len(fractions) - 1) * gap)
    avail = max(0, h - total_gap)
    fr_sum = sum(fractions) or 1.0
    rows = []
    yy = y
    for i, f in enumerate(fractions):
        hh = int(round(avail * (f / fr_sum))) if i < len(fractions) - 1 else (y + h - yy)
        rows.append((x, yy, w, max(0, hh)))
        yy += hh + (gap if i < len(fractions) - 1 else 0)
    return tuple(rows)


def split_v(rect: Rect, *fractions: float, gap: int = 0) -> tuple[Rect, ...]:
    """Split vertically (columns) by fractions.

    Example: split_v((0,0,80,24), 0.25, 0.5, 0.25, gap=1)
    """
    x, y, w, h = rect
    total_gap = max(0, (len(fractions) - 1) * gap)
    avail = max(0, w - total_gap)
    fr_sum = sum(fractions) or 1.0
    cols = []
    xx = x
    for i, f in enumerate(fractions):
        ww = int(round(avail * (f / fr_sum))) if i < len(fractions) - 1 else (x + w - xx)
        cols.append((xx, y, max(0, ww), h))
        xx += ww + (gap if i < len(fractions) - 1 else 0)
    return tuple(cols)


# Typed variants that return Rect dataclass for richer hints
def margin_rect(rect: RectLike, *, all: Optional[int] = None, x: int = 0, y: int = 0) -> _Rect:
    rx, ry, rw, rh = (rect.to_tuple() if hasattr(rect, 'to_tuple') else rect)  # type: ignore[attr-defined]
    if all is not None:
        x = y = int(all)
    nx = rx + x
    ny = ry + y
    nw = max(0, rw - 2 * x)
    nh = max(0, rh - 2 * y)
    return _Rect(nx, ny, nw, nh)


def split_h_rect(rect: RectLike, *fractions: float, gap: int = 0) -> tuple[_Rect, ...]:
    x, y, w, h = (rect.to_tuple() if hasattr(rect, 'to_tuple') else rect)  # type: ignore[attr-defined]
    total_gap = max(0, (len(fractions) - 1) * gap)
    avail = max(0, h - total_gap)
    fr_sum = sum(fractions) or 1.0
    rows = []
    yy = y
    for i, f in enumerate(fractions):
        hh = int(round(avail * (f / fr_sum))) if i < len(fractions) - 1 else (y + h - yy)
        rows.append(_Rect(x, yy, w, max(0, hh)))
        yy += hh + (gap if i < len(fractions) - 1 else 0)
    return tuple(rows)


def split_v_rect(rect: RectLike, *fractions: float, gap: int = 0) -> tuple[_Rect, ...]:
    x, y, w, h = (rect.to_tuple() if hasattr(rect, 'to_tuple') else rect)  # type: ignore[attr-defined]
    total_gap = max(0, (len(fractions) - 1) * gap)
    avail = max(0, w - total_gap)
    fr_sum = sum(fractions) or 1.0
    cols = []
    xx = x
    for i, f in enumerate(fractions):
        ww = int(round(avail * (f / fr_sum))) if i < len(fractions) - 1 else (x + w - xx)
        cols.append(_Rect(xx, y, max(0, ww), h))
        xx += ww + (gap if i < len(fractions) - 1 else 0)
    return tuple(cols)


# ---- FFI-driven splits (v0.2.0+) ----

def _build_constraints(constraints: Sequence[tuple[str, int] | tuple[str, int, int]]):
    kinds: list[int] = []
    a_vals: list[int] = []
    b_vals: list[int] = []
    has_ratio = False
    for c in constraints:
        if not isinstance(c, tuple) or len(c) < 2:
            raise ValueError("constraint must be ('len'|'pct'|'min'|'ratio', ...)")
        kind = c[0].lower()
        if kind in ("len", "length"):
            kinds.append(0); a_vals.append(int(c[1])); b_vals.append(0)
        elif kind in ("pct", "percent", "percentage"):
            kinds.append(1); a_vals.append(int(c[1])); b_vals.append(0)
        elif kind == "min":
            kinds.append(2); a_vals.append(int(c[1])); b_vals.append(0)
        elif kind == "ratio":
            if len(c) < 3:
                raise ValueError("ratio requires ('ratio', numer, denom)")
            kinds.append(3); a_vals.append(int(c[1])); b_vals.append(max(1, int(c[2]))); has_ratio = True
        else:
            raise ValueError(f"unknown constraint kind: {kind}")
    return kinds, a_vals, (b_vals if has_ratio else None)


def layout_split_ffi(
    rect: RectLike,
    *,
    direction: str = "vertical",
    constraints: Sequence[tuple[str, int] | tuple[str, int, int]] = (),
    spacing: int = 0,
    margins: Tuple[int, int, int, int] = (0, 0, 0, 0),
) -> tuple[Rect, ...]:
    """FFI-backed splitter with precise parity to Ratatui constraints.

    constraints: list of ('len', n) | ('pct', p) | ('min', n) | ('ratio', a, b)
    direction: 'vertical' stacks top-to-bottom; 'horizontal' splits into columns
    margins: (l, t, r, b)
    """
    lib = load_library()
    x, y, w, h = (rect.to_tuple() if hasattr(rect, 'to_tuple') else rect)  # type: ignore[attr-defined]
    kinds, a_vals, b_vals = _build_constraints(constraints)
    dir_val = 0 if direction.lower().startswith('v') else 1
    l, t, r, b = margins
    out = (FfiRect * max(1, len(kinds)))()
    if b_vals is not None and hasattr(lib, 'ratatui_layout_split_ex2'):
        arr_k = (C.c_uint * len(kinds))(*kinds)
        arr_a = (C.c_uint16 * len(a_vals))(*a_vals)
        arr_b = (C.c_uint16 * len(b_vals))(*b_vals)
        n = lib.ratatui_layout_split_ex2(C.c_uint16(w), C.c_uint16(h), C.c_uint(dir_val), arr_k, arr_a, arr_b, len(kinds), C.c_uint16(spacing), C.c_uint16(l), C.c_uint16(t), C.c_uint16(r), C.c_uint16(b), out, len(out))
    else:
        arr_k = (C.c_uint * len(kinds))(*kinds)
        arr_a = (C.c_uint16 * len(a_vals))(*a_vals)
        if hasattr(lib, 'ratatui_layout_split_ex'):
            n = lib.ratatui_layout_split_ex(C.c_uint16(w), C.c_uint16(h), C.c_uint(dir_val), arr_k, arr_a, len(kinds), C.c_uint16(spacing), C.c_uint16(l), C.c_uint16(t), C.c_uint16(r), C.c_uint16(b), out, len(out))
        else:
            # fallback to simple margin-only variant
            n = lib.ratatui_layout_split(C.c_uint16(w), C.c_uint16(h), C.c_uint(dir_val), arr_k, arr_a, len(kinds), C.c_uint16(l), C.c_uint16(t), C.c_uint16(r), C.c_uint16(b), out, len(out))
    rects: list[Rect] = []
    for i in range(int(n)):
        rr = out[i]
        rects.append((x + int(rr.x), y + int(rr.y), int(rr.width), int(rr.height)))
    return tuple(rects)


def split_h_ffi(rect: RectLike, constraints: Sequence[tuple[str, int] | tuple[str, int, int]], *, gap: int = 0, margins: Tuple[int, int, int, int] = (0, 0, 0, 0)) -> tuple[Rect, ...]:
    return layout_split_ffi(rect, direction="vertical", constraints=constraints, spacing=gap, margins=margins)


def split_v_ffi(rect: RectLike, constraints: Sequence[tuple[str, int] | tuple[str, int, int]], *, gap: int = 0, margins: Tuple[int, int, int, int] = (0, 0, 0, 0)) -> tuple[Rect, ...]:
    return layout_split_ffi(rect, direction="horizontal", constraints=constraints, spacing=gap, margins=margins)
