from __future__ import annotations
import os
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

    def render_cmds(self, rect: Tuple[int,int,int,int]) -> list:
        from . import Tabs, Sparkline, DrawCmd
        x, y, w, h = rect
        out = []
        if w < 20 or h < 8:
            p = Paragraph.from_text("Increase terminal size for dashboard…")
            p.set_block_title("Dashboard", True)
            return [DrawCmd.paragraph(p, rect)]
        header_h = min(3, h)
        footer_h = 5 if h >= 10 else max(3, h - header_h - 3)
        main_h = max(1, h - header_h - footer_h)
        header = (x, y, w, header_h)
        main = (x, y + header_h, w, main_h)
        footer = (x, y + header_h + main_h, w, footer_h)
        tabs = Tabs()
        tabs.set_titles(self.tabs)
        tabs.set_selected(self.tab_idx)
        tabs.set_block_title("ratatui-py Dashboard (a/d tabs, j/k move, r spike, q quit)", True)
        out.append(DrawCmd.tabs(tabs, header))
        left, right = split_v(main, 0.38, 0.62, gap=1)
        lst = UiList()
        for i, name in enumerate(self.services):
            lst.append_item(f"{'> ' if i == self.sel else '  '}{name}")
        lst.set_selected(self.sel)
        lst.set_block_title("Services", True)
        out.append(DrawCmd.list(lst, left))
        points = [(i, v) for i, v in enumerate(self.spark[-min(len(self.spark), max(10, right[2]-4)):])]
        ch = UiChart()
        ch.add_line("cpu", [(float(x), float(y)) for x, y in points])
        ch.set_axes_titles("t", "%")
        ch.set_block_title("CPU history", True)
        out.append(DrawCmd.chart(ch, right))
        bottom_top, bottom_bot = split_h(footer, 0.5, 0.5, gap=1)
        g_left, g_right = split_v(bottom_top, 0.5, 0.5, gap=1)
        g1 = UiGauge().ratio(self.cpu).label(f"CPU {int(self.cpu*100)}%")
        g1.set_block_title("CPU", True)
        out.append(DrawCmd.gauge(g1, g_left))
        g2 = UiGauge().ratio(self.mem).label(f"Mem {int(self.mem*100)}%")
        g2.set_block_title("Memory", True)
        out.append(DrawCmd.gauge(g2, g_right))
        sp = Sparkline()
        sp.set_values(self.spark[-(bottom_bot[2]-2 if bottom_bot[2] > 2 else len(self.spark)):])
        sp.set_block_title("Throughput", True)
        out.append(DrawCmd.sparkline(sp, bottom_bot))
        return out


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
    # Enable diagnostics only when explicitly requested
    if os.getenv("RATATUI_PY_DEBUG"):
        os.environ.setdefault("RUST_BACKTRACE", "full")
        os.environ.setdefault("RATATUI_FFI_TRACE", "1")
        os.environ.setdefault("RATATUI_FFI_NO_ALTSCR", "1")
        os.environ.setdefault("RATATUI_FFI_PROFILE", "debug")
        os.environ.setdefault("RATATUI_FFI_LOG", str((__import__('pathlib').Path('.').resolve() / 'ratatui_ffi.log')))
    # Link sources now that classes exist
    DashboardDemo.source_obj = run_dashboard
    ChartPlaygroundDemo.source_obj = getattr(ChartPlaygroundDemo, 'render_cmds', ChartPlaygroundDemo.render)
    SpectrumAnalyzerDemo.source_obj = getattr(SpectrumAnalyzerDemo, 'render_cmds', SpectrumAnalyzerDemo.render)
    LogViewerDemo.source_obj = getattr(LogViewerDemo, 'render_cmds', LogViewerDemo.render)
    MarkdownViewerDemo.source_obj = getattr(MarkdownViewerDemo, 'render_cmds', MarkdownViewerDemo.render)
    FileManagerDemo.source_obj = getattr(FileManagerDemo, 'render_cmds', FileManagerDemo.render)
    ChatDemo.source_obj = getattr(ChatDemo, 'render_cmds', ChatDemo.render)
    PlasmaDemo.source_obj = getattr(PlasmaDemo, 'render_cmds', PlasmaDemo.render)
    MandelbrotDemo.source_obj = getattr(MandelbrotDemo, 'render_cmds', MandelbrotDemo.render)

    demos: List[DemoBase] = [
        HelloDemo(),
        WidgetsDemo(),
        LifeDemo(),
        DashboardDemo(),
        ChartPlaygroundDemo(),
        SpectrumAnalyzerDemo(),
        LogViewerDemo(),
        MarkdownViewerDemo(),
        FileManagerDemo(),
        ChatDemo(),
        PlasmaDemo(),
        MandelbrotDemo(),
    ]
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
            pcode = Paragraph.new_empty()
            # naive syntax highlighting for Python-like code (no extra deps)
            kw = {
                'def','class','return','if','elif','else','for','while','try','except','finally','from','import','as','with','lambda','True','False','None','yield','in','and','or','not'
            }
            from . import Style, FFI_COLOR
            def emit_token(t: str, kind: str):
                if kind == 'kw': st = Style(fg=FFI_COLOR['LightMagenta'])
                elif kind == 'str': st = Style(fg=FFI_COLOR['LightYellow'])
                elif kind == 'com': st = Style(fg=FFI_COLOR['DarkGray'])
                elif kind == 'num': st = Style(fg=FFI_COLOR['LightCyan'])
                elif kind == 'dec': st = Style(fg=FFI_COLOR['LightGreen'])
                else: st = Style()
                pcode.append_span(t, st)
            import string
            ident_chars = string.ascii_letters + string.digits + '_'
            for line in vis:
                i = 0
                n = len(line)
                in_str = False
                sd = ''
                while i < n:
                    ch = line[i]
                    if in_str:
                        j = i
                        while j < n and line[j] != sd:
                            # naive: no escaping handling
                            j += 1
                        j = min(n, j+1)
                        emit_token(line[i:j], 'str')
                        i = j
                        in_str = False
                        continue
                    if ch == '#' :
                        emit_token(line[i:], 'com')
                        i = n
                        break
                    if ch in ('"', "'"):
                        in_str = True; sd = ch; i += 0  # handled next loop
                        # start string marker
                        i += 0
                        continue
                    if ch == '@':
                        j = i+1
                        while j < n and line[j] in ident_chars:
                            j += 1
                        emit_token(line[i:j], 'dec')
                        i = j
                        continue
                    if ch.isalpha() or ch == '_':
                        j = i+1
                        while j < n and line[j] in ident_chars:
                            j += 1
                        word = line[i:j]
                        emit_token(word, 'kw' if word in kw else 'id')
                        i = j
                        continue
                    if ch.isdigit():
                        j = i+1
                        while j < n and line[j].isdigit():
                            j += 1
                        emit_token(line[i:j], 'num')
                        i = j
                        continue
                    emit_token(ch, 'other')
                    i += 1
                pcode.line_break()
            pcode.set_block_title(f"{demo.name} – Source", True)

            # If the demo provides batched commands, render both panes in one frame.
            # Otherwise, draw code first and let the demo render itself.
            demo_cmds = demo.render_cmds(demo_rect)
            if demo_cmds:
                cmds = [DrawCmd.paragraph(pcode, code_rect)] + demo_cmds
                ok = term.draw_frame(cmds)
                if not ok:
                    demo.render(term, demo_rect)
            else:
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

