# ratatui-py — Python bindings for Ratatui (Rust TUI)

[![PyPI](https://img.shields.io/pypi/v/ratatui-py.svg)](https://pypi.org/project/ratatui-py/)
![Python Versions](https://img.shields.io/pypi/pyversions/ratatui-py.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)
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

## Install

By default, install tries to bundle the Rust shared library automatically:

Order of strategies (first that works is used):
- Use a prebuilt library if `RATATUI_FFI_LIB` is set.
- Build from a local source if `RATATUI_FFI_SRC` is set (runs `cargo build --release`).
- Clone and build `holo-q/ratatui-ffi` at `RATATUI_FFI_TAG` if network and toolchain are available.

The resulting shared library is packaged at `ratatui_py/_bundled/` and loaded automatically at runtime.

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

## CLI demos

After installation you can explore interactive demos:

```
ratatui-py-demos
```

Or run specific examples:

```
ratatui-py-hello
ratatui-py-widgets
ratatui-py-life
ratatui-py-dashboard
```

## Environment variables
- `RATATUI_FFI_LIB`: absolute path to a prebuilt shared library to bundle/load.
- `RATATUI_FFI_SRC`: path to local ratatui-ffi source to build with cargo.
- `RATATUI_FFI_GIT`: override git URL (default `https://github.com/holo-q/ratatui-ffi.git`).
- `RATATUI_FFI_TAG`: git tag/commit to fetch for bundling (default `v0.1.5`).

## Platform support
- Linux: `x86_64` is tested; other targets may work with a compatible `ratatui_ffi` build.
- macOS: Apple Silicon and Intel are supported via `dylib`.
- Windows: supported via `ratatui_ffi.dll`.

## Troubleshooting
- Build toolchain not found: set `RATATUI_FFI_LIB` to a prebuilt shared library or install Rust (`cargo`) and retry.
- Wrong library picked up: ensure `RATATUI_FFI_LIB` points to a library matching your OS/arch.
- Import errors on fresh install: reinstall in a clean venv to ensure the bundled library is present.

## Why ratatui-py?
- Bring Ratatui’s modern TUI widgets and layout engine to Python.
- Avoid ncurses boilerplate; focus on your UI and event loop.
- Keep Python for app logic while leveraging Rust for rendering.

## Links
- PyPI: https://pypi.org/project/ratatui-py/
- Source: https://github.com/holo-q/ratatui-py
- Ratatui (Rust): https://github.com/ratatui-org/ratatui
- ratatui_ffi: https://github.com/holo-q/ratatui-ffi

## License
MIT — see [LICENSE](./LICENSE).

[ratatui_ffi]: https://github.com/holo-q/ratatui-ffi
[Ratatui]: https://github.com/ratatui-org/ratatui
[!NOTE]
Demo preview placeholder: replace `docs/assets/dashboard.gif` with your recording.

![Dashboard demo](docs/assets/dashboard.gif)

See recording guide: docs/recording.md
