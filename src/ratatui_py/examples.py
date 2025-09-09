from __future__ import annotations
from . import Terminal, Paragraph, List, Table, Gauge, Style, FFI_COLOR
from typing import List as _List, Tuple
import random
import time


def hello_main() -> None:
    with Terminal() as term:
        p = Paragraph.from_text("Hello from Python!\nThis is ratatui.\n\nPress any key to exit.")
        p.set_block_title("Demo", True)
        p.append_line("\nStyled line", Style(fg=FFI_COLOR["LightCyan"]))
        term.draw_paragraph(p)
        # Wait for a key press (or 5s timeout)
        evt = term.next_event(5000)
        _ = evt


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
        tbl.set_block_title("Table (press any key)", True)

        g = Gauge().ratio(0.42).label("42%")
        g.set_block_title("Gauge", True)

        term.draw_list(lst, (0, 0, 30, 6))
        term.draw_table(tbl, (0, 6, 30, 6))
        term.draw_gauge(g, (0, 12, 30, 3))
        # Wait for a key press (or 5s timeout)
        evt = term.next_event(5000)
        _ = evt


def _rand_grid(w: int, h: int, p: float = 0.25) -> _List[_List[int]]:
    return [[1 if random.random() < p else 0 for _ in range(w)] for _ in range(h)]


def _step(grid: _List[_List[int]]) -> _List[_List[int]]:
    h = len(grid)
    if h == 0:
        return grid
    w = len(grid[0])
    out = [[0] * w for _ in range(h)]
    for y in range(h):
        ym = (y - 1) % h
        yp = (y + 1) % h
        row = grid[y]
        row_m = grid[ym]
        row_p = grid[yp]
        for x in range(w):
            xm = (x - 1) % w
            xp = (x + 1) % w
            s = (
                row_m[xm]
                + row_m[x]
                + row_m[xp]
                + row[xm]
                + row[xp]
                + row_p[xm]
                + row_p[x]
                + row_p[xp]
            )
            alive = row[x]
            if alive and (s == 2 or s == 3):
                out[y][x] = 1
            elif (not alive) and s == 3:
                out[y][x] = 1
            else:
                out[y][x] = 0
    return out


def _render_text(grid: _List[_List[int]]) -> str:
    # Use '█' for alive, ' ' for dead
    return "\n".join("".join("█" if c else " " for c in row) for row in grid)


def life_main() -> None:
    # Conway's Game of Life demo
    with Terminal() as term:
        width, height = term.size()
        # Ensure at least some reasonable size
        width = max(10, width)
        height = max(5, height)
        grid = _rand_grid(width, height, p=0.25)
        paused = False
        delay = 0.1  # seconds per step
        last = time.monotonic()

        while True:
            now = time.monotonic()
            # Input: poll quickly to stay responsive
            evt = term.next_event(10)
            if evt:
                if evt.get("kind") == "key":
                    ch = evt.get("ch", 0)
                    if ch:
                        c = chr(ch).lower()
                        if c == "q":
                            break
                        if c == "p":
                            paused = not paused
                        if c == "+":
                            delay = max(0.01, delay * 0.8)
                        if c == "-":
                            delay = min(1.0, delay * 1.25)
                        if c == "r":
                            grid = _rand_grid(width, height, p=0.25)
                elif evt.get("kind") == "resize":
                    width = max(10, evt.get("width", width))
                    height = max(5, evt.get("height", height))
                    grid = _rand_grid(width, height, p=0.25)

            if not paused and (now - last) >= delay:
                grid = _step(grid)
                last = now

            # Render current state
            text = _render_text(grid) + "\n\n[q]uit [p]ause [+/-] speed [r]andomize"
            p = Paragraph.from_text(text)
            p.set_block_title("Conway's Game of Life", True)
            term.draw_paragraph(p)
