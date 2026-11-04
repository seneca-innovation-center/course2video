# Running with a locally hosted model (gpt-oss)

The pipeline talks to every LLM through `LLMBackend.complete()`. The target deployment is
an open-weight model served inside the institution's network, so course content never
leaves it. The reference model is **gpt-oss-120b**; gpt-oss-20b is a smaller option for
testing on modest hardware. Switching between them is a config change.

Hardware, run times and disk space: [`requirements.md`](requirements.md).

## 1. Serve the model

**vLLM** (recommended for a GPU server; one 80 GB GPU such as H100 or A100-80GB for 120b):

```bash
pip install vllm
vllm serve openai/gpt-oss-120b --port 8000
```

**Ollama** (simpler; `gpt-oss:20b` also runs on a 16 GB+ GPU or an Apple Silicon Mac):

```bash
ollama pull gpt-oss:120b     # or gpt-oss:20b
ollama serve
```

## 2. Point the pipeline at it

| Config | Server | Model |
|---|---|---|
| `configs/gpt-oss-vllm.yaml` | vLLM, `http://localhost:8000/v1` | `openai/gpt-oss-120b` |
| `configs/gpt-oss-ollama.yaml` | Ollama, `http://localhost:11434/v1` | `gpt-oss:120b` |
| `configs/gpt-oss-20b-ollama.yaml` | Ollama, `http://localhost:11434/v1` | `gpt-oss:20b` |

```bash
course2video check-llm --config configs/gpt-oss-vllm.yaml          # one tiny request
course2video run examples/sample_course/vector_spaces.pdf --out out/oss --config configs/gpt-oss-vllm.yaml
```

Or override on the command line:

```bash
course2video run in.pdf --out out/oss --llm openai_compat \
    --base-url http://gpu-server.internal:8000/v1 --model openai/gpt-oss-120b
```

## 3. Validate

Run the same assertions for each model:

```bash
make test-llm CONFIG=configs/gpt-oss-vllm.yaml
make test-llm CONFIG=configs/gpt-oss-20b-ollama.yaml
```

Then compare the runs' `meta.json` (retry attempts, timings), `alignment.json` (coverage,
spoken-to-slide word ratio) and `grounding.json` (flagged talking points) with the development
results in `examples/demo.md` and `docs/teaching_style.md`, and score 20-30 slides from
each with `eval/rubric.md`.

## Things to watch

| Issue | Where it shows | What to do |
|---|---|---|
| Server rejects `response_format` json_schema | HTTP 400 in `check-llm` | set `llm.structured_output: false`; validation and retry still apply |
| Many retries | `meta.json` → `attempts_per_chunk` | lower `slides.chunk_chars`, raise `max_retries`, try `effort: high` |
| Output truncated (`finish_reason=length`) | `LLMError` in the log | raise `llm.max_tokens` |
| Reasoning text leaking into content | JSON parse errors | use a server version with the gpt-oss (harmony) chat template; vLLM and Ollama handle this |
| Video longer than the target | `meta.json` → `video.actual_minutes` | lower `script.words_per_slide`; the length check retries once, then accepts with a warning |
