"""Build an HTR training manifest by pairing per-line row crops to the
ground-truth JSON.

Input:
    - Ground-truth JSON (per-person records with line_number, dwelling, family,
      first_name, last_name, age, sex, color, occupation, real_estate_value,
      place_of_birth).
    - A directory of pre-cropped page images: crops/frame_XXXX/line_YY.png.

Output:
    - manifest.jsonl with one line per (crop, label) pair:
        {"image": "/path/to/line_01.png", "label": "N=Alex. Brooks|A=53|..."}
    - A stats summary printed to stdout.

Reel-frame ↔ JSON-page mapping:
    - The JSON is in strict order top-to-bottom. Pages are delimited by
      line_number resets (line_number decreases → new page).
    - Anchor: reel frame 5 = record 42 (Edmund Casterline, line 1),
      reel frame 23 = record 797 (Chls. Howard, line 1). These were
      verified visually.
    - So: reel_frame = FIRST_BARTON_FRAME + page_index, with page_index
      derived from line-number resets.
    - Known JSON anomalies (a stray line_number=105 at record 608, and two
      consecutive 21-record pages around records 588-630) create a phantom
      extra page-boundary. We merge consecutive pages of fewer than
      MIN_FULL_PAGE_RECORDS records to compensate.

Label format (tagged, `|`-delimited so the model can learn missing fields):
    N=<first last> | A=<age> | S=<sex> | C=<color> | O=<occupation>
    | R=<real_estate_value> | P=<place_of_birth>

Usage:
    python build_dataset.py JSON CROPS_DIR OUT_MANIFEST
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

FIRST_BARTON_FRAME = 4          # verified: frame 5 = file page 1, so page 0 = frame 4
MIN_FULL_PAGE_RECORDS = 30      # pages with fewer records get merged with neighbor

FIELDS = [
    ("N", lambda r: _name(r)),
    ("A", lambda r: _s(r.get("age"))),
    ("S", lambda r: _s(r.get("sex"))),
    ("C", lambda r: _s(r.get("color"))),
    ("O", lambda r: _s(r.get("occupation"))),
    ("R", lambda r: _s(r.get("real_estate_value"))),
    ("P", lambda r: _s(r.get("place_of_birth"))),
]


def _s(v) -> str:
    return "" if v is None else str(v)


def _name(r: dict) -> str:
    f = _s(r.get("first_name")).strip()
    l = _s(r.get("last_name")).strip()
    return f"{f} {l}".strip()


def compute_page_starts(data: list[dict]) -> list[int]:
    """Return record indices where a new form page begins (line_number
    reset). Merges the phantom short-page splits so the count matches the
    actual reel frames."""
    starts = [0]
    for i in range(1, len(data)):
        if data[i]["line_number"] < data[i - 1]["line_number"]:
            starts.append(i)
    # Merge short-run splits: if page k has < MIN_FULL_PAGE_RECORDS records
    # and its neighbor is also short, treat them as one page.
    merged: list[int] = [starts[0]]
    i = 1
    while i < len(starts):
        prev = merged[-1]
        cur = starts[i]
        cur_end = starts[i + 1] if i + 1 < len(starts) else len(data)
        cur_len = cur_end - cur
        prev_len = cur - prev
        if prev_len < MIN_FULL_PAGE_RECORDS and cur_len < MIN_FULL_PAGE_RECORDS:
            i += 1  # skip this start (merge with previous page)
            continue
        merged.append(cur)
        i += 1
    return merged


def encode_label(r: dict) -> str:
    return " | ".join(f"{tag}={fn(r)}" for tag, fn in FIELDS)


def uncertain(r: dict) -> bool:
    """Skip records with '?' anywhere in name/occupation/place — those are
    label noise the transcriber wasn't confident about."""
    for k in ("first_name", "last_name", "occupation", "place_of_birth"):
        v = r.get(k)
        if isinstance(v, str) and "?" in v:
            return True
    return False


def main() -> None:
    if len(sys.argv) != 4:
        print("usage: build_dataset.py GT_JSON CROPS_DIR OUT_MANIFEST",
              file=sys.stderr)
        sys.exit(2)
    gt = Path(sys.argv[1])
    crops = Path(sys.argv[2])
    manifest = Path(sys.argv[3])

    data = json.loads(gt.read_text())
    starts = compute_page_starts(data)
    print(f"records={len(data)}  detected pages (after merge)={len(starts)}")

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
                crop = crops / f"frame_{reel_frame:04d}" / f"line_{ln:02d}.png"
                if not crop.exists():
                    missing += 1
                    continue
                f.write(json.dumps({"image": str(crop),
                                    "label": encode_label(r)}) + "\n")
                written += 1

    print(f"total={total}  filtered={filtered}  missing_crop={missing}  "
          f"written={written}")
    print(f"manifest → {manifest}")


if __name__ == "__main__":
    main()
