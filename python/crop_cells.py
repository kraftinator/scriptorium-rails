"""Crop per-line NAME cells from a full 1850 census page image.

Purpose: produce (image_crop, ground-truth-text) training pairs for an HTR
model. This script handles the image side — one PNG per line, cropping just
the "Names of every person" column band.

Usage:
    python crop_cells.py PAGE.png OUT_DIR
        emits OUT_DIR/line_01.png ... line_42.png

Geometry comes from layout.json (row1_top, row_pitch, name_col_frac).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from PIL import Image

LAYOUT = json.loads((Path(__file__).parent / "layout.json").read_text())


def crop_name_cells(page_img: Path, out_dir: Path) -> list[Path]:
    n_rows = LAYOUT["n_rows"]
    row1_top = LAYOUT["row1_top"]
    pitch = LAYOUT["row_pitch"]
    margin = LAYOUT["crop_margin"]
    xl_frac, xr_frac = LAYOUT["name_col_frac"]

    img = Image.open(page_img)
    W, H = img.size
    xl, xr = int(W * xl_frac), int(W * xr_frac)

    out_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for line in range(1, n_rows + 1):
        y0 = max(0, row1_top + (line - 1) * pitch - margin)
        y1 = min(H, row1_top + line * pitch + margin)
        out = out_dir / f"line_{line:02d}.png"
        img.crop((xl, y0, xr, y1)).save(out)
        written.append(out)
    return written


def main() -> None:
    if len(sys.argv) != 3:
        print("usage: crop_cells.py PAGE.png OUT_DIR", file=sys.stderr)
        sys.exit(2)
    page = Path(sys.argv[1])
    out = Path(sys.argv[2])
    written = crop_name_cells(page, out)
    print(f"wrote {len(written)} crops to {out}")


if __name__ == "__main__":
    main()
