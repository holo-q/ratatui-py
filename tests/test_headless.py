import os

import pytest

from ratatui_py import Paragraph, List, Table, Gauge
import pytest
from ratatui_py import (
    headless_render_paragraph,
    headless_render_list,
    headless_render_table,
    headless_render_gauge,
)


def test_headless_paragraph_renders_text():
    try:
        p = Paragraph.from_text("Hello World")
        out = headless_render_paragraph(20, 3, p)
    except OSError:
        pytest.skip("libratatui_ffi not available in this environment")
    assert "Hello World" in out


def test_headless_list_and_table_basic():
    try:
        lst = List()
        lst.append_item("One")
        lst.append_item("Two")
        lst.set_selected(1)
        out_l = headless_render_list(20, 4, lst)
        assert "One" in out_l and "Two" in out_l

        tbl = Table()
        tbl.set_headers(["A", "B"]) 
        tbl.append_row(["1", "2"])
        out_t = headless_render_table(20, 4, tbl)
    except OSError:
        pytest.skip("libratatui_ffi not available in this environment")
    assert "A" in out_t and "1" in out_t


def test_headless_gauge_shows_label():
    try:
        g = Gauge().ratio(0.5).label("50%")
        out = headless_render_gauge(20, 3, g)
    except OSError:
        pytest.skip("libratatui_ffi not available in this environment")
    assert "50%" in out
