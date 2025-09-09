from __future__ import annotations
from dataclasses import dataclass
from typing import Callable, Dict, Optional, Tuple, Iterable
from .types import KeyCode, KeyMods, KeyEvt, Event


Key = Tuple[KeyCode, KeyMods]  # (code, mods) — Char handled via ch in KeyEvt


@dataclass
class Binding:
    action: Callable[[Event], None]
    repeat: bool = True  # if False, only triggers on key-down edge (future use)


class Keymap:
    """Minimal keybinding helper.

    - Bind by (KeyCode, KeyMods), e.g., (KeyCode.Left, KeyMods.NONE) → handler.
    - Char keys are matched via evt.ch when code == KeyCode.Char; bind them by
      passing KeyCode.Char and inspecting evt.ch in your handler.
    - `handle(evt)` dispatches to the first matching binding and returns True if
      handled; otherwise returns False so callers can fall back to defaults.
    """

    def __init__(self) -> None:
        self._map: Dict[Key, Binding] = {}

    def bind(self, code: KeyCode, mods: KeyMods, action: Callable[[Event], None], *, repeat: bool = True) -> None:
        self._map[(code, mods)] = Binding(action=action, repeat=repeat)

    def unbind(self, code: KeyCode, mods: KeyMods) -> None:
        self._map.pop((code, mods), None)

    def handle(self, evt: Event) -> bool:
        if getattr(evt, 'kind', None) != 'key':
            return False
        assert isinstance(evt, KeyEvt)
        key = (evt.code, evt.mods)
        b = self._map.get(key)
        if b is None:
            return False
        try:
            b.action(evt)
            return True
        except Exception:
            return False