# Link demo source for code pane is performed inside run_demo_hub after classes are defined


class ChartPlaygroundDemo(DemoBase):
    name = "Charts"
    desc = "Interactive line charts"
    source_obj = None

    def __init__(self) -> None:
        self.t = 0.0
        self.zoom = 1.0
        self.speed = 1.0

    def on_key(self, evt: dict) -> None:
        if evt.get("kind") != "key":
            return
        ch = evt.get("ch", 0)
        if not ch:
            return
        c = chr(ch).lower()
        if c == '+':
            self.zoom = min(4.0, self.zoom * 1.25)
        elif c == '-':
            self.zoom = max(0.25, self.zoom * 0.8)
        elif c == 'f':
            self.speed = min(8.0, self.speed * 1.4)
        elif c == 's':
            self.speed = max(0.125, self.speed * 0.7)

    def tick(self, dt: float) -> None:
        self.t += dt * self.speed

    def render_cmds(self, rect: Tuple[int,int,int,int]) -> list:
        from . import Chart, Style, FFI_COLOR, DrawCmd
        x, y, w, h = rect
        ch = Chart()
        n = max(20, w - 4)
        import math
        zoom = max(0.001, self.zoom)
        pts1 = [( (i/n)*(8.0/zoom), math.sin((i/n)*(8.0/zoom) + self.t)) for i in range(n)]
        pts2 = [( (i/n)*(8.0/zoom), math.cos((i/n)*(8.0/zoom) * 1.2 + self.t*0.8)) for i in range(n)]
        ch.add_line("sin", pts1, Style(fg=FFI_COLOR["LightCyan"]))
        ch.add_line("cos", pts2, Style(fg=FFI_COLOR["LightMagenta"]))
        ch.set_axes_titles("t", "val")
        ch.set_block_title("Chart Playground [+/- zoom, f/s speed, q quit]", True)
        return [DrawCmd.chart(ch, rect)]

    def render_cmds(self, rect: Tuple[int,int,int,int]) -> list:
        from . import Chart, Style, FFI_COLOR, DrawCmd
        x, y, w, h = rect
        ch = Chart()
        n = max(20, w - 4)
        import math
        pts1 = [( (i/n)*(8.0/self.zoom), math.sin((i/n)*(8.0/self.zoom) + self.t)) for i in range(n)]
        pts2 = [( (i/n)*(8.0/self.zoom), math.cos((i/n)*(8.0/self.zoom) * 1.2 + self.t*0.8)) for i in range(n)]
        ch.add_line("sin", pts1, Style(fg=FFI_COLOR["LightCyan"]))
        ch.add_line("cos", pts2, Style(fg=FFI_COLOR["LightMagenta"]))
        ch.set_axes_titles("t", "val")
        ch.set_block_title("Chart Playground [+/- zoom, f/s speed, q quit]", True)
        return [DrawCmd.chart(ch, rect)]


