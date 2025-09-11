# Changelog

All notable changes to this project are documented here.

## 0.4.0
- Update bundled ratatui_ffi to v0.2.0
- 100% Python→FFI symbol coverage (guarded by feature detection)
- Pythonic wrappers without overhead:
  - Terminal: raw/alt/cursor/viewport controls, draw_clear, event injection
  - Paragraph/List/Table/Gauge/Tabs/BarChart/Sparkline/Chart/Canvas/Logo: expanded setters and draw helpers
  - Batch spans APIs across widgets for high‑throughput text styling
  - ListState/TableState with draw + headless render
  - Headless frame helpers: text, styles_ex, cells
  - FFI‑driven layout splits with ratio constraints (layout_split_ffi)
  - Context helpers: raw_mode(), alt_screen(), terminal_session()
- Examples and tests: Canvas + Logo example; headless canvas/logo tests

## 0.3.x
- Python bindings for Ratatui via `ctypes`
- Bundled shared library strategy and environment variable overrides
- Initial widgets: Terminal, Paragraph, List, Table, Gauge, Tabs, BarChart, Sparkline, Scrollbar, Chart
- CLI demos: `ratatui-py-demos`, `ratatui-py-hello`, `ratatui-py-widgets`, `ratatui-py-life`
