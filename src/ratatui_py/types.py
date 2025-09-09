from __future__ import annotations
from dataclasses import dataclass
from typing import Iterator, Tuple, TypeAlias, Union, Sequence, Any, Optional
import enum


@dataclass(frozen=True)
class Point:
    x: int
    y: int

    def to_tuple(self) -> Tuple[int, int]:
        return (int(self.x), int(self.y))

    def __iter__(self) -> Iterator[int]:
        yield from (int(self.x), int(self.y))


@dataclass(frozen=True)
class Size:
    width: int
    height: int

    def to_tuple(self) -> Tuple[int, int]:
        return (int(self.width), int(self.height))

    def __iter__(self) -> Iterator[int]:
        yield from (int(self.width), int(self.height))


@dataclass(frozen=True)
class Rect:
    x: int
    y: int
    width: int
    height: int

    @staticmethod
    def from_tuple(t: Tuple[int, int, int, int]) -> "Rect":
        x, y, w, h = t
        return Rect(int(x), int(y), int(w), int(h))

    def to_tuple(self) -> Tuple[int, int, int, int]:
        return (int(self.x), int(self.y), int(self.width), int(self.height))

    def __iter__(self) -> Iterator[int]:
        yield from (int(self.x), int(self.y), int(self.width), int(self.height))

    @property
    def right(self) -> int:
        return int(self.x + self.width)

    @property
    def bottom(self) -> int:
        return int(self.y + self.height)

    # Fluent geometry helpers (pythonic alternative to layout module)
    def margin(self, *, all: Optional[int] = None, x: int = 0, y: int = 0) -> "Rect":
        if all is not None:
            x = y = int(all)
        nx = self.x + x
        ny = self.y + y
        nw = max(0, self.width - 2 * x)
        nh = max(0, self.height - 2 * y)
        return Rect(nx, ny, nw, nh)

    def split_h(self, *fractions: float, gap: int = 0) -> tuple["Rect", ...]:
        x, y, w, h = self.to_tuple()
        total_gap = max(0, (len(fractions) - 1) * gap)
        avail = max(0, h - total_gap)
        fr_sum = sum(fractions) or 1.0
        rows: list[Rect] = []
        yy = y
        for i, f in enumerate(fractions):
            hh = int(round(avail * (f / fr_sum))) if i < len(fractions) - 1 else (y + h - yy)
            rows.append(Rect(x, yy, w, max(0, hh)))
            yy += hh + (gap if i < len(fractions) - 1 else 0)
        return tuple(rows)

    def split_v(self, *fractions: float, gap: int = 0) -> tuple["Rect", ...]:
        x, y, w, h = self.to_tuple()
        total_gap = max(0, (len(fractions) - 1) * gap)
        avail = max(0, w - total_gap)
        fr_sum = sum(fractions) or 1.0
        cols: list[Rect] = []
        xx = x
        for i, f in enumerate(fractions):
            ww = int(round(avail * (f / fr_sum))) if i < len(fractions) - 1 else (x + w - xx)
            cols.append(Rect(xx, y, max(0, ww), h))
            xx += ww + (gap if i < len(fractions) - 1 else 0)
        return tuple(cols)


RectLike: TypeAlias = Union[Rect, Tuple[int, int, int, int]]

# Useful alias for sequences of draw commands (exported for type checking)
DrawCmdList: TypeAlias = Sequence[Any]

__all__ = [
    "Point",
    "Size",
    "Rect",
    "RectLike",
    "DrawCmdList",
]


# Enums mirroring low-level FFI constants for better typing/completions

class Color(enum.IntEnum):
    Reset = 0
    Black = 1
    Red = 2
    Green = 3
    Yellow = 4
    Blue = 5
    Magenta = 6
    Cyan = 7
    Gray = 8
    DarkGray = 9
    LightRed = 10
    LightGreen = 11
    LightYellow = 12
    LightBlue = 13
    LightMagenta = 14
    LightCyan = 15
    White = 16


class KeyCode(enum.IntEnum):
    Char = 0
    Enter = 1
    Left = 2
    Right = 3
    Up = 4
    Down = 5
    Esc = 6
    Backspace = 7
    Tab = 8
    Delete = 9
    Home = 10
    End = 11
    PageUp = 12
    PageDown = 13
    Insert = 14
    F1 = 100
    F2 = 101
    F3 = 102
    F4 = 103
    F5 = 104
    F6 = 105
    F7 = 106
    F8 = 107
    F9 = 108
    F10 = 109
    F11 = 110
    F12 = 111


class KeyMods(enum.IntFlag):
    NONE = 0
    SHIFT = 1 << 0
    ALT = 1 << 1
    CTRL = 1 << 2


class Mod(enum.IntFlag):
    """Text style modifiers for Style.mods (aligned with Ratatui Modifier bits)."""
    NONE = 0
    BOLD = 1 << 0
    DIM = 1 << 1
    ITALIC = 1 << 2
    UNDERLINED = 1 << 3
    SLOW_BLINK = 1 << 4
    RAPID_BLINK = 1 << 5
    REVERSED = 1 << 6
    HIDDEN = 1 << 7
    CROSSED_OUT = 1 << 8


class MouseKind(enum.IntEnum):
    Down = 1
    Up = 2
    Drag = 3
    Moved = 4
    ScrollUp = 5
    ScrollDown = 6


class MouseButton(enum.IntEnum):
    None_ = 0
    Left = 1
    Right = 2
    Middle = 3


@dataclass(frozen=True)
class KeyEvt:
    kind: str
    code: KeyCode
    ch: int
    mods: KeyMods


@dataclass(frozen=True)
class ResizeEvt:
    kind: str
    width: int
    height: int


@dataclass(frozen=True)
class MouseEvt:
    kind: str
    x: int
    y: int
    mouse_kind: MouseKind
    mouse_btn: MouseButton
    mods: KeyMods


Event: TypeAlias = Union[KeyEvt, ResizeEvt, MouseEvt]

__all__ += [
    "Color",
    "KeyCode",
    "KeyMods",
    "Mod",
    "MouseKind",
    "MouseButton",
    "KeyEvt",
    "ResizeEvt",
    "MouseEvt",
    "Event",
]