class LogViewerDemo(DemoBase):
    name = "Logs"
    desc = "Streaming log viewer with search"
    source_obj = None

    def __init__(self) -> None:
        from . import List
        self.lst = List()
        self.sel = None
        self.buf: list[str] = []
        self.q = ""
        self.t = 0.0

    def on_key(self, evt: dict) -> None:
        if evt.get("kind") != "key":
            return
        ch = evt.get("ch", 0)
        if not ch:
            return
        c = chr(ch)
        if c == '\b' or ord(c) == 127:
            self.q = self.q[:-1]
        elif c == '\n':
            pass
        elif c.isprintable():
            self.q += c

    def tick(self, dt: float) -> None:
        self.t += dt
        import random
        if self.t >= 0.1:
            self.t = 0.0
            lvl = random.choice(["INFO", "WARN", "DEBUG", "ERROR"]) 
            msg = random.choice(["started", "connected", "timeout", "retry", "ok"]) 
            line = f"{lvl} service={random.randint(1,4)} msg={msg} id={random.randint(1000,9999)}"
            self.buf.append(line)
            if len(self.buf) > 500:
                self.buf.pop(0)

    def render_cmds(self, rect: Tuple[int,int,int,int]) -> list:
        from . import List, Paragraph, DrawCmd
        x, y, w, h = rect
        top, bot = split_h(rect, 1.0, 3.0, gap=1)
        rows = [s for s in self.buf if self.q.lower() in s.lower()]
        lst = List()
        for s in rows[-(h-4):]:
            lst.append_item(s)
        lst.set_block_title("Logs", True)
        p = Paragraph.from_text(f"/ {self.q}\nType to filter. Backspace deletes. q to quit")
        p.set_block_title("Search", True)
        return [DrawCmd.list(lst, top), DrawCmd.paragraph(p, bot)]


