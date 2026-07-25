"""Crop per-line WHOLE-ROW strips from a full 1850 census page image.

One crop per line (42 per page), each covering the full page width. Column
cropping is deliberately skipped — the row geometry generalizes across pages
(same y-offsets work), but column boundaries drift and need form registration
we're not doing yet. The HTR model will learn to read the whole row and output
a structured label; column extraction happens in post-processing.

Usage:
    python crop_cells.py PAGE.png OUT_DIR
        emits OUT_DIR/line_01.png ... line_42.png (full-width strips)
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from PIL import Image

LAYOUT = json.loads((Path(__file__).parent / "layout.json").read_text())


def crop_rows(page_img: Path, out_dir: Path) -> list[Path]:
    n_rows = LAYOUT["n_rows"]
    row1_top = LAYOUT["row1_top"]
    pitch = LAYOUT["row_pitch"]
    margin = LAYOUT["crop_margin"]

    img = Image.open(page_img)
    W, H = img.size

    out_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for line in range(1, n_rows + 1):
        y0 = max(0, row1_top + (line - 1) * pitch - margin)
        y1 = min(H, row1_top + line * pitch + margin)
        out = out_dir / f"line_{line:02d}.png"
        img.crop((0, y0, W, y1)).save(out)
        written.append(out)
    return written


def main() -> None:
    if len(sys.argv) != 3:
        print("usage: crop_cells.py PAGE.png OUT_DIR", file=sys.stderr)
        sys.exit(2)
    page = Path(sys.argv[1])
    out = Path(sys.argv[2])
    written = crop_rows(page, out)
    print(f"wrote {len(written)} full-row crops to {out}")


if __name__ == "__main__":
    main()
