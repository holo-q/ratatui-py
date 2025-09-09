from __future__ import annotations
import time
import inspect
from typing import Optional, Tuple, List

from . import (
    Terminal,
    Paragraph,
    List as UiList,
    Table as UiTable,
    Gauge as UiGauge,
    Chart as UiChart,
    Style,
    FFI_COLOR,
)
from . import examples as ex


class DemoBase:
    name: str = "Demo"
    desc: str = ""
    source_obj = None  # object to inspect for source

    def on_key(self, evt: dict) -> None:
        pass

    def tick(self, dt: float) -> None:
        pass

    def render(self, term: Terminal, rect: Tuple[int, int, int, int]) -> None:
        pass


class HelloDemo(DemoBase):
    name = "Hello"
    desc = "Basic paragraph + help"
    source_obj = ex.hello_main

    def render(self, term: Terminal, rect: Tuple[int, int, int, int]) -> None:
        p = Paragraph.from_text(
            "Hello from Python!\nThis is ratatui.\n\n" \
            "Press Tab to switch demos, q to quit.\n"
        )
        p.set_block_title("Hello", True)
        term.draw_paragraph(p, rect)


class WidgetsDemo(DemoBase):
    name = "Widgets"
    desc = "List + Table + Gauge"
    source_obj = ex.widgets_main

    def __init__(self) -> None:
        self.lst = UiList()
        for i in range(1, 8):
            self.lst.append_item(f"Item {i}")
        self.lst.set_selected(2)
        self.tbl = UiTable()
        self.tbl.set_headers(["A", "B", "C"])
        self.tbl.append_row(["1", "2", "3"])
        self.tbl.append_row(["x", "y", "z"])
        self.g = UiGauge().ratio(0.42).label("42%")

    def render(self, term: Terminal, rect: Tuple[int, int, int, int]) -> None:
        x, y, w, h = rect
        h1 = max(3, h // 3)
        h2 = max(3, h // 3)
        h3 = max(1, h - h1 - h2)
        self.lst.set_block_title("List", True)
        term.draw_list(self.lst, (x, y, w, h1))
        self.tbl.set_block_title("Table", True)
        term.draw_table(self.tbl, (x, y + h1, w, h2))
        self.g.set_block_title("Gauge", True)
        term.draw_gauge(self.g, (x, y + h1 + h2, w, h3))


class LifeDemo(DemoBase):
    name = "Life"
    desc = "Conway's Game of Life"
    source_obj = ex.life_main

    def __init__(self) -> None:
        self.grid: List[List[int]] = []
        self.paused = False
        self.delay = 0.1
        self._acc = 0.0

    def _ensure(self, w: int, h: int) -> None:
        if not self.grid or len(self.grid) != h or len(self.grid[0]) != w:
            # new random grid
            self.grid = ex._rand_grid(w, h, p=0.25)

    def on_key(self, evt: dict) -> None:
        if evt.get("kind") != "key":
            return
        ch = evt.get("ch", 0)
        if not ch:
            return
        c = chr(ch).lower()
        if c == "p":
            self.paused = not self.paused
        elif c == "+":
            self.delay = max(0.01, self.delay * 0.8)
        elif c == "-":
            self.delay = min(1.0, self.delay * 1.25)
        elif c == "r":
            if self.grid:
                self.grid = ex._rand_grid(len(self.grid[0]), len(self.grid), p=0.25)

    def tick(self, dt: float) -> None:
        if self.paused:
            return
        self._acc += dt
        if self._acc >= self.delay:
            self.grid = ex._step(self.grid) if self.grid else self.grid
            self._acc = 0.0

    def render(self, term: Terminal, rect: Tuple[int, int, int, int]) -> None:
        x, y, w, h = rect
        self._ensure(w, h - 2 if h > 2 else h)
        text = ex._render_text(self.grid)
        hints = "\n[q]uit [Tab] next [p]ause [+/-] speed [r]andomize"
        p = Paragraph.from_text(text + hints)
        p.set_block_title("Conway's Life", True)
        term.draw_paragraph(p, rect)


def _load_source(obj) -> str:
    try:
        src = inspect.getsource(obj)
    except Exception:
        src = "<source unavailable>"
    return src.rstrip("\n")


def _render_code(term: Terminal, rect: Tuple[int, int, int, int], title: str, code: str, scroll: int) -> None:
    lines = code.splitlines()
    if scroll < 0:
        scroll = 0
    visible = lines[scroll:]
    text = "\n".join(visible)
    p = Paragraph.from_text(text)
    p.set_block_title(title, True)
    term.draw_paragraph(p, rect)


def run_demo_hub() -> None:
    demos: List[DemoBase] = [HelloDemo(), WidgetsDemo(), LifeDemo()]
    idx = 0
    code_scroll = 0
    last = time.monotonic()

    with Terminal() as term:
        while True:
            now = time.monotonic()
            dt = now - last
            last = now

            width, height = term.size()
            # layout: left demo area, right code pane
            code_w = max(20, int(width * 0.42))
            demo_w = max(10, width - code_w)
            demo_rect = (0, 0, demo_w, height)
            code_rect = (demo_w, 0, code_w, height)

            demo = demos[idx]
            demo.tick(dt)

            # draw demo
            demo.render(term, demo_rect)

            # draw code pane
            src = _load_source(demo.source_obj)
            _render_code(term, code_rect, f"{demo.name} – Source", src, code_scroll)

            # input handling
            evt = term.next_event(50)
            if evt:
                if evt.get("kind") == "key":
                    code = evt.get("code", 0)
                    ch = evt.get("ch", 0)
                    if code in (2,):  # Left
                        idx = (idx - 1) % len(demos)
                        code_scroll = 0
                        continue
                    if code in (3, 9):  # Right or Tab
                        idx = (idx + 1) % len(demos)
                        code_scroll = 0
                        continue
                    if ch:
                        c = chr(ch).lower()
                        if c == "q":
                            break
                        if c == "w":
                            code_scroll = max(0, code_scroll - 1)
                            continue
                        if c == "s":
                            code_scroll += 1
                            continue
                    # pass to demo
                    demo.on_key(evt)


if __name__ == "__main__":
    run_demo_hub()

