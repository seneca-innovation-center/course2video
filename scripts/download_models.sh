#!/usr/bin/env bash
set -euo pipefail
DEST="${1:-models/piper}"
BASE="https://huggingface.co/rhasspy/piper-voices/resolve/main"
mkdir -p "$DEST"
fetch_voice() {
  local voice="$1" path="$2"
  for f in "$voice.onnx" "$voice.onnx.json" "MODEL_CARD"; do
    out="$DEST/$f"; [ "$f" = MODEL_CARD ] && out="$DEST/$voice.MODEL_CARD"
    if [ ! -s "$out" ]; then
      echo "downloading $voice/$f"
      curl -fL --retry 3 -o "$out" "$BASE/$path/$f"
    fi
  done
}
fetch_voice en_US-ljspeech-medium en/en_US/ljspeech/medium
fetch_voice fr_FR-siwis-medium fr/fr_FR/siwis/medium
echo "Piper voices ready in $DEST"
