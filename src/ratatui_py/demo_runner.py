from __future__ import annotations
import os
import sys
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

# Recording-friendly knobs
_REC = bool(os.getenv("ASCIINEMA_REC") or os.getenv("RATATUI_PY_RECORDING"))
_FPS = int(os.getenv("RATATUI_PY_FPS", "30"))
_STATIC = os.getenv("RATATUI_PY_STATIC", "0") not in ("0", "false", "False", "")
_NO_CODE = os.getenv("RATATUI_PY_NO_CODE", "1" if _REC else "0") not in ("0", "false", "False", "")

# Prefer inline mode (preserve scrollback) by default
os.environ.setdefault("RATATUI_FFI_NO_ALTSCR", "1")


def _sync_start():
    # iTerm2/kitty synchronized output; harmless elsewhere
    if _REC or os.getenv("RATATUI_PY_SYNC"):
        try:
            sys.stdout.write("\x1b[?2026h")
            sys.stdout.flush()
        except Exception:
            pass


def _sync_end():
    if _REC or os.getenv("RATATUI_PY_SYNC"):
        try:
            sys.stdout.write("\x1b[?2026l")
            sys.stdout.flush()
        except Exception:
            pass


def _cursor_hide():
    try:
        sys.stdout.write("\x1b[?25l")
        sys.stdout.flush()
    except Exception:
        pass


