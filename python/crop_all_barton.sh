#!/bin/bash
# Convert all Barton page JP2s → PNG → per-line row crops.
# Reads FIRST_BARTON_FRAME + N_PAGES from CLI, defaults to Barton range.
set -euo pipefail

REEL_DIR="/home/adam/Projects/scriptorium/corpora/us_census_1850/data/reels/populationschedu0604unix"
CROPS_DIR="${CROPS_DIR:-/home/adam/Projects/scriptorium-rails/data/crops}"
FIRST_FRAME="${FIRST_FRAME:-4}"
LAST_FRAME="${LAST_FRAME:-83}"
PY="/home/adam/Projects/scriptorium/.venv/bin/python"
CROP_SCRIPT="/home/adam/Projects/scriptorium-rails/python/crop_cells.py"

mkdir -p "$CROPS_DIR"

for i in $(seq "$FIRST_FRAME" "$LAST_FRAME"); do
    frame=$(printf "%04d" "$i")
    jp2="$REEL_DIR/populationschedu0604unix_${frame}.jp2"
    png="$REEL_DIR/populationschedu0604unix_${frame}.png"
    out="$CROPS_DIR/frame_${frame}"

    if [ -d "$out" ] && [ "$(ls "$out"/line_*.png 2>/dev/null | wc -l)" = "42" ]; then
        echo "  frame $frame: already cropped, skipping"
        continue
    fi
    if [ ! -f "$png" ]; then
        if [ ! -f "$jp2" ]; then
            echo "  frame $frame: JP2 not found, skipping"
            continue
        fi
        echo "  frame $frame: converting JP2 → PNG"
        convert "$jp2" "$png"
    fi
    echo "  frame $frame: cropping rows"
    "$PY" "$CROP_SCRIPT" "$png" "$out" > /dev/null
done

echo "done. crops in $CROPS_DIR"
