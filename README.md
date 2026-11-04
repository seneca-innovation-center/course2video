# course2video

[![CI](https://github.com/seneca-innovation-center/course2video/actions/workflows/ci.yml/badge.svg)](https://github.com/seneca-innovation-center/course2video/actions/workflows/ci.yml)
![status](https://img.shields.io/badge/status-early%20development-orange)
![licence](https://img.shields.io/badge/licence-Apache--2.0-blue)

**A self-hostable, open-source pipeline that turns course documents into lecturer-approved
slides and narrated videos, without sending course material to a cloud service.**

> **Status: early development.** Pipeline v0 runs end to end on the sample courses and on a
> real 3-document course. The results in [`examples/demo.md`](examples/demo.md) are development runs made
> with a hosted LLM API on openly licensed sample material. The pipeline is built to run on
> premises: the deployment target is gpt-oss-120b served on our internal server through an
> OpenAI-compatible API; recording the same runs there is the next step (#9).
> Output quality has **not** been formally evaluated yet (see [`eval/rubric.md`](eval/rubric.md)).

## The problem

Universities hold large archives of lecture notes, exercise sheets, solutions and
practicals. Turning them into teaching media is slow by hand, and cloud AI tools are often
ruled out by privacy, copyright and data-sovereignty rules. The individual open-source
tools exist (document parsers, open-weight LLMs, TTS, FFmpeg). What is missing is a clear,
auditable way to combine them on premises.

## What v0 does

**Input:** one document, or a **course folder** with lecture notes, exercise sheets and their
solutions. Roles come from `course.yaml` or from file names; each exercise is linked to its
solution by number (`course_index.json` shows every link and every guess).

```
PDF ─► Markdown ─► slide JSON ─► LECTURER REVIEW ─► script ─► alignment check ─► PPTX + TTS ─► MP4 + SRT
      (Docling)   (LLM, validated     (edit .md      (LLM, from     (coverage per
                   + retried)          or .json)      slides only)    bullet/equation)
```

* **Course packages.** Theory slides come from the lecture notes; each selected exercise
  becomes a worked example (problem slide, then solution slides built only from the
  official solution), shown in its own colour with its source ("Problem Set 2, Problem 2").
* **Target length.** `--minutes 20` (or `target_minutes` in `course.yaml`) sets the number of
  slides and words per slide; `meta.json` reports target versus actual. Short sources give a
  shorter video and a warning, never padding.
* **Figures from the sources.** Diagrams found by the parser (e.g. a probability tree in the
  official solutions) can be shown on the slide, chosen per slide and approved in review.
* **Bullets revealed with the narration** (`render.reveal_bullets`), and optionally one short
  video per part (`render.per_part_videos`).
* **English and French** structure, wording and voice, picked from the course language.
* **Scoring tools** for a review session: `course2video score` (see `eval/rubric.md`).
* **Validated structure.** Slides follow a Pydantic schema ([`schemas/`](schemas/)). Invalid
  LLM output is sent back with the validator's errors and retried a bounded number of times.
* **Lecturer in the loop.** The run **stops** after slide generation. Nothing is narrated
  until the lecturer has reviewed `slides.md` (or `slides.json`) and run `course2video continue`.
* **Script from approved slides only.** The narration model never sees the source document.
* **Alignment check.** `alignment.json` reports, per slide, which bullets and equation
  explanations the narration actually covers.
* **Slides show, the lecturer explains.** Slides carry 2-4 keyword bullets; each slide also has
  reviewed *talking points* from the sources (intuition, a worked example with its numbers, the
  common mistake) that the narration develops, like a professor at the board. Based on a real
  MIT lecture transcript and multimedia-learning research: [`docs/teaching_style.md`](docs/teaching_style.md).
* **A real lecture, not a slide dump.** The video opens with a title and an outline,
  announces each part ("Part 2 of 6: Subspaces"), shows a breadcrumb and a progress bar on
  every slide, and ends with a summary.
* **Deterministic assembly.** python-pptx, Pillow or LibreOffice, Piper TTS and FFmpeg. No
  generative video. Segment length comes from the real audio duration.
* **Accessibility.** SRT subtitles are exported with the video.

Details: [`docs/architecture.md`](docs/architecture.md).

## LLM backends: a locally hosted model

| Backend | Where the model runs | Use |
|---|---|---|
| `mock` | nowhere (fixed heuristics) | tests and CI, no GPU or network |
| `openai_compat` | **your server** (vLLM, Ollama) | target deployment, e.g. **gpt-oss-120b** |

Switching models is a config change, not a code change: see [`docs/local-llm.md`](docs/local-llm.md).
The gpt-oss backend is covered by tests against a simulated server; an end-to-end run with
gpt-oss-120b has not been recorded yet.

## Quick start

```bash
make setup          # Python >= 3.10, ffmpeg on PATH
make test           # offline tests: mock LLM, silent stub TTS
make demo-mock      # whole pipeline offline → out/demo_mock/video.mp4 (silent audio)
```

With real components (Docling, Piper, and an LLM):

```bash
make setup-full
vllm serve openai/gpt-oss-120b --port 8000    # on the GPU server; see docs/local-llm.md
course2video run examples/sample_course/vector_spaces.pdf --out out/run1 --config configs/gpt-oss-vllm.yaml
#   → review and edit out/run1/slides.md
course2video continue out/run1 --from md
```

Step-by-step walkthrough with real output: [`examples/demo.md`](examples/demo.md).

A real multi-document course (MIT OpenCourseWare 18.05: reading + problem set + solutions,
CC BY-NC-SA, downloaded rather than committed): [`examples/mit1805_bayes/`](examples/mit1805_bayes/SOURCE.md).

```bash
make run-mit       # fetch the 3 PDFs, then slides for a 20-minute lecture; review; make continue OUT=out/mit_bayes
```

## What you need to run it

| Step | Laptop | GPU server |
|---|---|---|
| Parsing (Docling with formula decoding) | slow: about 4 min per formula-heavy page on CPU | recommended |
| LLM | gpt-oss-20b with 16 GB+ memory | gpt-oss-120b on one 80 GB GPU |
| Review, slide images, TTS, video | yes, about a minute per course | yes |

Details, measured times and disk space: [`docs/requirements.md`](docs/requirements.md).

## Repository layout

| Path | Contents |
|---|---|
| `src/course2video/parsing/` | `Parser` interface; Docling and pypdf implementations |
| `src/course2video/slides/` | Pydantic models (= schema), generation, validation and retry |
| `src/course2video/review/` | export for review, import and validation of edits |
| `src/course2video/script/` | script generation, alignment check |
| `src/course2video/tts/` | `TTSBackend`; Piper, macOS `say`, silent stub |
| `src/course2video/render/` | PPTX builder, slide images, FFmpeg assembly, SRT |
| `src/course2video/llm/` | `LLMBackend`; mock, OpenAI-compatible (vLLM, Ollama) |
| `configs/` | ready-made configs: mock, gpt-oss-120b via vLLM or Ollama, gpt-oss-20b via Ollama |
| `tests/` | offline tests, plus an optional real-LLM smoke test (`pytest -m llm`) |
| `eval/rubric.md` | 0-2 manual scoring rubric |

## Known limitations

Short version: born-digital PDFs only (no OCR), exercises linked by number only (no
cross-course retrieval yet), equations decoded by
Docling can be wrong, figure captions are often missing, and the coverage metric is lexical. Full list
with examples: [`docs/limitations.md`](docs/limitations.md).

## Roadmap

Parser routing (Docling, Marker, MinerU), linking exercises to the theory sections they
use, retrieval across many courses, a review UI, and translation with glossary context (a
hypothesis to test). See [`docs/roadmap.md`](docs/roadmap.md).

## Licence

Code: [Apache-2.0](LICENSE). Every dependency, external program and model is listed with
its code and model licence in [`LICENSES_THIRD_PARTY.md`](LICENSES_THIRD_PARTY.md). Note that
the optional Piper TTS is **GPL-3.0**. We do not claim "all permissive" until that table
supports it.

Contributions are welcome: see [`CONTRIBUTING.md`](CONTRIBUTING.md).
