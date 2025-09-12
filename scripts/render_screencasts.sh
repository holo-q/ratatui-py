#!/usr/bin/env bash
set -euo pipefail

# Render screencasts defined in a simple TSV index (cast\tgif\tmp4\ttheme\tspeed\tscale).
# Defaults to scripts/screencasts.tsv. You can override with -i <index>.
#
# Examples:
#   bash scripts/render_screencasts.sh                 # render all entries (skip up-to-date)
#   bash scripts/render_screencasts.sh dashboard       # render lines matching 'dashboard' in any column
#   bash scripts/render_screencasts.sh -f              # force re-render
#   bash scripts/render_screencasts.sh -n              # dry run
#   bash scripts/render_screencasts.sh -i custom.tsv   # alternate index
#
# Tooling:
#   - Prefers Docker image asciinema/asciicast2gif for cast->gif
#   - Falls back to local asciinema-agg if available
#   - Converts GIF -> MP4 with ffmpeg (even dimensions, faststart)

INDEX="scripts/screencasts.tsv"
DRY_RUN=0
FORCE=0

usage() {
  cat <<USAGE
Usage: $0 [-i index.tsv] [-n] [-f] [filter...]
  -i   Path to TSV index (default: scripts/screencasts.tsv)
  -n   Dry run (print actions only)
  -f   Force re-render even if outputs are newer than input
  filter  Optional substring filter to select rows (match anywhere)
USAGE
}

while getopts ":i:nfh" opt; do
  case $opt in
    i) INDEX="$OPTARG" ;;
    n) DRY_RUN=1 ;;
    f) FORCE=1 ;;
    h) usage; exit 0 ;;
    \?) echo "Invalid option: -$OPTARG" >&2; usage; exit 2 ;;
  esac
done
shift $((OPTIND-1))

FILTER=("$@")

have_cmd() { command -v "$1" >/dev/null 2>&1; }

# Detect agg binary name (asciinema-agg or agg)
detect_agg() {
  if have_cmd asciinema-agg; then echo "asciinema-agg"; return 0; fi
  if have_cmd agg; then echo "agg"; return 0; fi
  return 1
}

render_cast_to_gif() {
  local cast="$1" gif="$2" theme="${3:-solarized-dark}" speed="${4:-2}" scale="${5:-2}"
  # Convert v3 header to v2 if needed (some tools only accept v1/v2)
  local header
  header=$(head -n1 "$cast" || true)
  if [[ "$header" == "{"*"\"version\"":3* ]]; then
    local tmp_cast
    tmp_cast=$(mktemp)
    echo "[cast] converting v3 -> v2: $cast"
    if [ "$DRY_RUN" -eq 0 ]; then
      python3 scripts/convert_cast_v3_to_v2.py "$cast" "$tmp_cast"
    fi
    cast="$tmp_cast"
  fi
  local AGG_BIN
  AGG_BIN=$(detect_agg || true)
  if [ -n "$AGG_BIN" ]; then
    # Map inputs: use speed as --speed, choose theme when supported, rely on default cols/rows from cast
    echo "[cast->gif] $AGG_BIN: $cast -> $gif (speed=$speed theme=$theme)"
    if [ "$DRY_RUN" -eq 0 ]; then
      if [ "$AGG_BIN" = "asciinema-agg" ]; then
        # asciinema-agg (older CLI): --fps approximates speed*30
        local fps=$((30 * speed))
        "$AGG_BIN" --fps "$fps" --idle 2 "$cast" "$gif"
      else
        # agg v1.5.0 CLI: supports --speed and --theme
        "$AGG_BIN" --speed "$speed" --theme "$theme" "$cast" "$gif"
      fi
    fi
  elif have_cmd asciicast2gif; then
    # asciicast2gif depends on PhantomJS; ensure it's available
    if ! have_cmd phantomjs && [ -z "${PHANTOMJS_BIN:-}" ]; then
      echo "ERROR: 'asciicast2gif' requires PhantomJS. Install 'phantomjs' (AUR) or set PHANTOMJS_BIN=/path/to/phantomjs, or install 'asciinema-agg'." >&2
      return 1
    fi
    echo "[cast->gif] asciicast2gif: $cast -> $gif (theme=$theme speed=$speed scale=$scale)"
    if [ "$DRY_RUN" -eq 0 ]; then
      asciicast2gif -t "$theme" -S "$speed" -s "$scale" "$cast" "$gif"
    fi
  else
    echo "ERROR: need 'asciinema-agg' or 'asciicast2gif' installed (no Docker)." >&2
    return 1
  fi
}

gif_to_mp4() {
  local gif="$1" mp4="$2"
  if ! have_cmd ffmpeg; then
    echo "ERROR: ffmpeg not found (required for GIF->MP4). Try: sudo apt-get install -y ffmpeg" >&2
    return 1
  fi
  echo "[gif->mp4] ffmpeg: $gif -> $mp4"
  if [ "$DRY_RUN" -eq 0 ]; then
    ffmpeg -y -i "$gif" -movflags +faststart -pix_fmt yuv420p \
      -vf "fps=30,scale=trunc(iw/2)*2:trunc(ih/2)*2" -r 30 "$mp4" </dev/null >/dev/null 2>&1 || {
        echo "ffmpeg failed (see above output)." >&2; return 1; }
  fi
}

should_render() {
  local in="$1" out="$2"
  if [ "$FORCE" -eq 1 ]; then return 0; fi
  if [ ! -f "$out" ]; then return 0; fi
  # If output newer than input, skip
  [ "$out" -nt "$in" ] && return 1 || return 0
}

match_filter() {
  local line="$1"
  if [ ${#FILTER[@]} -eq 0 ]; then return 0; fi
  for f in "${FILTER[@]}"; do
    if [[ "$line" == *"$f"* ]]; then return 0; fi
  done
  return 1
}

if [ ! -f "$INDEX" ]; then
  echo "Index not found: $INDEX" >&2
  exit 1
fi

echo "Using index: $INDEX"
rc=0
while IFS=$'\t' read -r cast gif mp4 theme speed scale rest; do
  # Skip header/comments/blank lines
  [[ -z "$cast" ]] && continue
  [[ "$cast" =~ ^# ]] && continue
  [[ "$cast" == "cast" ]] && continue
  line="$cast\t$gif\t$mp4\t$theme\t$speed\t$scale"
  if ! match_filter "$line"; then continue; fi

  if [ ! -f "$cast" ]; then
    echo "WARN: input cast not found: $cast (skipping)" >&2
    continue
  fi

  # Render GIF
  if should_render "$cast" "$gif"; then
    render_cast_to_gif "$cast" "$gif" "$theme" "$speed" "$scale" || rc=$?
  else
    echo "[cast->gif] up-to-date: $gif"
  fi

  # Render MP4
  if [ -n "${mp4:-}" ]; then
    if should_render "$gif" "$mp4"; then
      gif_to_mp4 "$gif" "$mp4" || rc=$?
    else
      echo "[gif->mp4] up-to-date: $mp4"
    fi
  fi
done < "$INDEX"

exit "$rc"
