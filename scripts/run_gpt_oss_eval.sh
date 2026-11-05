#!/usr/bin/env bash
set -uo pipefail
cd "$(dirname "$0")/.."

: "${GPTOSS_BASE_URL:?set GPTOSS_BASE_URL first, e.g. export GPTOSS_BASE_URL=http://host:port/v1}"
: "${GPTOSS_API_KEY:?set GPTOSS_API_KEY first: export GPTOSS_API_KEY=...}"
export GPTOSS_API_KEY
export PYTHONPATH=src
PY="${PY:-.venv/bin/python}"
BASE_CONFIG="${CONFIG:-configs/gpt-oss-120b-8k.yaml}"
OUT="${OUT:-out/gptoss}"
CANDIDATES="${GPTOSS_MODEL:-gpt-oss-120b openai/gpt-oss-120b gpt-oss:120b gpt-oss}"
COURSES="${COURSES:-vector_spaces probability french_course mit_bayes}"
mkdir -p "$OUT/logs"

write_config() {
  "$PY" - "$BASE_CONFIG" "$OUT/config.yaml" "$GPTOSS_BASE_URL" "$1" "$2" <<'PYEOF'
import sys, yaml
src, dst, url, model, structured = sys.argv[1:6]
cfg = yaml.safe_load(open(src))
cfg["llm"].update(base_url=url, model=model, structured_output=structured == "true",
                  api_key_env="GPTOSS_API_KEY")
yaml.safe_dump(cfg, open(dst, "w"), sort_keys=False)
PYEOF
}

echo "== 1/5 offline tests"
"$PY" -m pytest -q > "$OUT/logs/offline_tests.log" 2>&1 && tail -1 "$OUT/logs/offline_tests.log" || { tail -5 "$OUT/logs/offline_tests.log"; echo "offline tests failed"; exit 1; }

echo "== 2/5 connection and model name"
MODEL=""; STRUCTURED=""
for structured in true false; do
  for m in $CANDIDATES; do
    write_config "$m" "$structured"
    if "$PY" -m course2video check-llm --config "$OUT/config.yaml" > "$OUT/logs/check_llm.log" 2>&1; then
      MODEL="$m"; STRUCTURED="$structured"; break 2
    fi
    reason="$(grep -E 'LLMError|Error:|HTTP [0-9]{3} from' "$OUT/logs/check_llm.log" | grep -v 'HTTP Request' | tail -1 | cut -c1-200)"
    echo "   tried model=$m structured_output=$structured: ${reason:-no answer}"
    if grep -q "HTTP 401" "$OUT/logs/check_llm.log"; then
      echo "the server rejected the key (HTTP 401): check GPTOSS_API_KEY and run again"
      exit 1
    fi
  done
done
if [ -z "$MODEL" ]; then
  echo "could not get an answer from $GPTOSS_BASE_URL; see $OUT/logs/check_llm.log"
  echo "if the model has another name: export GPTOSS_MODEL=<name> and run again"
  exit 1
fi
echo "   ok: model=$MODEL structured_output=$STRUCTURED"
tail -1 "$OUT/logs/check_llm.log"

echo "== 3/5 smoke test with the real model"
C2V_SMOKE_CONFIG="$OUT/config.yaml" "$PY" -m pytest -m llm -q > "$OUT/logs/smoke_test.log" 2>&1
tail -1 "$OUT/logs/smoke_test.log"

echo "== 4/5 courses (slides approved without edits)"
./scripts/fetch_mit1805_example.sh > "$OUT/logs/fetch_mit.log" 2>&1 || echo "   MIT files could not be downloaded; that course is skipped"
run_course() {
  local name="$1" input="$2"; shift 2
  case " $COURSES " in *" $name "*) ;; *) return ;; esac
  [ -e "$input" ] || { echo "   $name: input missing, skipped"; return; }
  echo "   $name ..."
  rm -rf "$OUT/$name"
  if "$PY" -m course2video run "$input" --out "$OUT/$name" --config "$OUT/config.yaml" --auto-approve "$@" \
      > "$OUT/logs/$name.log" 2>&1; then
    echo "   $name: done"
  else
    echo "   $name: FAILED, see $OUT/logs/$name.log"; tail -3 "$OUT/logs/$name.log"
  fi
}
run_course vector_spaces examples/sample_course/vector_spaces.pdf
run_course probability examples/probability_course/probability.pdf
run_course french_course examples/cours_probabilites
run_course mit_bayes examples/mit1805_bayes

echo "== 5/5 summary"
"$PY" scripts/summarize_runs.py "$OUT"
echo "Results: $OUT/summary.md and one folder per course (video.mp4, slides.md, script.md, meta.json)."