class MarkdownViewerDemo(DemoBase):
    name = "Markdown"
    desc = "Simple Markdown viewer (scroll)"
    source_obj = None

    def __init__(self) -> None:
        sample = [
            "# ratatui-py",
            "",
            "Python bindings for Ratatui (Rust TUI).",
            "",
            "- Paragraph, List, Table, Gauge, Tabs, Chart, BarChart, Sparkline",
            "- Batched frame rendering",
            "- Diagnostics on demand",
            "",
            "## Controls",
            "j/k: scroll, q: quit",
            "",
        ]
        # Try to load README.md; fall back to sample
        try:
            import pathlib
            p = pathlib.Path(__file__).resolve().parents[2] / "README.md"
            if p.exists():
                text = p.read_text(encoding="utf-8", errors="replace")
                self.lines = text.splitlines() or sample
            else:
                self.lines = sample
        except Exception:
            self.lines = sample
        self.off = 0

    def on_key(self, evt: dict) -> None:
        if evt.get("kind") != "key":
            return
        ch = evt.get("ch", 0)
        if not ch:
            return
        c = chr(ch).lower()
        if c == 'j':
            self.off = min(max(0, len(self.lines) - 1), self.off + 1)
        elif c == 'k':
            self.off = max(0, self.off - 1)

    def render_cmds(self, rect: Tuple[int,int,int,int]) -> list:
        from . import Paragraph, DrawCmd
        x, y, w, h = rect
        view = self.lines[self.off:self.off+max(1, h-2)]
        p = Paragraph.from_text("\n".join(view))
        p.set_block_title(f"Markdown (lines {self.off+1}-{self.off+len(view)} / {len(self.lines)})", True)
        return [DrawCmd.paragraph(p, rect)]


class SpectrumAnalyzerDemo(DemoBase):
    name = "Spectrum"
    desc = "Synthetic audio spectrum (bars)"
    source_obj = None

    def __init__(self) -> None:
        import math
        self.t = 0.0
        self.n = 48
        self.vals = [0] * self.n
        self.decay = 0.85

    def tick(self, dt: float) -> None:
        import math, random
        self.t += dt
        # generate a few sine peaks + noise
        peaks = [
            (0.1, 8.0),
            (0.2, 4.5),
            (0.35, 6.2),
            (0.55, 7.0),
        ]
        new = []
        for i in range(self.n):
            x = i / max(1, self.n - 1)
            v = 0.0
            for a, f in peaks:
                v += a * max(0.0, math.sin((x * f + self.t * 2.0)))
            v += 0.05 * random.random()
            new.append(int(max(0.0, v) * 40))
        # decay / peak-hold style
        self.vals = [max(int(self.vals[i] * self.decay), new[i]) for i in range(self.n)]

    def render_cmds(self, rect: Tuple[int,int,int,int]) -> list:
        from . import BarChart, DrawCmd
        b = BarChart()
        b.set_values(self.vals)
        b.set_labels([""] * len(self.vals))
        b.set_block_title("Spectrum (q quit)", True)
        return [DrawCmd.barchart(b, rect)]


