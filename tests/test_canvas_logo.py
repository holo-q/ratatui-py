import pytest

from ratatui_py import Canvas, Style, headless_render_canvas, headless_render_logo, rgb


def test_headless_logo_nonempty():
    try:
        out = headless_render_logo(40, 12)
    except OSError:
        pytest.skip("libratatui_ffi not available in this environment")
    if out == "":
        pytest.skip("headless logo not available in this FFI build")
    assert len(out.strip()) > 0


def test_headless_canvas_nonempty():
    try:
        cv = Canvas(0.0, 10.0, 0.0, 10.0)
        cv.add_line(0, 0, 10, 10, Style(fg=rgb(255, 0, 0)))
        out = headless_render_canvas(20, 10, cv)
    except OSError:
        pytest.skip("libratatui_ffi not available in this environment")
    if out == "":
        pytest.skip("headless canvas not available in this FFI build")
    assert len(out.strip()) > 0