def _cursor_show():
    try:
        sys.stdout.write("\x1b[?25h")
        sys.stdout.flush()
    except Exception:
        pass


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
        code = int(evt.get("code", 0))
        ch = int(evt.get("ch", 0))
        # Support both arrow keys (codes) and vim-style chars
        if code == 2:  # Left
            self.tab_idx = (self.tab_idx - 1) % len(self.tabs)
            return
        if code in (3, 9):  # Right or Tab
            self.tab_idx = (self.tab_idx + 1) % len(self.tabs)
            return
        if code == 5:  # Down
            self.sel = (self.sel + 1) % len(self.services)
            return
        if code == 4:  # Up
            self.sel = (self.sel - 1) % len(self.services)
            return
        if ch:
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
        if obj is None:
            raise ValueError("no source_obj")
        # If given a bound/unbound function from a class, prefer the class source
        if inspect.isfunction(obj) or inspect.ismethod(obj):
            qn = getattr(obj, "__qualname__", "")
            globs = getattr(obj, "__globals__", {})
            if "." in qn:
                cls_name = qn.split(".")[0]
                cls = globs.get(cls_name)
                if inspect.isclass(cls):
                    return inspect.getsource(cls).rstrip("\n")
        if inspect.isclass(obj) or inspect.isfunction(obj) or inspect.ismethod(obj):
            return inspect.getsource(obj).rstrip("\n")
        # Fallback: module source
        mod = inspect.getmodule(obj)
        if mod is not None:
            return inspect.getsource(mod).rstrip("\n")
    except Exception:
        pass
    return "<source unavailable>"


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
    WidgetSceneDemo.source_obj = getattr(WidgetSceneDemo, 'render_cmds', WidgetSceneDemo.render)

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
        WidgetSceneDemo(),
        FireDemo(),
        TunnelDemo(),
        CubeDemo(),
    ]
    idx = 0
    code_scroll = 0
    last = time.monotonic()
    frame_budget = max(1, int(1000 / max(1, _FPS)))
    # Caches to reduce per-frame work
    src_cache: dict[object, tuple[str, list[str]]] = {}
    tokens_cache: dict[object, list[list[tuple[str, str]]]] = {}
    last_title_w = -1
    ptitle = None
    last_nav = {"w": -1, "idx": -1, "names": [], "pnav": None}
    last_draw = 0.0
    last_draw = 0.0
    with Terminal() as term:
        while True:
            now = time.monotonic()
            dt = now - last
            last = now
            if _STATIC:
                dt = 0.0
            width, height = term.size()
            # layout: title bar (1), navbar (1), then left demo area + right code pane
            # keep at least 10 cols for demo; clamp code width
            min_demo = 10
            code_w_target = 0 if _NO_CODE else max(20, int(width * 0.42))
            code_w_max = max(0, width - min_demo)
            code_w = min(code_w_target, code_w_max)
            demo_w = max(min_demo, width - code_w)

            # Reserve rows for title and navbar if possible
            use_title = height >= 1
            use_nav = height >= 2
            title_h = 1 if use_title else 0
            nav_h = 1 if use_nav else 0
            body_h = max(0, height - title_h - nav_h)

            title_rect = (0, 0, width, title_h) if use_title else (0, 0, 0, 0)
            nav_rect = (0, title_h, width, nav_h) if use_nav else (0, 0, 0, 0)
            body_y = title_h + nav_h
            demo_rect = (0, body_y, demo_w, body_h)
            code_rect = (demo_w, body_y, code_w, body_h)

            demo = demos[idx]
            demo.tick(dt)

            # Build title bar spanning full width
            if use_title:
                from . import Style, FFI_COLOR
                title_bg = FFI_COLOR.get('DarkGray', 0x40_40_40)
                title_fg = FFI_COLOR.get('White', 0xFF_FF_FF)
                max_w = title_rect[2]
                if last_title_w != max_w:
                    ptitle = Paragraph.new_empty()
                    cur_w = 0
                    def add_t(text: str, style: Style):
                        nonlocal cur_w
                        if max_w <= 0:
                            return
                        tw = len(text)
                        if cur_w + tw > max_w:
                            text = text[: max(0, max_w - cur_w)]
                            tw = len(text)
                        if tw > 0:
                            ptitle.append_span(text, style)
                            cur_w += tw
                    title = " ratatui-py demo "
                    add_t(title, Style(fg=title_fg, bg=title_bg))
                    if cur_w < max_w:
                        add_t(" " * (max_w - cur_w), Style(bg=title_bg))
                    last_title_w = max_w
                title_cmd = DrawCmd.paragraph(ptitle, title_rect)
            else:
                title_cmd = None

            # Build top navbar as contiguous blocks: inactive light bg, active vivid bg
            if use_nav:
                from . import Style, FFI_COLOR
                accent = FFI_COLOR.get('LightBlue', 0x00_00_FF)
                bg_inactive = FFI_COLOR.get('Gray', 0x80_80_80)
                fg_active = FFI_COLOR.get('Black', 0x00_00_00)
                fg_inactive = FFI_COLOR.get('Black', 0x00_00_00)
                names = [d.name for d in demos]
                max_w = nav_rect[2]
                need = last_nav["w"] != max_w or last_nav["idx"] != idx or last_nav["names"] != names
                if need:
                    pnav = Paragraph.new_empty()
                    cur_w = 0
                    def add_span(text: str, style: Style):
                        nonlocal cur_w
                        if max_w <= 0:
                            return
                        tw = len(text)
                        if cur_w + tw > max_w:
                            text = text[: max(0, max_w - cur_w)]
                            tw = len(text)
                        if tw > 0:
                            pnav.append_span(text, style)
                            cur_w += tw
                    for i, nm in enumerate(names):
                        active = (i == idx)
                        if active:
                            add_span(nm, Style(fg=fg_active, bg=accent))
                        else:
                            add_span(nm, Style(fg=fg_inactive, bg=bg_inactive))
                        if i != len(names) - 1:
                            add_span(' ', Style())
                    last_nav.update({"w": max_w, "idx": idx, "names": names[:], "pnav": pnav})
                else:
                    pnav = last_nav["pnav"]
                nav_cmd = DrawCmd.paragraph(pnav, nav_rect)
            else:
                nav_cmd = None

            # Build code pane content (cached source and tokenized lines)
            if _NO_CODE:
                demo_cmds = demo.render_cmds(demo_rect)
                if demo_cmds:
                    cmds = []
                    if title_cmd is not None:
                        cmds.append(title_cmd)
                    if nav_cmd is not None:
                        cmds.append(nav_cmd)
                    cmds.extend(demo_cmds)
                    _sync_start(); ok = term.draw_frame(cmds); _sync_end()
                    if not ok:
                        demo.render(term, demo_rect)
                else:
                    if use_title:
                        _sync_start(); term.draw_paragraph(ptitle, title_rect); _sync_end()
                    if use_nav:
                        _sync_start(); term.draw_paragraph(pnav, nav_rect); _sync_end()
                    _sync_start(); demo.render(term, demo_rect); _sync_end()
                # Input handling (fast path) and lightweight nav
                evt = term.next_event(min(20, frame_budget))
                if evt and evt.get("kind") == "key":
                    code = int(evt.get("code", 0))
                    ch = int(evt.get("ch", 0))
                    if ch and chr(ch).lower() == 'q':
                        break
                    # left/right/tab to switch demos
                    if code == 2:  # Left
                        idx = (idx - 1) % len(demos)
                    elif code in (3, 9):  # Right or Tab
                        idx = (idx + 1) % len(demos)
                    else:
                        demo.on_key(evt)
                else:
                    if _REC:
                        now3 = time.monotonic()
                        sleep_ms = frame_budget - int((now3 - now) * 1000)
                        if sleep_ms > 0:
                            time.sleep(sleep_ms / 1000.0)
                # Skip the rest of the code-pane path
                continue
            src_key = getattr(demo, 'source_obj', None) or demo.__class__
            if src_key not in src_cache:
                src = _load_source(src_key)
                lines = src.splitlines()
                src_cache[src_key] = (src, lines)
                # Tokenize once for all frames
                kw = {
                    'def','class','return','if','elif','else','for','while','try','except','finally','from','import','as','with','lambda','True','False','None','yield','in','and','or','not'
                }
                import string
                ident_chars = set(string.ascii_letters + string.digits + '_')
                toks_all = []
                for line in lines:
                    i = 0; n = len(line); in_str = False; sd = ''
                    row = []
                    while i < n:
                        ch = line[i]
                        if in_str:
                            j = i
                            while j < n and line[j] != sd:
                                j += 1
                            j = min(n, j+1)
                            row.append((line[i:j], 'str'))
                            i = j; in_str = False; continue
                        if ch == '#':
                            row.append((line[i:], 'com'))
                            i = n; break
                        if ch in ('"', "'"):
                            in_str = True; sd = ch; continue
                        if ch == '@':
                            j = i+1
                            while j < n and line[j] in ident_chars:
                                j += 1
                            row.append((line[i:j], 'dec'))
                            i = j; continue
                        if ch.isalpha() or ch == '_':
                            j = i+1
                            while j < n and line[j] in ident_chars:
                                j += 1
                            word = line[i:j]
                            row.append((word, 'kw' if word in kw else 'id'))
                            i = j; continue
                        if ch.isdigit():
                            j = i+1
                            while j < n and line[j].isdigit():
                                j += 1
                            row.append((line[i:j], 'num'))
                            i = j; continue
                        row.append((ch, 'other'))
                        i += 1
                    toks_all.append(row)
                tokens_cache[src_key] = toks_all
            src, code_lines = src_cache[src_key]
            # determine visible slice and scrollbar
            max_vis = max(1, code_rect[3] - 2)
            code_scroll = max(0, min(code_scroll, max(0, len(code_lines) - max_vis)))
            pcode = Paragraph.new_empty()
            from . import Style, FFI_COLOR
            styles = {
                'kw': Style(fg=FFI_COLOR['LightMagenta']),
                'str': Style(fg=FFI_COLOR['LightYellow']),
                'com': Style(fg=FFI_COLOR['DarkGray']),
                'num': Style(fg=FFI_COLOR['LightCyan']),
                'dec': Style(fg=FFI_COLOR['LightGreen']),
                'id': Style(),
                'other': Style(),
            }
            toks_all = tokens_cache[src_key]
            start = code_scroll
            end = min(len(code_lines), code_scroll + max_vis)
            for line_idx in range(start, end):
                for t, kind in toks_all[line_idx]:
                    pcode.append_span(t, styles.get(kind) or Style())
                pcode.line_break()
            # build a simple ASCII scrollbar on the far-right of code pane
            sb_cmd = []
            total = max(1, len(code_lines))
            bar_h = max(1, code_rect[3])
            # position of thumb within bar
            thumb_h = max(1, int(bar_h * min(1.0, max_vis / total)))
            thumb_y = int((bar_h - thumb_h) * (code_scroll / max(1, total - max_vis))) if total > max_vis else 0
            sb_lines = []
            for j in range(bar_h):
                sb_lines.append('█' if thumb_y <= j < thumb_y + thumb_h else '│')
            sb_rect = (code_rect[0] + max(0, code_rect[2]-1), code_rect[1], 1, code_rect[3])
            pscroll = Paragraph.from_text("\n".join(sb_lines))
            pcode.set_block_title(f"{demo.name} – Source", True)

            # If the demo provides batched commands, render both panes in one frame.
            # Otherwise, draw code first and let the demo render itself.
            demo_cmds = demo.render_cmds(demo_rect)
            # Optionally coalesce draws in static mode to avoid visible flashing
            if _STATIC and (now - last_draw) < 0.10:
                evt = term.next_event(min(20, frame_budget))
                if evt and evt.get("kind") == "key":
                    # process below as usual
                    pass
                else:
                    # Skip drawing this cycle
                    continue

            if demo_cmds:
                cmds = []
                if title_cmd is not None:
                    cmds.append(title_cmd)
                if nav_cmd is not None:
                    cmds.append(nav_cmd)
                cmds.extend([DrawCmd.paragraph(pcode, code_rect), DrawCmd.paragraph(pscroll, sb_rect)])
                cmds.extend(demo_cmds)
                _sync_start()
                ok = term.draw_frame(cmds)
                _sync_end()
                if not ok:
                    demo.render(term, demo_rect)
            else:
                # Bracket the entire multi-call frame in one synchronized update
                _sync_start()
                if use_title:
                    term.draw_paragraph(ptitle, title_rect)
                if use_nav:
                    term.draw_paragraph(pnav, nav_rect)
                term.draw_paragraph(pcode, code_rect)
                demo.render(term, demo_rect)
                _sync_end()
            last_draw = now

            # input handling with event drain to avoid backlog
            evt = term.next_event(min(20, frame_budget))
            if _REC and not evt:
                now3 = time.monotonic()
                sleep_ms = frame_budget - int((now3 - now) * 1000)
                if sleep_ms > 0:
                    time.sleep(sleep_ms / 1000.0)
            if evt:
                if evt.get("kind") == "key":
                    nav_delta = 0
                    scroll_delta = 0
                    set_home = set_end = False
                    quit_flag = False
                    last_demo_evt = None

                    def fold(e):
                        nonlocal nav_delta, scroll_delta, set_home, set_end, quit_flag, last_demo_evt
                        code = e.get("code", 0)
                        ch = e.get("ch", 0)
                        if code == 2:  # Left
                            nav_delta -= 1
                            return True
                        if code in (3, 9):  # Right or Tab
                            nav_delta += 1
                            return True
                        if code == 4:  # Up
                            scroll_delta -= 1
                            return True
                        if code == 5:  # Down
                            scroll_delta += 1
                            return True
                        if code == 12:  # PageUp
                            scroll_delta -= max_vis
                            return True
                        if code == 13:  # PageDown
                            scroll_delta += max_vis
                            return True
                        if code == 10:  # Home
                            set_home = True
                            set_end = False
                            return True
                        if code == 11:  # End
                            set_end = True
                            set_home = False
                            return True
                        if ch:
                            c = chr(ch).lower()
                            if c == 'q':
                                quit_flag = True
                                return True
                            if c == 'w':
                                scroll_delta -= 1
                                return True
                            if c == 's':
                                scroll_delta += 1
                                return True
                        # Keep last non-navigation event for the demo
                        last_demo_evt = e
                        return False

                    # Fold the first event then drain the rest non-blocking
                    fold(evt)
                    while True:
                        e = term.next_event(0)
                        if not e:
                            break
                        if e.get("kind") != "key":
                            last_demo_evt = e
                            continue
                        fold(e)

                    if quit_flag:
                        break
                    if nav_delta != 0:
                        idx = (idx + nav_delta) % len(demos)
                        code_scroll = 0
                        continue
                    if set_home:
                        code_scroll = 0
                        continue
                    if set_end:
                        code_scroll = 10**9
                        continue
                    if scroll_delta != 0:
                        if scroll_delta < 0:
                            code_scroll = max(0, code_scroll + scroll_delta)
                        else:
                            code_scroll += scroll_delta
                        continue
                    if last_demo_evt is not None:
                        demo.on_key(last_demo_evt)


