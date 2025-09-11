"""Convenience imports for quick starts and REPLs.

Usage:
    from ratatui_py.prelude import *
"""
from .wrappers import (
    Terminal, Paragraph, List, Table, Gauge, Tabs, BarChart, Sparkline, Scrollbar, Chart,
    Style, DrawCmd, App, ListState, TableState, rgb, color_indexed, terminal_session,
)
from .layout import (
    margin, split_h, split_v,
    margin_rect, split_h_rect, split_v_rect,
    layout_split_ffi, split_h_ffi, split_v_ffi,
)
from .types import (
    Rect, Point, Size, RectLike,
    Color, KeyCode, KeyMods, MouseKind, MouseButton,
)
from .util import (
    frame_begin, BackgroundTask, ProcessTask,
)

__all__ = [name for name in globals().keys() if not name.startswith('_')]
