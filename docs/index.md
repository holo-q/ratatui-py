# ratatui-py

Fast Python bindings for [Ratatui], the modern Rust TUI library. Build rich terminal UIs with Python while leveraging Ratatui’s performance and widgets.

- Zero-build install when a prebuilt shared library is available
- Cross-platform: Linux, macOS, Windows
- Idiomatic Python wrappers: Terminal, Paragraph, List, Table, Gauge, Tabs, BarChart, Sparkline, Scrollbar, Chart

Get started in minutes:

```python
from ratatui_py import Terminal, Paragraph

with Terminal() as term:
    p = Paragraph.from_text("Hello from Python!\nThis is ratatui.")
    p.set_block_title("Demo", True)
    term.draw_paragraph(p)
    term.next_event(3000)
```

[Quickstart](quickstart.md) • [Demos](demos.md) • [API](api.md)

[Ratatui]: https://github.com/ratatui-org/ratatui
