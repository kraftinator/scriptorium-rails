"""Downscale row crops for faster training.

Kraken already resizes the height to 120 px internally, so keeping the
original 190 px height wastes I/O. Downscaling to a 3000×120 target keeps
each character comfortably readable but cuts the dataloader work by ~4×
(image bytes drop from ~1.2 MB to ~0.3 MB uncompressed).

Usage:
    python resize_crops.py CROPS_DIR TARGET_WIDTH TARGET_HEIGHT
"""
from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image


def main() -> None:
    if len(sys.argv) != 4:
        print("usage: resize_crops.py CROPS_DIR TARGET_W TARGET_H",
              file=sys.stderr)
        sys.exit(2)
    root = Path(sys.argv[1])
    tw, th = int(sys.argv[2]), int(sys.argv[3])

    n = 0
    for p in sorted(root.rglob("line_*.png")):
        img = Image.open(p).convert("L")
        if img.size == (tw, th):
            continue
        img.resize((tw, th), Image.LANCZOS).save(p, optimize=True)
        n += 1
    print(f"resized {n} images to {tw}x{th}")


if __name__ == "__main__":
    main()
