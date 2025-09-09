from __future__ import annotations
from . import Terminal, Paragraph, List, Table, Gauge, Style, FFI_COLOR


def hello_main() -> None:
    with Terminal() as term:
        p = Paragraph.from_text("Hello from Python!\nThis is ratatui.")
        p.set_block_title("Demo", True)
        p.append_line("\nStyled line", Style(fg=FFI_COLOR["LightCyan"]))
        term.draw_paragraph(p)


def widgets_main() -> None:
    with Terminal() as term:
        lst = List()
        for i in range(5):
            lst.append_item(f"Item {i}")
        lst.set_selected(2)
        lst.set_block_title("List", True)

        tbl = Table()
        tbl.set_headers(["A", "B", "C"])
        tbl.append_row(["1", "2", "3"])
        tbl.append_row(["x", "y", "z"])
        tbl.set_block_title("Table", True)

        g = Gauge().ratio(0.42).label("42%")
        g.set_block_title("Gauge", True)

        term.draw_list(lst, (0, 0, 30, 6))
        term.draw_table(tbl, (0, 6, 30, 6))
        term.draw_gauge(g, (0, 12, 30, 3))

