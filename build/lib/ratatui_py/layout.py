from __future__ import annotations

from typing import Tuple

Rect = Tuple[int, int, int, int]  # x, y, w, h


def margin(rect: Rect, *, all: int | None = None, x: int = 0, y: int = 0) -> Rect:
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

