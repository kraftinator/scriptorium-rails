"""Build a name-only training manifest for the transfer-learning experiment.

Same pairing logic as build_dataset.py, but the label is just `first last`
(no tags, no other fields). The image is still the whole-row crop — the
model has to learn to find and read the name within the row.

Filters (unchanged from build_dataset.py):
- skip records where the transcriber marked uncertainty with '?'
- skip records with anomalous line_number values
- merge phantom short-page splits in the JSON so page_index → reel_frame
  stays 1:1

Usage:
    python build_dataset_names.py GT_JSON CROPS_DIR OUT_MANIFEST
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

FIRST_BARTON_FRAME = 4
MIN_FULL_PAGE_RECORDS = 30


def compute_page_starts(data: list[dict]) -> list[int]:
    starts = [0]
    for i in range(1, len(data)):
        if data[i]["line_number"] < data[i - 1]["line_number"]:
            starts.append(i)
    merged: list[int] = [starts[0]]
    i = 1
    while i < len(starts):
        prev = merged[-1]
        cur = starts[i]
        cur_end = starts[i + 1] if i + 1 < len(starts) else len(data)
        cur_len = cur_end - cur
        prev_len = cur - prev
        if prev_len < MIN_FULL_PAGE_RECORDS and cur_len < MIN_FULL_PAGE_RECORDS:
            i += 1
            continue
        merged.append(cur)
        i += 1
    return merged


def name_label(r: dict) -> str:
    f = (r.get("first_name") or "").strip()
    l = (r.get("last_name") or "").strip()
    return f"{f} {l}".strip()


def uncertain(r: dict) -> bool:
    for k in ("first_name", "last_name"):
        v = r.get(k)
        if isinstance(v, str) and "?" in v:
            return True
    return False


def main() -> None:
    if len(sys.argv) != 4:
        print("usage: build_dataset_names.py GT_JSON CROPS_DIR OUT_MANIFEST",
              file=sys.stderr)
        sys.exit(2)
    gt = Path(sys.argv[1])
    crops = Path(sys.argv[2])
    manifest = Path(sys.argv[3])

    data = json.loads(gt.read_text())
    starts = compute_page_starts(data)
    print(f"records={len(data)}  pages={len(starts)}")

    total = missing = filtered = written = 0
    manifest.parent.mkdir(parents=True, exist_ok=True)
    with manifest.open("w") as f:
        for pg_idx in range(len(starts)):
            s = starts[pg_idx]
            e = starts[pg_idx + 1] if pg_idx + 1 < len(starts) else len(data)
            reel_frame = FIRST_BARTON_FRAME + pg_idx
            for r in data[s:e]:
                total += 1
                ln = r.get("line_number")
                if not isinstance(ln, int) or not (1 <= ln <= 42):
                    filtered += 1
                    continue
                if uncertain(r):
                    filtered += 1
                    continue
                label = name_label(r)
                if not label:
                    filtered += 1
                    continue
                crop = crops / f"frame_{reel_frame:04d}" / f"line_{ln:02d}.png"
                if not crop.exists():
                    missing += 1
                    continue
                f.write(json.dumps({"image": str(crop),
                                    "label": label}) + "\n")
                written += 1

    print(f"total={total} filtered={filtered} missing_crop={missing} "
          f"written={written}")
    print(f"manifest → {manifest}")


if __name__ == "__main__":
    main()
