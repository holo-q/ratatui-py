# Recording the Dashboard Demo

This shows how to record the `ratatui-py-dashboard` demo and generate an embeddable GIF/SVG for the README and docs.

## Option A: Asciinema + GIF (Docker)

1) Record a cast:

```
asciinema rec demo.cast -c "ratatui-py-dashboard"
```

2) Convert to GIF

Option A (preferred): asciinema-agg (install via Homebrew or cargo)

```
asciinema-agg --fps 60 --idle 2 demo.cast docs/assets/dashboard.gif
```

Option B: asciicast2gif (requires PhantomJS)

```
asciicast2gif -t solarized-dark -S 2 -s 2 demo.cast docs/assets/dashboard.gif
# Ensure 'phantomjs' is installed or PHANTOMJS_BIN is set
```

- `-t` theme (try: `tango`, `solarized-dark`, `solarized-light`)
- `-S` speed multiplier (2x)
- `-s` scale factor (2x)

3) Optionally convert GIF to MP4 for smoother playback in browsers:

```
ffmpeg -y -i docs/assets/dashboard.gif -movflags +faststart -pix_fmt yuv420p \
  -vf "scale=trunc(iw/2)*2:trunc(ih/2)*2" docs/assets/dashboard.mp4
```

4) Commit `docs/assets/dashboard.gif` (and `.mp4`) and it will render in README/docs.

## Option B: Asciinema + SVG (svg-term)

1) Record a cast:

```
asciinema rec demo.cast -c "ratatui-py-dashboard"
```

2) Convert to SVG via svg-term (Node.js required):

```
npm i -g svg-term-cli
svg-term --cast demo.cast --out docs/assets/dashboard.svg \
  --window --width 100 --height 30 --font-size 14
```

- Adjust `--width/--height` to match columns/rows, or omit to auto-fit.

3) Embed `docs/assets/dashboard.svg` in README/docs instead of GIF.

## Option C: Host on asciinema.org

1) Upload the cast:

```
asciinema upload demo.cast
```

2) Copy the share URL and embed a link or badge in README.

## Tips

- Use a clean background (e.g., solarized-dark) for legibility.
- Resize your terminal to a common size (e.g., 100x30) before recording.
- Keep the clip short (10–20 seconds) and show the core interactions: tabs (a/d), selection (j/k), spike (r), quit (q).
