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
    DrawCmd,
)
from . import examples as ex
from .layout import margin, split_h, split_v


class DemoBase:
    name: str = "Demo"
    desc: str = ""
    source_obj = None  # object to inspect for source

    def on_key(self, evt: dict) -> None:
        pass

    def tick(self, dt: float) -> None:
        pass

    def render_cmds(self, rect: Tuple[int, int, int, int]) -> list:
        return []

    def render(self, term: Terminal, rect: Tuple[int, int, int, int]) -> None:
        # Fallback simple renderer; override in subclasses
        for cmd in self.render_cmds(rect):
            k = cmd.kind
            r = (cmd.rect.x, cmd.rect.y, cmd.rect.width, cmd.rect.height)
            if k == 1:  # Paragraph
                # We can't reconstruct from handle generically here; subclasses should override
                pass


class HelloDemo(DemoBase):
    name = "Hello"
    desc = "Basic paragraph + help"
    source_obj = ex.hello_main

    def render_cmds(self, rect: Tuple[int, int, int, int]) -> list:
        p = Paragraph.from_text(
            "Hello from Python!\nThis is ratatui.\n\n" \
            "Press Tab to switch demos, q to quit.\n"
        )
        p.set_block_title("Hello", True)
        return [DrawCmd.paragraph(p, rect)]

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

    def render_cmds(self, rect: Tuple[int, int, int, int]) -> list:
        x, y, w, h = rect
        h1 = max(3, h // 3)
        h2 = max(3, h // 3)
        h3 = max(1, h - h1 - h2)
        self.lst.set_block_title("List", True)
        c1 = DrawCmd.list(self.lst, (x, y, w, h1))
        self.tbl.set_block_title("Table", True)
        c2 = DrawCmd.table(self.tbl, (x, y + h1, w, h2))
        self.g.set_block_title("Gauge", True)
        c3 = DrawCmd.gauge(self.g, (x, y + h1 + h2, w, h3))
        return [c1, c2, c3]

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

    def render_cmds(self, rect: Tuple[int, int, int, int]) -> list:
        x, y, w, h = rect
        self._ensure(w, h - 2 if h > 2 else h)
        text = ex._render_text(self.grid)
        hints = "\n[q]uit [Tab] next [p]ause [+/-] speed [r]andomize"
        p = Paragraph.from_text(text + hints)
        p.set_block_title("Conway's Life", True)
        return [DrawCmd.paragraph(p, rect)]

    def render(self, term: Terminal, rect: Tuple[int, int, int, int]) -> None:
        x, y, w, h = rect
        self._ensure(w, h - 2 if h > 2 else h)
        text = ex._render_text(self.grid)
        hints = "\n[q]uit [Tab] next [p]ause [+/-] speed [r]andomize"
        p = Paragraph.from_text(text + hints)
        p.set_block_title("Conway's Life", True)
        term.draw_paragraph(p, rect)


class DashboardDemo(DemoBase):
    name = "Dashboard"
    desc = "Tabs + List + Chart + Gauges + Sparkline"
    source_obj = None  # filled dynamically below

    def __init__(self) -> None:
        self.tabs = ["Overview", "Services", "Metrics"]
        self.tab_idx = 0
        self.services = [f"svc-{i:02d}" for i in range(1, 9)]
        self.sel = 0
        self.cpu = 0.35
        self.mem = 0.55
        self.spark = [10, 12, 9, 14, 11, 13, 12, 16, 15, 14, 17, 16, 18]
        self.t = 0.0

    def on_key(self, evt: dict) -> None:
        if evt.get("kind") != "key":
            return
        ch = evt.get("ch", 0)
        if not ch:
            return
        c = chr(ch).lower()
        if c == 'a':
            self.tab_idx = (self.tab_idx - 1) % len(self.tabs)
        elif c == 'd':
            self.tab_idx = (self.tab_idx + 1) % len(self.tabs)
        elif c == 'j':
            self.sel = (self.sel + 1) % len(self.services)
        elif c == 'k':
            self.sel = (self.sel - 1) % len(self.services)
        elif c == 'r':
            # randomize a small spike
            self.cpu = min(0.99, self.cpu + 0.2)
            self.mem = min(0.99, self.mem + 0.15)

    def tick(self, dt: float) -> None:
        self.t += dt
        # gentle random walk for cpu/mem
        import random
        self.cpu = max(0.02, min(0.98, self.cpu + random.uniform(-0.05, 0.05)))
        self.mem = max(0.02, min(0.98, self.mem + random.uniform(-0.03, 0.03)))
        # update sparkline history
        val = max(1, min(50, (self.spark[-1] if self.spark else 20) + random.randint(-4, 5)))
        self.spark.append(val)
        if len(self.spark) > 50:
            self.spark.pop(0)

    def render(self, term: Terminal, rect: Tuple[int, int, int, int]) -> None:
        x, y, w, h = rect
        if w < 20 or h < 8:
            p = Paragraph.from_text("Increase terminal size for dashboard…")
            p.set_block_title("Dashboard", True)
            term.draw_paragraph(p, rect)
            return
        # layout: header (3), main (h-8), footer (5)
        header_h = min(3, h)
        footer_h = 5 if h >= 10 else max(3, h - header_h - 3)
        main_h = max(1, h - header_h - footer_h)
        header = (x, y, w, header_h)
        main = (x, y + header_h, w, main_h)
        footer = (x, y + header_h + main_h, w, footer_h)

        # header: tabs
        from . import Tabs
        tabs = Tabs()
        tabs.set_titles(self.tabs)
        tabs.set_selected(self.tab_idx)
        tabs.set_block_title("ratatui-py Dashboard (a/d tabs, j/k move, r spike, q quit)", True)
        term.draw_tabs(tabs, header)

        # main: left list, right chart
        left, right = split_v(main, 0.38, 0.62, gap=1)
        lst = UiList()
        for i, name in enumerate(self.services):
            lst.append_item(f"{'> ' if i == self.sel else '  '}{name}")
        lst.set_selected(self.sel)
        lst.set_block_title("Services", True)
        term.draw_list(lst, left)

        # Chart of CPU over time
        points = [(i, v) for i, v in enumerate(self.spark[-min(len(self.spark), max(10, right[2]-4)):])]
        ch = UiChart()
        ch.add_line("cpu", [(float(x), float(y)) for x, y in points])
        ch.set_axes_titles("t", "%")
        ch.set_block_title("CPU history", True)
        term.draw_chart(ch, right)

        # footer: two gauges + sparkline bar
        bottom_top, bottom_bot = split_h(footer, 0.5, 0.5, gap=1)
        g_left, g_right = split_v(bottom_top, 0.5, 0.5, gap=1)
        g1 = UiGauge().ratio(self.cpu).label(f"CPU {int(self.cpu*100)}%")
        g1.set_block_title("CPU", True)
        term.draw_gauge(g1, g_left)
        g2 = UiGauge().ratio(self.mem).label(f"Mem {int(self.mem*100)}%")
        g2.set_block_title("Memory", True)
        term.draw_gauge(g2, g_right)

        from . import Sparkline
        sp = Sparkline()
        sp.set_values(self.spark[-(bottom_bot[2]-2 if bottom_bot[2] > 2 else len(self.spark)):])
        sp.set_block_title("Throughput", True)
        term.draw_sparkline(sp, bottom_bot)


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
    demos: List[DemoBase] = [HelloDemo(), WidgetsDemo(), LifeDemo(), DashboardDemo()]
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
            # keep at least 10 cols for demo; clamp code width
            min_demo = 10
            code_w_target = max(20, int(width * 0.42))
            code_w_max = max(0, width - min_demo)
            code_w = min(code_w_target, code_w_max)
            demo_w = max(min_demo, width - code_w)
            demo_rect = (0, 0, demo_w, height)
            code_rect = (demo_w, 0, code_w, height)

            demo = demos[idx]
            demo.tick(dt)

            # Build code pane content
            src = _load_source(demo.source_obj)
            code_lines = src.splitlines()
            vis = code_lines[code_scroll:]
            code_text = "\n".join(vis)
            pcode = Paragraph.from_text(code_text)
            pcode.set_block_title(f"{demo.name} – Source", True)

            # Simple two-draw rendering (more compatible across envs)
            term.draw_paragraph(pcode, code_rect)
            demo.render(term, demo_rect)

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


def run_dashboard() -> None:
    demo = DashboardDemo()
    last = time.monotonic()
    with Terminal() as term:
        while True:
            now = time.monotonic()
            dt = now - last
            last = now
            demo.tick(dt)
            w, h = term.size()
            demo.render(term, (0, 0, w, h))
            evt = term.next_event(50)
            if evt and evt.get("kind") == "key":
                ch = evt.get("ch", 0)
                if ch and chr(ch).lower() == 'q':
                    break
                demo.on_key(evt)

# Link demo source for code pane
DashboardDemo.source_obj = run_dashboard
