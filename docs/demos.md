# Demos

Preview (placeholder):

![Dashboard demo](assets/dashboard.gif)

The package installs several demo entrypoints. Run them from your shell:

```bash
ratatui-py-demos
# or run specific ones
ratatui-py-hello
ratatui-py-widgets
ratatui-py-life
ratatui-py-dashboard
```

If you see errors about missing libraries, set `RATATUI_FFI_LIB` to a prebuilt
shared library, or install Rust toolchain and let bundling build from source.

Dashboard demo controls:
- a/d: switch tabs
- j/k: move selection
- r: spike values
- q: quit

Recording instructions: see [recording.md](recording.md).
