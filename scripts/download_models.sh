#!/usr/bin/env bash
set -euo pipefail
DEST="${1:-models/piper}"
VOICE="en_US-ljspeech-medium"
BASE="https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/ljspeech/medium"
mkdir -p "$DEST"
for f in "$VOICE.onnx" "$VOICE.onnx.json" "MODEL_CARD"; do
  out="$DEST/$f"; [ "$f" = MODEL_CARD ] && out="$DEST/$VOICE.MODEL_CARD"
  if [ ! -s "$out" ]; then
    echo "downloading $f"
    curl -fL --retry 3 -o "$out" "$BASE/$f"
  fi
done
echo "Piper voice ready in $DEST"
