# Contributing to ratatui-py

Thanks for helping make ratatui-py great!

- Dev setup
  - Python 3.9+
  - Clone and create a virtualenv
  - `pip install -e .` to install with the bundled shared library
  - `pip install -r requirements-dev.txt` or just `pip install ruff mypy pytest`
- Lint/type/test
  - `ruff check .`
  - `mypy src`
  - `pytest -q`
- Docs
  - `pip install mkdocs mkdocs-material`
  - `mkdocs serve` to preview

If bundling fails during editable install, set `RATATUI_FFI_LIB` to a prebuilt
shared library that matches your OS/arch, or set `RATATUI_FFI_SRC` to a local
`ratatui-ffi` checkout with a Rust toolchain installed.

