from __future__ import annotations
from dataclasses import dataclass
from typing import Iterator, Tuple, TypeAlias, Union, Sequence, Any


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

