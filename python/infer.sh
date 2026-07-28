#!/bin/bash
# Recognize text in a single pre-cropped row image using the trained kraken
# HTR model. Prints the decoded text to stdout.
#
# Usage:  ./infer.sh IMAGE.png
#
# Runs on the Mac (Intel) because the Pi's ARM CPU can't run current PyTorch.
# Rails would invoke this over SSH:
#   ssh admin@192.168.4.27 '~/scriptorium/infer.sh /tmp/crop.png'
set -euo pipefail

KRAKEN="${KRAKEN:-$HOME/kraken7_venv/bin/kraken}"
MODEL="${MODEL:-$HOME/scriptorium/models/barton_htr.safetensors}"

if [ $# -ne 1 ]; then
    echo "usage: infer.sh IMAGE.png" >&2
    exit 2
fi

img="$1"
out=$(mktemp -t kraken_out.XXXXXX)
trap "rm -f $out" EXIT

"$KRAKEN" -i "$img" "$out" ocr -m "$MODEL" -s > /dev/null 2>&1
cat "$out"
