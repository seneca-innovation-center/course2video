#!/usr/bin/env bash
set -euo pipefail
DEST="$(cd "$(dirname "$0")/.." && pwd)/examples/mit1805_bayes"
BASE="https://ocw.mit.edu/courses/18-05-introduction-to-probability-and-statistics-spring-2022"
fetch() {
  mkdir -p "$DEST/$1"
  if [ ! -s "$DEST/$1/$2" ]; then
    echo "downloading $2"
    curl -fL --retry 3 -o "$DEST/$1/$2" "$BASE/$2"
  fi
}
fetch lecture   mit18_05_s22_class03-prep.pdf
fetch exercises mit18_05_s22_pset02.pdf
fetch solutions mit18_05_s22_pset02_sol.pdf
echo "MIT 18.05 example ready in $DEST (CC BY-NC-SA 4.0)"