if __name__ == "__main__":
    run_demo_hub()


def run_dashboard() -> None:
    demo = DashboardDemo()
    last = time.monotonic()
    last_draw = 0.0
    frame_budget = max(1, int(1000 / max(1, _FPS)))
    with Terminal() as term:
        _cursor_hide()
        try:
            while True:
                now = time.monotonic()
                dt = now - last
                last = now
                if _STATIC:
                    dt = 0.0
                # Handle input first for snappier response
                pre_evt = term.next_event(min(10, frame_budget))
                quit_flag = False
                if pre_evt and pre_evt.get("kind") == "key":
                    def handle(e):
                        nonlocal quit_flag
                        ch = int(e.get("ch", 0))
                        if ch and chr(ch).lower() == 'q':
                            quit_flag = True
                        else:
                            demo.on_key(e)
                    handle(pre_evt)
                    # Drain any repeats without waiting
                    while True:
                        e = term.next_event(0)
                        if not e:
                            break
                        if e.get("kind") != "key":
                            continue
                        handle(e)
                if quit_flag:
                    break
                demo.tick(dt)
                w, h = term.size()
                # Coalesce draws in static mode to minimize flashing when idle
                if _STATIC and (now - last_draw) < 0.05 and not pre_evt:
                    continue
                # Prefer batched frame if available
                cmds = demo.render_cmds((0, 0, w, h))
                if cmds:
                    _sync_start(); term.draw_frame(cmds); _sync_end()
                else:
                    _sync_start(); demo.render(term, (0, 0, w, h)); _sync_end()
                last_draw = now
                # Idle pacing only if we didn't process input this loop
                if _REC and not pre_evt:
                    now3 = time.monotonic()
                    sleep_ms = frame_budget - int((now3 - now) * 1000)
                    if sleep_ms > 0:
                        time.sleep(sleep_ms / 1000.0)
        finally:
            _cursor_show()

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


