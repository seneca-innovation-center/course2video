# Architecture (pipeline v0)

```
 course PDF / Markdown
        │
        ▼
 ┌──────────────┐   parsing/      Docling (layout, reading order, formulas → LaTeX)
 │ 1. Parse     │                 or pypdf (text layer only, no ML) behind one Parser interface
 └──────┬───────┘
        ▼  parsed.md
 ┌──────────────┐   slides/       chunk by headings → LLM → JSON → Pydantic validation
 │ 2. Slides    │                 → on failure, send the errors back and retry (max N)
 └──────┬───────┘
        ▼  slides.json + slides.md
 ┌──────────────┐   review/       ██ STOP ██  the lecturer edits slides.md or slides.json
 │ 3. REVIEW    │                 `course2video continue` re-validates and sets approved=true
 └──────┬───────┘
        ▼  approved slides.json  (single source of truth)
 ┌──────────────┐   script/       LLM sees ONLY the approved slide JSON, never the source
 │ 4. Script    │
 └──────┬───────┘
        ▼  script.json
 ┌──────────────┐   script/alignment.py   per-bullet / per-equation coverage → alignment.json
 │ 5. Alignment │
 └──────┬───────┘
        ▼
 ┌──────────────┐   render/lecture.py   wrap the approved slides in a lecture:
 │ 6. Structure │                 title → outline → [Part N → slides]… → summary
 └──────┬───────┘                 (deterministic, no LLM) → lecture_plan.json
        ▼
 ┌──────────────┐   render/       python-pptx (deck.pptx, narration in speaker notes)
 │ 7. Render    │                 frame PNGs with breadcrumb + progress bar (Pillow / LibreOffice)
 └──────┬───────┘
        ▼
 ┌──────────────┐   tts/          Piper (local), macOS `say`, or silent stub (CI)
 │ 8. TTS       │                 one WAV per frame
 └──────┬───────┘
        ▼
 ┌──────────────┐   render/       FFmpeg: one segment per slide, timed by the REAL audio
 │ 9. Assemble  │                 length → video.mp4 + subtitles.srt
 └──────────────┘
```

## Stages

| # | Stage | Module | Output | Deterministic? |
|---|---|---|---|---|
| 1 | Parse | `parsing/` | `parsed.md` | yes (for a given parser version) |
| 2 | Slide generation | `slides/generate.py`, `slides/validate.py` | `slides.json`, `slides.md` | no (LLM) → hence review |
| 3 | Lecturer review | `review/` | approved `slides.json` | human |
| 4 | Script | `script/generate.py` | `script.json`, `script.md` | no (LLM) |
| 5 | Alignment check | `script/alignment.py` | `alignment.json` | yes |
| 6 | Lecture structure | `render/lecture.py` | `lecture_plan.json` | yes |
| 7 | Render | `render/pptx_builder.py`, `render/slide_images.py` | `deck.pptx`, `images/*.png` | yes |
| 8 | TTS | `tts/` | `audio/*.wav` | yes for Piper with a fixed voice |
| 9 | Assembly | `render/video_assembly.py`, `render/subtitles.py` | `video.mp4`, `subtitles.srt` | yes |

Every run also writes `meta.json` (parser, LLM backend and model, retry attempts,
timings, coverage) and `state.json` (where the run stopped), so a run can be audited.

## Lecture structure

A video that starts on the first content slide feels like joining a course halfway. Stage 6
wraps the approved slides in a lecture, built from the deck alone (no LLM, nothing extra to
review):

| Frame | Shows | Narration |
|---|---|---|
| Title | course title, `lecture.subtitle`, `lecture.presenter`, `lecture.institution` | "Welcome. In this lecture we study …" |
| Outline | numbered list of parts | "Here is the plan. We will go through N parts: …" |
| Part N (one per section) | part number and name, outline with done ✓ / current ▶ / upcoming | "Let's start with part 1: …" / "Now we move on to part N: …" |
| Content | the slide; header breadcrumb "PART 2 OF 6 · SUBSPACES" | the generated script |
| Summary | all parts ticked, "Thank you for watching" | "That brings us to the end … We covered …" |

Every frame has a progress bar with a marker at the start of each part, plus "n / N".
Parts are consecutive slides with the same `source_section`. With a single section, the
outline and part frames are skipped. Narration templates exist for English, French and
Spanish (picked from the deck's `language`). Each element can be switched off in the
`lecture:` block of the config. The script prompt is told that the video already has its
own welcome and closing, so the narration links slides instead of greeting.

## Figures

Docling's pictures (and `![caption](file)` in Markdown sources) are numbered across the whole
course as F1, F2, … and saved in `figures/` with `figures.json` (caption, page, source). In the
text sent to the LLM each one appears where it sits in the document, as `[Figure F3: caption]`.
A slide may show one figure (`figure: "F3"`); ids not present in the slide's source are
rejected and retried. In `slides.md` the lecturer sees a `Figure: F3` line, can change or delete
it, and unknown ids are rejected. The figure is drawn in a right-hand column of the slide image
and the PPTX, and the narration is told what is on screen.

## Shorter videos: one per part

With `render: {per_part_videos: true}` the pipeline also writes `parts/part_01.mp4`,
`parts/part_01.srt`, … one video per part of the lecture (title and outline go with part 1,
the summary with the last part), next to the full `video.mp4`. Each part is typically a few
minutes, in line with the finding that shorter videos are more engaging
([`teaching_style.md`](teaching_style.md)). Durations are listed in `meta.json` → `parts`.

## Pluggable parts

| Interface | File | Implementations | Selected by |
|---|---|---|---|
| `LLMBackend` | `llm/base.py` | `mock`, `openai_compat` (vLLM, Ollama, any OpenAI-style server) | `llm.backend` |
| `Parser` | `parsing/base.py` | `docling`, `pypdf`, `markdown` | `parser.backend` |
| `TTSBackend` | `tts/base.py` | `piper`, `say`, `stub` | `tts.backend` |
| renderer | `render/slide_images.py` | `pillow`, `libreoffice` | `render.renderer` |

Switching models changes only the config file (e.g. `configs/gpt-oss-vllm.yaml` →
`configs/gpt-oss-20b-ollama.yaml`). No code changes.

## Design principles, as implemented

* **The validated slide JSON is the single source of truth.** `generate_script()` refuses
  a deck whose `approved` flag is false, and its prompt contains only slide JSON.
* **Valid is not the same as correct.** Pydantic plus LaTeX checks guarantee shape;
  `review/` puts a human in charge of content; `alignment.json` measures narration coverage.
* **Constrained decoding where available, validation always.** The JSON schema is sent to
  the server (vLLM guided decoding, Ollama structured outputs), but output is still
  validated locally, because not every server enforces every constraint.
* **Reproducible assembly.** No generative video. Same slides + same voice → same video.