class FileManagerDemo(DemoBase):
    name = "Files"
    desc = "Two‑pane file manager"
    source_obj = None

    def __init__(self) -> None:
        import os
        self.left_dir = os.getcwd()
        self.right_dir = os.getcwd()
        self.left_sel = 0
        self.right_sel = 0
        self.focus = 'left'

    def _listdir(self, path: str) -> list[str]:
        import os
        try:
            entries = os.listdir(path)
        except Exception:
            return []
        entries.sort(key=str.lower)
        # show parent and directories first
        out = [".."]
        for e in entries:
            p = os.path.join(path, e)
            if os.path.isdir(p):
                out.append(e + "/")
        for e in entries:
            p = os.path.join(path, e)
            if not os.path.isdir(p):
                out.append(e)
        return out

    def on_key(self, evt: dict) -> None:
        if evt.get("kind") != "key":
            return
        code = evt.get("code", 0)
        ch = evt.get("ch", 0)
        import os
        if code in (2,):  # left
            self.focus = 'left'
            return
        if code in (3,):  # right
            self.focus = 'right'
            return
        if ch:
            c = chr(ch).lower()
            if c == 'j':
                if self.focus == 'left':
                    self.left_sel += 1
                else:
                    self.right_sel += 1
            elif c == 'k':
                if self.focus == 'left':
                    self.left_sel = max(0, self.left_sel - 1)
                else:
                    self.right_sel = max(0, self.right_sel - 1)
            elif c == '\r':
                # enter directory
                if self.focus == 'left':
                    items = self._listdir(self.left_dir)
                    idx = min(self.left_sel, max(0, len(items)-1))
                    target = items[idx] if items else None
                    if target:
                        path = os.path.normpath(os.path.join(self.left_dir, target))
                        if target == "..":
                            self.left_dir = os.path.dirname(self.left_dir)
                            self.left_sel = 0
                        elif os.path.isdir(path):
                            self.left_dir = path
                            self.left_sel = 0
                else:
                    items = self._listdir(self.right_dir)
                    idx = min(self.right_sel, max(0, len(items)-1))
                    target = items[idx] if items else None
                    if target:
                        path = os.path.normpath(os.path.join(self.right_dir, target))
                        if target == "..":
                            self.right_dir = os.path.dirname(self.right_dir)
                            self.right_sel = 0
                        elif os.path.isdir(path):
                            self.right_dir = path
                            self.right_sel = 0

    def render_cmds(self, rect: Tuple[int,int,int,int]) -> list:
        from . import List, DrawCmd
        left, right = split_v(rect, 0.5, 0.5, gap=1)
        litems = self._listdir(self.left_dir)
        ritems = self._listdir(self.right_dir)
        l = List()
        for s in litems: l.append_item(s)
        r = List()
        for s in ritems: r.append_item(s)
        l.set_selected(min(self.left_sel, max(0, len(litems)-1)))
        r.set_selected(min(self.right_sel, max(0, len(ritems)-1)))
        l.set_block_title(f"{self.left_dir}  (j/k, Enter, ← focus)", True)
        r.set_block_title(f"{self.right_dir}  (j/k, Enter, → focus)", True)
        return [DrawCmd.list(l, left), DrawCmd.list(r, right)]


class ChatDemo(DemoBase):
    name = "Chat"
    desc = "Mock chat UI"
    source_obj = None

    def __init__(self) -> None:
        self.msgs: list[str] = ["Welcome to ratatui-py chat! (Enter sends, q quits)"]
        self.input = ""

    def on_key(self, evt: dict) -> None:
        if evt.get("kind") != "key":
            return
        ch = evt.get("ch", 0)
        if not ch:
            return
        c = chr(ch)
        if c == '\r':
            if self.input.strip():
                self.msgs.append(self.input)
                if len(self.msgs) > 200: self.msgs.pop(0)
                self.input = ""
        elif c == '\b' or ord(c) == 127:
            self.input = self.input[:-1]
        elif c.isprintable():
            self.input += c

    def render_cmds(self, rect: Tuple[int,int,int,int]) -> list:
        from . import List, Paragraph, DrawCmd
        main, inp = split_h(rect, 1.0, 3.0, gap=1)
        lst = List()
        start = max(0, len(self.msgs) - (main[3] - 2))
        for s in self.msgs[start:]: lst.append_item(s)
        lst.set_block_title("Messages", True)
        p = Paragraph.from_text(self.input)
        p.set_block_title("Input", True)
        return [DrawCmd.list(lst, main), DrawCmd.paragraph(p, inp)]