class FireDemo(DemoBase):
    name = "Fire"
    desc = "Classic fire effect"
    source_obj = None

    def __init__(self) -> None:
        self.w = 0
        self.h = 0
        self.buf: list[int] = []  # intensity per cell 0..255
        self.grad = " .:-=+*#%@"  # 10 chars
        self.cool = 0.02

    def _ensure(self, w: int, h: int) -> None:
        if w != self.w or h != self.h or not self.buf:
            self.w, self.h = w, h
            self.buf = [0] * (w * h)

    def tick(self, dt: float) -> None:
        # nothing persistent; we update per frame in render_cmds
        pass

    def render_cmds(self, rect: Tuple[int,int,int,int]) -> list:
        from . import Paragraph, DrawCmd
        x, y, w, h = rect
        if w <= 0 or h <= 0:
            return []
        self._ensure(w, h)
        import random
        # Seed bottom row with noisy high values
        base = 200
        row = (h-1)*w
        for i in range(w):
            self.buf[row + i] = max(0, min(255, base + random.randint(-40, 40)))

        # Diffuse upward using a randomized lateral source and cooling
        nextbuf = self.buf[:]
        for j in range(h-1):  # 0..h-2 write next row j from sources at j+1
            srcy = j+1
            for i in range(w):
                srcx = (i + random.randint(-1, 1)) % w
                s = 0
                # sample three cells below (left, center, right)
                s += self.buf[srcy*w + ((srcx-1) % w)]
                s += self.buf[srcy*w + srcx]
                s += self.buf[srcy*w + ((srcx+1) % w)]
                s += self.buf[min(h-1, srcy+1)*w + srcx]
                v = (s // 4) - random.randint(0, 12)
                if v < 0: v = 0
                nextbuf[j*w + i] = v
        self.buf = nextbuf
        # map to chars
        gmax = len(self.grad) - 1
        lines = []
        for j in range(h):
            row = []
            for i in range(w):
                v = self.buf[j*w + i]
                idx = (v * gmax) // 255
                row.append(self.grad[idx])
            lines.append(''.join(row))
        p = Paragraph.from_text('\n'.join(lines))
        p.set_block_title("Fire (classic) — q quit", True)
        return [DrawCmd.paragraph(p, rect)]


class TunnelDemo(DemoBase):
    name = "Tunnel"
    desc = "Ray-tunnel illusion"
    source_obj = None

    def __init__(self) -> None:
        self.t = 0.0
        self.speed = 1.0
        self.grad = " .:-=+*#%@"

    def on_key(self, evt: dict) -> None:
        if evt.get("kind") != "key":
            return
        ch = evt.get("ch", 0)
        if not ch:
            return
        c = chr(ch).lower()
        if c == '+': self.speed = min(5.0, self.speed*1.25)
        elif c == '-': self.speed = max(0.2, self.speed*0.8)

    def tick(self, dt: float) -> None:
        self.t += dt * self.speed

    def render_cmds(self, rect: Tuple[int,int,int,int]) -> list:
        from . import Paragraph, DrawCmd
        x, y, w, h = rect
        if w <= 0 or h <= 0:
            return []
        cx = (w-1)/2
        cy = (h-1)/2
        g = self.grad
        gm = len(g)-1
        import math
        lines = []
        for j in range(h):
            row = []
            for i in range(w):
                dx = (i - cx) / max(1, w*0.5)
                dy = (j - cy) / max(1, h*0.5)
                r = math.sqrt(dx*dx + dy*dy)
                a = math.atan2(dy, dx)
                # texture coords with time-based motion
                u = 1.0/(r+0.0001) + self.t*0.5
                v = a / (2*math.pi) + self.t*0.2
                # cheap checker texture
                c = (int(u*10) ^ int((v)*20)) & 3
                idx = min(gm, c * (gm//3))
                row.append(g[idx])
            lines.append(''.join(row))
        p = Paragraph.from_text('\n'.join(lines))
        p.set_block_title("Tunnel (+/- speed) — q quit", True)
        return [DrawCmd.paragraph(p, rect)]


class CubeDemo(DemoBase):
    name = "Cube"
    desc = "Spinning wireframe cube"
    source_obj = None

    def __init__(self) -> None:
        self.t = 0.0
        self.speed = 1.0

    def on_key(self, evt: dict) -> None:
        if evt.get("kind") != "key": return
        ch = evt.get("ch", 0)
        if not ch: return
        c = chr(ch).lower()
        if c == '+': self.speed = min(5.0, self.speed*1.25)
        elif c == '-': self.speed = max(0.2, self.speed*0.8)

    def tick(self, dt: float) -> None:
        self.t += dt * self.speed

    def render_cmds(self, rect: Tuple[int,int,int,int]) -> list:
        from . import Paragraph, DrawCmd
        x, y, w, h = rect
        if w <= 0 or h <= 0:
            return []
        import math
        # simple orthographic projection with rotation
        # cube vertices
        verts = [
            (-1,-1,-1),(1,-1,-1),(1,1,-1),(-1,1,-1),
            (-1,-1, 1),(1,-1, 1),(1,1, 1),(-1,1, 1),
        ]
        edges = [(0,1),(1,2),(2,3),(3,0),(4,5),(5,6),(6,7),(7,4),(0,4),(1,5),(2,6),(3,7)]
        a = self.t*0.9; b = self.t*0.6
        sa, ca = math.sin(a), math.cos(a)
        sb, cb = math.sin(b), math.cos(b)
        rot = []
        for x0,y0,z0 in verts:
            # rotate around Y then X
            x1 = x0*cb + z0*sb
            z1 = -x0*sb + z0*cb
            y1 = y0*ca - z1*sa
            z2 = y0*sa + z1*ca
            rot.append((x1,y1,z2))
        # project
        sx, sy = w*0.5, h*0.5
        scale = min(w,h)*0.22
        pts = []
        for x1,y1,z1 in rot:
            pts.append((int(sx + x1*scale), int(sy + y1*scale)))
        # rasterize to buffer
        buf = [[' ']*w for _ in range(h)]
        def plot(px,py):
            if 0<=px<w and 0<=py<h: buf[py][px] = '#'
        def line(x0,y0,x1,y1):
            dx = abs(x1-x0); dy = -abs(y1-y0)
            sx = 1 if x0<x1 else -1; sy = 1 if y0<y1 else -1
            err = dx+dy
            while True:
                plot(x0,y0)
                if x0==x1 and y0==y1: break
                e2 = 2*err
                if e2>=dy: err+=dy; x0+=sx
                if e2<=dx: err+=dx; y0+=sy
        for a,b in edges:
            x0,y0 = pts[a]; x1,y1 = pts[b]
            line(x0,y0,x1,y1)
        lines = [''.join(r) for r in buf]
        p = Paragraph.from_text('\n'.join(lines))
        p.set_block_title("Wireframe Cube (+/- speed)", True)
        return [DrawCmd.paragraph(p, rect)]


class WidgetSceneDemo(DemoBase):
    name = "WidgetScene"
    desc = "Demoscene made of widgets"
    source_obj = None

    def __init__(self) -> None:
        self.t = 0.0
        self.speed = 1.0
        self.sel = 0

    def on_key(self, evt: dict) -> None:
        if evt.get("kind") != "key": return
        ch = evt.get("ch", 0)
        if not ch: return
        c = chr(ch).lower()
        if c == '+': self.speed = min(5.0, self.speed*1.25)
        elif c == '-': self.speed = max(0.2, self.speed*0.8)

    def tick(self, dt: float) -> None:
        self.t += dt * self.speed
        self.sel = int(self.t*2) % 4

    def render_cmds(self, rect: Tuple[int,int,int,int]) -> list:
        from . import Tabs, BarChart, Sparkline, Gauge, List, Paragraph, DrawCmd, Style, FFI_COLOR
        out = []
        x, y, w, h = rect
        if w < 20 or h < 8:
            p = Paragraph.from_text("WidgetScene needs more space")
            p.set_block_title("WidgetScene", True)
            return [DrawCmd.paragraph(p, rect)]
        top, rest = split_h(rect, 3.0, 7.0, gap=1)
        mid, bottom = split_h(rest, 6.0, 4.0, gap=1)
        left, right = split_v(mid, 0.5, 0.5, gap=1)

        # Top tabs pulsate selection
        tabs = Tabs()
        tabs.set_titles(["Ratatui", "Widgets", "Demoscene", "Py"])
        tabs.set_selected(self.sel)
        tabs.set_block_title("WidgetScene (+/- speed)", True)
        out.append(DrawCmd.tabs(tabs, top))

        # Left: BarChart as rising/falling equalizer
        import math
        n = max(8, min(32, left[2]//2))
        vals = []
        for i in range(n):
            v = 30 + 20*math.sin(self.t*2 + i*0.5) + 10*math.sin(self.t*3 + i*0.9)
            vals.append(max(0, int(v)))
        bc = BarChart()
        bc.set_values(vals)
        bc.set_labels([""]*len(vals))
        bc.set_block_title("Equalizer", True)
        out.append(DrawCmd.barchart(bc, left))

        # Right: Sparkline snake (Lissajous-like)
        sp = Sparkline()
        snake = []
        for i in range(max(10, right[2]-2)):
            snake.append(int(10 + 9*math.sin(self.t*4 + i*0.3)))
        sp.set_values(snake)
        sp.set_block_title("Snake", True)
        out.append(DrawCmd.sparkline(sp, right))

        # Bottom: dual gauges + scrolling list
        g_left, g_right = split_v(bottom, 0.5, 0.5, gap=1)
        g1 = Gauge().ratio(0.5 + 0.49*math.sin(self.t*1.7)).label("Pulse")
        g1.set_block_title("Pulse", True)
        out.append(DrawCmd.gauge(g1, g_left))
        g2 = Gauge().ratio(0.5 + 0.49*math.sin(self.t*2.3 + 1.2)).label("Wave")
        g2.set_block_title("Wave", True)
        out.append(DrawCmd.gauge(g2, g_right))

        return out


class CACubeDemo(DemoBase):
    name = "CA Cube"
    desc = "3D shell cellular automaton (only the cube surface)"
    source_obj = None

    def __init__(self) -> None:
        # Conceptually 128^3; simulate 16^3 for speed (no numpy)
        self.n = 16
        self.field = [0.0] * (self.n*self.n*self.n)
        self.nextf = [0.0] * (self.n*self.n*self.n)
        self.t = 0.0
        self.speed = 1.0
        # Precompute radial distance from kernel (center)
        import math
        c = (self.n-1)/2
        self.rad = []
        maxr = math.sqrt(3)*c
        for z in range(self.n):
            for y in range(self.n):
                for x in range(self.n):
                    r = math.sqrt((x-c)**2 + (y-c)**2 + (z-c)**2)/maxr
                    self.rad.append(r)
        self.threshold = 0.30

    def idx(self, x,y,z):
        return (z*self.n + y)*self.n + x

    def on_key(self, evt: dict) -> None:
        if evt.get("kind") != "key": return
        code = evt.get("code", 0)
        ch = evt.get("ch", 0)
        if ch:
            c = chr(ch).lower()
            if c == '+': self.speed = min(5.0, self.speed*1.25)
            elif c == '-': self.speed = max(0.2, self.speed*0.8)
            elif c == 'i': self.threshold = min(0.9, self.threshold+0.02)
            elif c == 'k': self.threshold = max(0.1, self.threshold-0.02)
            elif c == 'r': self.field = [0.0]*len(self.field)

    def tick(self, dt: float) -> None:
        # Evolve CA (26-neighborhood) a few microsteps per frame
        import math
        self.t += dt * self.speed
        n = self.n
        steps = 2
        for _ in range(steps):
            # inject near kernel
            c = n//2
            pulse = 0.65 + 0.35*math.sin(self.t*2.0)
            for z in range(max(0,c-1), min(n,c+2)):
                for y in range(max(0,c-1), min(n,c+2)):
                    for x in range(max(0,c-1), min(n,c+2)):
                        i = self.idx(x,y,z)
                        self.field[i] = min(1.0, self.field[i]*0.7 + pulse*0.3)
            # update from neighbors
            for z in range(n):
                for y in range(n):
                    for x in range(n):
                        i = self.idx(x,y,z)
                        v = self.field[i]
                        r = self.rad[i]
                        # decay increases with radius
                        decay = 0.015 + 0.25*(r*r)
                        s = 0.0; cnb = 0
                        for dz in (-1,0,1):
                            zz = z+dz
                            if 0<=zz<n:
                                for dy in (-1,0,1):
                                    yy = y+dy
                                    if 0<=yy<n:
                                        for dx in (-1,0,1):
                                            xx = x+dx
                                            if 0<=xx<n and not (dx==0 and dy==0 and dz==0):
                                                s += self.field[self.idx(xx,yy,zz)]; cnb += 1
                        nb = s/max(1,cnb)
                        grow = max(0.0, nb - 0.30) * (0.6 - 0.3*r)  # weaker further out
                        nv = v*(1.0-decay) + grow
                        self.nextf[i] = max(0.0, min(1.0, nv))
            self.field, self.nextf = self.nextf, self.field

    def render_cmds(self, rect: Tuple[int,int,int,int]) -> list:
        from . import Paragraph, DrawCmd
        x, y, w, h = rect
        if w<=0 or h<=0: return []
        import math
        # Projection setup like CubeDemo
        sx, sy = w*0.5, h*0.5
        scale = min(w,h)*0.22
        a = self.t*0.7; b = self.t*0.4
        sa, ca = math.sin(a), math.cos(a)
        sb, cb = math.sin(b), math.cos(b)
        # Buffer init
        buf = [[' ']*w for _ in range(h)]
        # Draw wireframe cube
        verts = [(-1,-1,-1),(1,-1,-1),(1,1,-1),(-1,1,-1),(-1,-1,1),(1,-1,1),(1,1,1),(-1,1,1)]
        edges = [(0,1),(1,2),(2,3),(3,0),(4,5),(5,6),(6,7),(7,4),(0,4),(1,5),(2,6),(3,7)]
        pts = []
        for x0,y0,z0 in verts:
            x1 = x0*cb + z0*sb
            z1 = -x0*sb + z0*cb
            y1 = y0*ca - z1*sa
            pts.append((int(sx + x1*scale), int(sy + y1*scale)))
        def plot(px,py,ch='#'):
            if 0<=px<w and 0<=py<h: buf[py][px] = ch
        def line(x0,y0,x1,y1):
            dx = abs(x1-x0); dy = -abs(y1-y0)
            sx1 = 1 if x0<x1 else -1; sy1 = 1 if y0<y1 else -1
            err = dx+dy
            while True:
                plot(x0,y0)
                if x0==x1 and y0==y1: break
                e2 = 2*err
                if e2>=dy: err+=dy; x0+=sx1
                if e2<=dx: err+=dx; y0+=sy1
        for a,b in edges:
            x0,y0 = pts[a]; x1,y1 = pts[b]
            line(x0,y0,x1,y1)
        # Plot active voxels above threshold only on the outer shell of the cube
        n = self.n; c = (n-1)/2
        stride = 1  # full sampling at 16^3
        shell_positions = []
        for z in range(0,n,stride):
            for y0 in range(0,n,stride):
                for x0 in range(0,n,stride):
                    if not (x0==0 or x0==n-1 or y0==0 or y0==n-1 or z==0 or z==n-1):
                        continue
                    v = self.field[self.idx(x0,y0,z)]
                    if v <= self.threshold:
                        continue
                    # store normalized coords and intensity once; render at multiple scales
                    X = (x0 - c)/c
                    Y = (y0 - c)/c
                    Z = (z  - c)/c
                    shell_positions.append((X,Y,Z,v))
        # render multiple concentric cubes (scaled down)
        layers = [1.0, 0.8, 0.6, 0.45]
        for li, s in enumerate(layers):
            for X,Y,Z,v in shell_positions:
                X1 = (X*cb + Z*sb) * s
                Z1 = (-X*sb + Z*cb)
                Y1 = (Y*ca - Z1*sa) * s
                px = int(sx + X1*scale)
                py = int(sy + Y1*scale)
                # slightly easier threshold for inner layers for visibility
                ch = '#' if v>0.7 else ('*' if v>0.5 else ('+' if v>0.35 else '.'))
                plot(px,py,ch)
        lines = [''.join(r) for r in buf]
        from . import Paragraph
        p = Paragraph.from_text('\n'.join(lines))
        p.set_block_title(f"CA Cube (+/- speed, i/k thresh={self.threshold:.2f})", True)
        return [DrawCmd.paragraph(p, rect)]
