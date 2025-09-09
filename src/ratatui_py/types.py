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
    "MouseKind",
    "MouseButton",
    "KeyEvt",
    "ResizeEvt",
    "MouseEvt",
    "Event",
]
