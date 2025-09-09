# Recording the Dashboard Demo

This shows how to record the `ratatui-py-dashboard` demo and generate an embeddable GIF/SVG for the README and docs.

## Option A: Asciinema + GIF (Docker)

1) Record a cast:

```
asciinema rec demo.cast -c "ratatui-py-dashboard"
```

2) Convert to GIF using the official converter (needs Docker):

```
docker run --rm -v "$PWD":/data asciinema/asciicast2gif \
  -t solarized-dark -S 2 -s 2 demo.cast docs/assets/dashboard.gif
```

- `-t` theme (try: `tango`, `solarized-dark`, `solarized-light`)
- `-S` speed multiplier (2x)
- `-s` scale factor (2x)

3) Commit `docs/assets/dashboard.gif` and it will render in README/docs.

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