class PlasmaDemo(DemoBase):
    name = "Plasma"
    desc = "Demoscene plasma shader"
    source_obj = None

    def __init__(self) -> None:
        self.t = 0.0
        self.paused = False
        self.speed = 1.0
        # simple ASCII gradient (light to dark)
        self.grad = " .:-=+*#%@"

    def on_key(self, evt: dict) -> None:
        if evt.get("kind") != "key":
            return
        ch = evt.get("ch", 0)
        if not ch:
            return
        c = chr(ch).lower()
        if c == 'p':
            self.paused = not self.paused
        elif c == '+':
            self.speed = min(5.0, self.speed * 1.25)
        elif c == '-':
            self.speed = max(0.2, self.speed * 0.8)

    def tick(self, dt: float) -> None:
        if not self.paused:
            self.t += dt * self.speed

    def render_cmds(self, rect: Tuple[int,int,int,int]) -> list:
        from . import Paragraph
        x, y, w, h = rect
        if w <= 0 or h <= 0:
            return []
        import math
        # plasma based on combined sines in screen space + time
        lines = []
        for j in range(h):
            row = []
            for i in range(w):
                xf = i / max(1, w - 1)
                yf = j / max(1, h - 1)
                v = 0.0
                v += math.sin((xf * 6.283) + self.t)
                v += math.sin((yf * 6.283) * 1.5 - self.t * 0.8)
                v += math.sin((xf + yf) * 6.283 * 0.7 + self.t * 0.5)
                # normalize to 0..1
                vn = (v / 3.0 + 1.0) * 0.5
                idx = int(vn * (len(self.grad) - 1))
                row.append(self.grad[idx])
            lines.append("".join(row))
        p = Paragraph.from_text("\n".join(lines))
        p.set_block_title("Plasma (p pause, +/- speed)", True)
        return [DrawCmd.paragraph(p, rect)]


class MandelbrotDemo(DemoBase):
    name = "Mandelbrot"
    desc = "Zoomable Mandelbrot fractal"
    source_obj = None

    def __init__(self) -> None:
        # Viewport center and scale (imaginary half-height)
        self.cx = -0.5
        self.cy = 0.0
        self.scale = 1.2  # larger => zoomed out
        self.max_iter = 80
        # character gradient light→dark
        self.grad_sets = [
            " .:-=+*#%@",
            " '`.:-=+*#%@",
            " .,:;ox%#@",
        ]
        self.grad_idx = 0

    def on_key(self, evt: dict) -> None:
        if evt.get("kind") != "key":
            return
        code = evt.get("code", 0)
        ch = evt.get("ch", 0)
        if ch:
            c = chr(ch).lower()
            if c == '+':
                self.scale *= 0.8
            elif c == '-':
                self.scale *= 1.25
            elif c == 'i':
                self.max_iter = min(500, self.max_iter + 10)
            elif c == 'k':
                self.max_iter = max(20, self.max_iter - 10)
            elif c == 'c':
                self.grad_idx = (self.grad_idx + 1) % len(self.grad_sets)
        # pan with arrows
        step = self.scale * 0.2
        if code == 2:  # left
            self.cx -= step
        elif code == 3:  # right
            self.cx += step
        elif code == 4:  # up
            self.cy -= step
        elif code == 5:  # down
            self.cy += step

    def render_cmds(self, rect: Tuple[int,int,int,int]) -> list:
        from . import Paragraph, DrawCmd
        x, y, w, h = rect
        if w <= 0 or h <= 0:
            return []
        # Aspect-correct viewport mapping
        aspect = (w / max(1, h))
        half_h = self.scale
        half_w = self.scale * aspect
        xmin = self.cx - half_w
        xmax = self.cx + half_w
        ymin = self.cy - half_h
        ymax = self.cy + half_h
        grad = self.grad_sets[self.grad_idx]
        gmax = len(grad) - 1
        lines = []
        for j in range(h):
            cy = ymin + (ymax - ymin) * (j / max(1, h - 1))
            row = []
            for i in range(w):
                cx = xmin + (xmax - xmin) * (i / max(1, w - 1))
                zx = 0.0
                zy = 0.0
                it = 0
                while it < self.max_iter and zx*zx + zy*zy <= 4.0:
                    zx, zy = zx*zx - zy*zy + cx, 2.0*zx*zy + cy
                    it += 1
                if it >= self.max_iter:
                    row.append(' ')
                else:
                    t = it / self.max_iter
                    idx = int(t * gmax)
                    row.append(grad[idx])
            lines.append(''.join(row))
        p = Paragraph.from_text("\n".join(lines))
        p.set_block_title(f"Mandelbrot (+/- zoom, arrows pan, i/k iters={self.max_iter}, c palette)", True)
        return [DrawCmd.paragraph(p, rect)]
