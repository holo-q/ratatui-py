"""Convenience imports for quick starts and REPLs.

Usage:
    from ratatui_py.prelude import *
"""
from . import (
    Terminal, Paragraph, List, Table, Gauge, Tabs, BarChart, Sparkline, Scrollbar, Chart,
    Style, DrawCmd, App,
    margin, split_h, split_v,
    margin_rect, split_h_rect, split_v_rect,
    Rect, Point, Size, RectLike,
    Color, KeyCode, KeyMods, MouseKind, MouseButton,
    frame_begin, BackgroundTask, ProcessTask,
)

__all__ = [name for name in globals().keys() if not name.startswith('_')]

