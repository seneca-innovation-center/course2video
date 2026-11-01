PY ?= .venv/bin/python
PIP ?= .venv/bin/pip
C2V ?= PYTHONPATH=src $(PY) -m course2video
CONFIG ?= configs/gpt-oss-vllm.yaml
OUT ?= out/run

.PHONY: setup setup-full models test test-llm lint schemas sample-pdf demo demo-mock run run-mit continue render clean

setup:
	python3 -m venv .venv
	$(PIP) install -U pip
	$(PIP) install -e '.[dev,math]'

setup-full: setup models
	$(PIP) install -e '.[dev,math,docling,piper]'

models:
	./scripts/download_models.sh

test:
	$(PY) -m pytest

test-llm:
	C2V_SMOKE_CONFIG=$(CONFIG) $(PY) -m pytest -m llm -v

lint:
	$(PY) -m ruff check src tests scripts

schemas:
	$(C2V) schemas --out schemas

sample-pdf:
	$(PY) scripts/make_sample_pdf.py

demo-mock:
	$(C2V) run examples/sample_course/vector_spaces.pdf --out out/demo_mock \
		--config configs/mock.yaml --auto-approve

run:
	$(C2V) run examples/sample_course/vector_spaces.pdf --out $(OUT) --config $(CONFIG)

run-mit:
	./scripts/fetch_mit1805_example.sh
	$(C2V) run examples/mit1805_bayes --out out/mit_bayes --config $(CONFIG)

continue:
	$(C2V) continue $(OUT) --from md

render:
	$(C2V) render $(OUT)

demo: demo-mock

clean:
	rm -rf out .pytest_cache
