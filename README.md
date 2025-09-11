# ratatui-py — Python bindings for Ratatui (Rust TUI)

[![PyPI](https://img.shields.io/pypi/v/ratatui-py.svg)](https://pypi.org/project/ratatui-py/)
[![Docs](https://github.com/holo-q/ratatui-py/actions/workflows/docs.yml/badge.svg)](https://github.com/holo-q/ratatui-py/actions/workflows/docs.yml)
[![CI](https://github.com/holo-q/ratatui-py/actions/workflows/ci.yml/badge.svg)](https://github.com/holo-q/ratatui-py/actions/workflows/ci.yml)

Fast, zero-build Python bindings for [ratatui_ffi], the C ABI for
[Ratatui] — a modern Rust library for building rich terminal user
interfaces (TUIs). Use Ratatui’s performant rendering and widget set
from Python via `ctypes`, with prebuilt shared libraries bundled for
Linux, macOS, and Windows.

Key features:
- Zero-build install: bundles a prebuilt shared library when available
  and falls back to building from source when configured.
- Cross‑platform: loads `libratatui_ffi.so` (Linux), `libratatui_ffi.dylib` (macOS), or `ratatui_ffi.dll` (Windows).
- Idiomatic Python wrappers: start quickly with `Terminal`, `Paragraph`, `List`, `Table`, `Gauge`, and more.
- Minimal overhead: direct FFI calls using `ctypes`.
 - Layout helpers: `margin`, `split_h`, `split_v` for quick UI splits.

## Installation

Use uv for a fast, reproducible install:

```
uv add ratatui-py
```

Try the interactive demos without installing into your environment:

```
uvx --from ratatui-py ratatui-py-demos
# or a specific one
uvx --from ratatui-py ratatui-py-dashboard
```

## Quick start

```python
from ratatui_py import Terminal, Paragraph

with Terminal() as term:
    p = Paragraph.from_text("Hello from Python!\nThis is ratatui.\n\nPress any key to exit.")
    p.set_block_title("Demo", show_border=True)
    term.draw_paragraph(p)
    term.next_event(5000)  # wait for key or 5s
```

### Run loop helper

Prefer a simple app pattern? Use `App`:

```python
from ratatui_py import App, Terminal, Paragraph

def render(term: Terminal, state: dict) -> None:
    w, h = term.size()
    p = Paragraph.from_text("Hello ratatui-py!\nPress q to quit.")
    p.set_block_title("Demo", True)
    term.draw_paragraph(p, (0, 0, w, h))

def on_event(term: Terminal, evt: dict, state: dict) -> bool:
    return not (evt.get("kind") == "key" and evt.get("ch") in (ord('q'), ord('Q')))

App(render=render, on_event=on_event, tick_ms=250).run({})
```

### One‑liner session and spans

Snappy, minimal setup for a full session (raw + alt screen), plus per‑span styling:

```python
from ratatui_py import terminal_session, Paragraph, Style, rgb

with terminal_session(raw=True, alt=True, clear=True) as term:
    spans = [("Hello ", Style()), ("world", Style(fg=rgb(0,180,255)).bold())]
    p = Paragraph.new_empty().append_lines_spans([spans])
    term.draw_paragraph(p, (0,0,*term.size()))
    term.next_event(1000)
```

## Widgets demo (List + Table + Gauge)

```python
from ratatui_py import Terminal, List, Table, Gauge, Style, FFI_COLOR

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

    term.draw_list(lst, (0,0,20,6))
    term.draw_table(tbl, (0,6,20,6))
    term.draw_gauge(g, (0,12,20,3))
```

## Demos (via uvx, no install)

The easiest way to try things out is with `uvx` — it downloads and runs the
demo entry points in an isolated, ephemeral environment:

```

### Canvas + Logo (extras)

Draw shapes with `Canvas`, and optionally render the Ratatui logo for fun:

```python
from ratatui_py import Terminal, Canvas, Style, rgb

with Terminal() as term:
    w, h = term.size()
    cv = Canvas(0.0, 100.0, 0.0, 100.0)
    cv.add_rect(10,10,80,60, Style(fg=rgb(0,255,255)))
    cv.add_line(10,10,90,70, Style(fg=rgb(255,128,0)))
    term.draw_canvas(cv, (0,0,w,h))
    if h >= 12:
        term.draw_logo((0, h-12, w, 12))
```
uvx --from ratatui-py ratatui-py-demos
uvx --from ratatui-py ratatui-py-dashboard
uvx --from ratatui-py ratatui-py-hello
```

If you’ve already installed the package, the same commands are available on
your PATH (e.g., `ratatui-py-demos`).


## Environment variables
- `RATATUI_FFI_LIB`: absolute path to a prebuilt shared library to bundle/load.
- `RATATUI_FFI_SRC`: path to local ratatui-ffi source to build with cargo.
- `RATATUI_FFI_GIT`: override git URL (default `https://github.com/holo-q/ratatui-ffi.git`).
- `RATATUI_FFI_TAG`: git tag/commit to fetch for bundling (default `v0.2.0`).

### Advanced installation and bundling

If you need precise control over the bundled Rust library, you can direct how
the shared library is sourced. On install, the package tries strategies in the
following order until one succeeds:

1) Use a prebuilt artifact when `RATATUI_FFI_LIB` points to a `.so/.dylib/.dll`.
2) Build from local sources when `RATATUI_FFI_SRC` is set (runs `cargo build`).
3) Clone and build `holo-q/ratatui-ffi` at `RATATUI_FFI_TAG`.

The chosen library is copied into `ratatui_py/_bundled/` and auto‑loaded at
runtime. Most users do not need this; it’s provided for reproducible builds
and development workflows.

### Demo/recording behavior toggles
- `RATATUI_PY_RECORDING=1`: optimize demo runner for recording. Enables inline mode, synchronized updates, and frame coalescing.
- `RATATUI_PY_FPS=NN`: target redraw rate in FPS (default 30). Use higher (e.g., 60) for snappier feel while recording.
- `RATATUI_PY_STATIC=1`: freeze animations for perfectly stable captures; input still works.
- `RATATUI_PY_NO_CODE=1`: hide the right‑hand code pane in the demo hub to reduce churn and draw only the live demo.
- `RATATUI_PY_SYNC=1`: force synchronized update bracketing even outside recording (usually not needed).
- `RATATUI_FFI_NO_ALTSCR=1`: render inline (no alternate screen) so scrollback is preserved. The demo runner enables this by default.

## Utilities for responsive apps

The `ratatui_py.util` module provides helpers to keep your UI snappy under load:

- `frame_begin(budget_ms=12)`: start a frame time budget. In heavy loops, periodically check `fb.should_yield()` and return to the event loop to avoid input backlog.

- `BackgroundTask(fn, loop=False)`: run work in a thread. Use when your workload releases the GIL (e.g., FFI/Rust, NumPy, I/O). Call `task.start()`, do `task.peek()` each frame to get the latest result, and `task.stop()` on shutdown.

- `ProcessTask(fn, loop=False, start_method='spawn')`: run CPU-bound work in a separate process (bypasses the GIL). The worker receives a context with:
  - `ctx.recv_latest(timeout=0)`: read the most recent submitted job (drops stale ones).
  - `ctx.publish(result)`: send back a result (older ones are dropped).
  - `ctx.should_stop()`: check for cooperative shutdown.

Example (looping worker):

```python
from ratatui_py import ProcessTask

def worker(ctx):
    params = None
    while not ctx.should_stop():
        msg = ctx.recv_latest(timeout=0.01)
        if msg is not None:
            params = msg
        if params is None:
            continue
        result = do_heavy_compute(params)  # pure CPU ok here
        ctx.publish(result)

task = ProcessTask(worker, loop=True)
task.start()
task.submit({"zoom": 1.25})
# In your render loop: latest = task.peek()
# On shutdown: task.stop(join=True, terminate=True)
```

Tip: Prefer `BackgroundTask` when your computation releases the GIL; prefer `ProcessTask` for pure-Python CPU work where threading won’t help.

## Typed API (developer ergonomics)

Use the typed helpers for clear, discoverable code and great editor support:

- Rect/Point/Size dataclasses and `RectLike` union — pass either a `Rect` or a tuple to draw calls; layout helpers also offer typed variants:

```python
from ratatui_py import Rect, margin_rect, split_v_rect

area = Rect(0, 0, 80, 24)
body = margin_rect(area, all=1)
left, right = split_v_rect(body, 0.4, 0.6, gap=1)
```

- Color enum with `Style`: write `Style(fg=Color.LightBlue)` instead of raw integers.
  Fluent helpers for emphasis: `Style().bold().underlined()` (uses `Mod` flags).

- Typed events: prefer `next_event_typed()` for dataclass events with enums:

```python
from ratatui_py import Terminal, KeyCode

with Terminal() as term:
    evt = term.next_event_typed(100)
    if evt and evt.kind == 'key' and evt.code == KeyCode.Left:
        ...  # move selection
```

- Batched frames via a context manager:

```python
from ratatui_py import Terminal, Paragraph, Rect

with Terminal() as term:
    p1 = Paragraph.from_text("Left")
    p2 = Paragraph.from_text("Right")
    with term.frame() as f:
        f.paragraph(p1, Rect(0, 0, 20, 3))
        f.paragraph(p2, Rect(20, 0, 20, 3))
    # f.ok is True/False depending on `draw_frame`
```

- Key binding helper:

```python
from ratatui_py import Terminal, Keymap, KeyCode, KeyMods

km = Keymap()
km.bind(KeyCode.Left, KeyMods.NONE, lambda e: print('←'))

with Terminal() as term:
    evt = term.next_event_typed(100)
    if evt:
        km.handle(evt)
```

- Convenience prelude:

```python
from ratatui_py.prelude import *  # Terminal, Paragraph, Rect, Color, etc.
```

## Platform support
- Linux: `x86_64` is tested; other targets may work with a compatible `ratatui_ffi` build.
- macOS: Apple Silicon and Intel are supported via `dylib`.
- Windows: supported via `ratatui_ffi.dll`.

## Recording (flicker‑free, with scrollback)

The demos are tuned for clean screencasts:

- Inline viewport by default (no alternate screen) so your terminal scrollback remains intact.
- Whole‑frame synchronized updates to avoid partial‑frame flicker in recorders.
- Event‑driven redraw with key‑repeat draining for responsive navigation.

Quick start with asciinema (no shell prompt in the cast):

```
# Record the dashboard only (80x24), smooth and flicker‑free
asciinema rec -q --cols 80 --rows 24 --idle-time-limit 2 \
  -c 'RATATUI_PY_RECORDING=1 RATATUI_PY_FPS=60 uv run ratatui-py-dashboard' \
  docs/assets/dashboard.cast --overwrite

# Or record the demo hub (hide code pane for minimal churn)
asciinema rec -q --cols 80 --rows 24 --idle-time-limit 2 \
  -c 'RATATUI_PY_RECORDING=1 RATATUI_PY_NO_CODE=1 RATATUI_PY_FPS=60 uv run ratatui-py-demos' \
  docs/assets/demos.cast --overwrite
```

Prefer a GIF for GitHub’s README preview? Convert the cast:

```
# Using asciinema-agg (install locally or use its container image)
asciinema-agg --fps 30 --idle 2 docs/assets/dashboard.cast docs/assets/dashboard.gif
```

Notes:
- To absolutely eliminate motion during capture, add `RATATUI_PY_STATIC=1`.
- If your terminal still shows artifacts, record inside tmux: `tmux new -As rec` then run the same command.
- GitHub READMEs cannot embed a `.cast` player; use a GIF/MP4 and link to the `.cast` in docs.

## Troubleshooting
- Build toolchain not found: set `RATATUI_FFI_LIB` to a prebuilt shared library or install Rust (`cargo`) and retry.
- Wrong library picked up: ensure `RATATUI_FFI_LIB` points to a library matching your OS/arch.
- Import errors on fresh install: reinstall in a clean venv to ensure the bundled library is present.

### Terminal behavior and “clashes” cheat‑sheet

Ratatui (via crossterm) uses raw mode and (optionally) the alternate screen. Some terminal environments or Python shells can interact with these features in surprising ways. This section lists common scenarios and how to address them.

- Scrollback appears “lost”
  - Alt screen replaces the visible buffer; your scrollback is preserved but hidden until exit.
  - Fix: leave alt screen off (default in this package) or exit the app. To force alt screen: set `RATATUI_FFI_ALTSCR=1`.

- Keystrokes echo on screen, or input feels “sticky”
  - Raw mode controls whether the terminal echoes input and how keys are delivered.
  - Fix: raw mode is on by default here; to disable (e.g. for logging), set `RATATUI_FFI_NO_RAW=1`.

- Integrated terminals (VS Code, JetBrains, Jupyter, ipython)
  - Some shells may buffer or handle ANSI differently; full‑screen TUIs might flicker.
  - Fix: run from a regular terminal (e.g., GNOME Terminal, iTerm2, Windows Terminal). For diagnostics, disable alt screen and enable logging (see below).

- tmux/screen quirks
  - Multiplexers change terminfo and may alter mouse/keypress behavior or scrollback.
  - Fix: prefer alt screen in tmux (`RATATUI_FFI_ALTSCR=1`). If scrollback is a priority, keep alt screen off and accept in‑place updates.

- WSL/ConPTY (Windows)
  - ConPTY handling can differ across versions; ensure you’re using Windows Terminal or a recent console host.
  - If you see rendering anomalies, try disabling alt screen first.

- CI/headless usage
  - TUIs require a TTY; instead, use headless render helpers like `headless_render_*` and `ratatui_headless_render_frame` to snapshot output for tests.

- Unicode/emoji rendering
  - Ensure your locale is UTF‑8 and your font supports the glyphs you render. Some terminals need explicit configuration.

### Stable diagnostics and backtraces

Turn on robust diagnostics only when needed:

```bash
# rich diagnostics without alt screen
RATATUI_PY_DEBUG=1 uv run ratatui-py-demos

# or enable flags individually
RUST_BACKTRACE=full \
RATATUI_FFI_TRACE=1 \
RATATUI_FFI_NO_ALTSCR=1 \
RATATUI_FFI_PROFILE=debug \
RATATUI_FFI_LOG=ratatui_ffi.log \
uv run ratatui-py-demos
```

What these do:
- `RUST_BACKTRACE=full`: line‑accurate Rust backtraces on panics.
- `RATATUI_FFI_TRACE=1`: prints ENTER/EXIT lines for FFI calls and panics.
- `RATATUI_FFI_NO_ALTSCR=1`: avoids alt screen so logs remain visible.
- `RATATUI_FFI_PROFILE=debug`: bundles the debug cdylib for accurate symbols.
- `RATATUI_FFI_LOG=…`: saves all FFI logs to a file (recreated per run). Set `RATATUI_FFI_LOG_APPEND=1` to append.

Advanced:
- Python faulthandler: `PYTHONFAULTHANDLER=1` to dump tracebacks on signals.
- gdb/lldb: `gdb --args python -m ratatui_py.demo_runner` → `run`, then `bt full` on crash.

### Known pitfalls we harden against

- Dangling handles in batched frames (use‑after‑free)
  - Cause: passing raw FFI pointers without keeping owners alive across `draw_frame`.
  - Mitigation: Python wrapper retains strong references to widget owners for the duration of the draw.

- Out‑of‑bounds rectangles
  - Cause: computing rects larger than the frame area.
  - Mitigation: FFI clamps rects to the current frame before rendering.

- Panics inside FFI draw
  - Cause: invalid inputs or internal errors.
  - Mitigation: All FFI draw/init/free are wrapped with `catch_unwind`, logging the panic and backtrace and returning `false` rather than aborting.

If you still hit rendering anomalies or crashes, please open an issue with:
- Your OS/terminal, whether under tmux/screen/WSL.
- The exact command and environment variables used.
- `ratatui_ffi.log` and the console backtrace (if any).
- A minimal script to reproduce.

## Why ratatui-py?

Build rich, fast TUIs in Python without giving up a modern rendering engine.

- Performance‑first core: rendering and layout are powered by a Rust engine, so
  complex scenes, charts, and animations stay smooth even at high FPS. Python
  drives app logic; Rust does the pixel pushing.
- Batteries included UI: tables, lists, gauges, charts, sparklines, blocks,
  borders, and a flexible layout system (constraints, margins, splits).
- Record‑ready output: synchronized updates, inline mode (no alt‑screen), and
  frame coalescing produce clean casts in asciinema and similar tools.
- Practical ergonomics: a small, idiomatic wrapper (`Terminal`, widgets, and
  `DrawCmd`) and layout helpers (`split_h`, `split_v`, `margin`).
- Testability: headless render helpers generate text snapshots for fast,
  deterministic tests in CI without a TTY.

How this differs from common pure‑Python TUI stacks (respectfully, no names):

- Rendering model
  - ratatui‑py: double‑buffered composition with batched draws; minimizes
    cursor movement and reduces flicker/tearing.
  - Pure‑Python stacks often stream writes and cursor moves directly; simple
    UIs are fine, but complex scenes can require extra care to stay flicker‑free.

- Throughput and headroom
  - ratatui‑py: high throughput under load (widgets + charts at 30–60 FPS) by
    offloading rendering to Rust.
  - Pure‑Python: perfectly adequate for text‑heavy apps; very dense scenes or
    heavy per‑frame styling can stutter without extra optimization.

- Widgets and visuals
  - ratatui‑py: ships with performance‑oriented widgets (charts/sparklines,
    gauges, tables) and consistent borders/colors across terminals.
  - Pure‑Python: highly hackable, often favoring line‑editing/REPL workflows;
    advanced visuals may need custom drawing code.

- Packaging trade‑offs
  - ratatui‑py: uses a small shared library (bundled wheels or build‑from‑source
    paths provided). In exchange, you get Rust‑level rendering speed.
  - Pure‑Python: zero external binary; simplest to vendor or embed.

When to pick which (rules of thumb)
- Choose ratatui‑py if you want smooth charts/dashboards, dense widgets,
  flicker‑free recording, or you expect to push the terminal hard.
- Choose a Python‑only stack when you want a tiny dependency footprint, focus
  on line editing/REPL flows, or prefer fully dynamic patch‑and‑reload cycles.

## Links
- PyPI: https://pypi.org/project/ratatui-py/
- Source: https://github.com/holo-q/ratatui-py
- Ratatui (Rust): https://github.com/ratatui-org/ratatui
- ratatui_ffi: https://github.com/holo-q/ratatui-ffi

## License
MIT — see [LICENSE](./LICENSE).

[ratatui_ffi]: https://github.com/holo-q/ratatui-ffi
[Ratatui]: https://github.com/ratatui-org/ratatui
Demo preview

![Dashboard demo](docs/assets/dashboard.gif)

[View asciinema cast](docs/assets/dashboard.cast)
