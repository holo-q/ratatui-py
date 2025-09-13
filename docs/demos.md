# Demos

Preview: see the README’s Recording section for how to capture a GIF/MP4. Once you have
`docs/assets/dashboard.gif`, it will be rendered here automatically. Until then, no
preview image is displayed to keep strict builds happy.

The package installs several demo entrypoints. Run them from your shell:

```bash
ratatui-demos
# or run specific ones
ratatui-hello
ratatui-widgets
ratatui-life
ratatui-dashboard
```

Legacy aliases `ratatui-py-*` are kept for compatibility.

If you see errors about missing libraries, set `RATATUI_FFI_LIB` to a prebuilt
shared library, or install Rust toolchain and let bundling build from source.

Dashboard demo controls:
- a/d: switch tabs
- j/k: move selection
- r: spike values
- q: quit

Recording instructions: see [recording.md](recording.md).
