"""Emit Kraken ground-truth companion files.

Kraken's `ketos train` reads pairs of `<image>.png` + `<image>.gt.txt`. This
walks manifest.jsonl and writes the label as a `.gt.txt` next to each crop.

Usage:
    python prep_kraken_gt.py MANIFEST.jsonl
"""
from __future__ import annotations

import json
import sys
from pathlib import Path


def main() -> None:
    if len(sys.argv) != 2:
        print("usage: prep_kraken_gt.py MANIFEST.jsonl", file=sys.stderr)
        sys.exit(2)
    manifest = Path(sys.argv[1])
    n = 0
    for line in manifest.read_text().splitlines():
        rec = json.loads(line)
        img = Path(rec["image"])
        gt = img.with_suffix(".gt.txt")
        gt.write_text(rec["label"], encoding="utf-8")
        n += 1
    print(f"wrote {n} .gt.txt companion files")


if __name__ == "__main__":
    main()
