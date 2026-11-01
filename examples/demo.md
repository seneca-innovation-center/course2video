# Demo: sample course to narrated video

Two sample courses are included (both CC-BY-4.0, written for this project):

| Course | PDF | Equations |
|---|---|---|
| [`sample_course/`](sample_course/) Vector spaces | 2 pages, 6 sections | 4, as plain text lines |
| [`probability_course/`](probability_course/) Introduction to probability | 3 pages, 5 chapters | 8, **typeset as images** |

The numbers below come from real runs on 2026-10-29 (Apple Silicon laptop, no NVIDIA GPU)
with **Docling + an LLM + Piper** (initial development runs, to be reproduced with
gpt-oss-120b). Their output files are in each course's `output_initial/` folder (slides, script, alignment report, lecture plan,
subtitles and sample frames; videos are not committed).

> To run on premises with gpt-oss-120b, use `configs/gpt-oss-vllm.yaml`; see
> [`../docs/local-llm.md`](../docs/local-llm.md).

## 0. Offline first (no API key, no GPU)

```bash
make setup && make test && make demo-mock
```

This produces `out/demo_mock/video.mp4` with silent audio, using the mock LLM. It proves the
plumbing, not the quality.

## 1. Parse and generate slides, then stop

```bash
make setup-full
course2video run examples/sample_course/vector_spaces.pdf --out out/run1 --config configs/gpt-oss-vllm.yaml
```

```
[1/2] 9 slides written to out/run1/slides.json and out/run1/slides.md

Lecturer review required. Edit slides.md or slides.json, then run:
    course2video continue out/run1 --from md     (or --from json)
```

| File | What to look at |
|---|---|
| `parsed.md` | What the parser recovered. Equations appear as `$$...$$` when Docling decoded them |
| `slides.md` | The slides, in an easy-to-edit format |
| `meta.json` | Parser warnings, LLM model, **retry attempts**, timings |

In this run the slides validated on the **first attempt**. Docling decoded equation (2) as
`a ( u ) = ( a ( u 1 , \dots , a ( u n ) )` (broken), and the slide contains the correct
`a\mathbf{u} = (a u_1, \dots, a u_n) \quad (2)`. That is good, but it is exactly the kind of
change a lecturer must check against the source. (The slide also kept the source's equation
number `(2)`, which a lecturer may want to delete.)

## 2. Lecturer review

Edit `out/run1/slides.md`: fix wording, correct an equation, delete a slide. Then:

```bash
course2video continue out/run1 --from md
```

Invalid edits (e.g. a slide left with no bullets, unbalanced braces in LaTeX) are rejected,
and nothing is narrated:

```
Review edits rejected, nothing was narrated.
slides.json is invalid:
slides.0.bullets: List should have at least 1 item after validation, not 0
```

## 3. Script, alignment check, video

```
[2/2] done: {
  "pptx": "out/run1/deck.pptx",
  "frames": 19,
  "alignment": {"overall_coverage": 1.0, "flagged_slides": []},
  "video": "out/run1/video.mp4",
  "subtitles": "out/run1/subtitles.srt",
  "duration_s": 447.66
}
```

The 9 approved slides become a 19-frame lecture: title, outline, a "Part N" frame before
each of the 6 parts, the content slides (with a "PART 2 OF 6 · …" breadcrumb and a progress
bar), and a summary. To change the layout or the `lecture:` settings later without calling
the LLM again:

```bash
course2video render out/run1
```

| File | Contents |
|---|---|
| `script.md` / `script.json` | Narration per slide, generated from the approved slides only |
| `alignment.json` | Per-bullet and per-equation coverage; slides under 0.8 are flagged |
| `lecture_plan.json` | Every frame of the video in order, with its narration |
| `deck.pptx` | Editable deck with the same structure, narration in the speaker notes |
| `images/`, `audio/` | One PNG and one WAV per frame |
| `video.mp4` | 1920×1080 H.264 + AAC |
| `subtitles.srt` | Subtitles timed from the real audio durations |

## Measured on these runs

| | Vector spaces | Probability |
|---|---|---|
| Parse (Docling + formula model on **CPU**) | 402 s | 711 s |
| Slides (LLM) | 17 s, valid on 1st attempt | 26 s, valid on 1st attempt |
| Script (LLM) | 21 s, valid on 1st attempt | 27 s, valid on 1st attempt |
| Images + Piper TTS + FFmpeg | 59 s | 81 s |
| Content slides → video frames | 9 → 19 | 12 → 21 |
| Video length | 7 min 28 s | 10 min 40 s |
| Alignment (overall) | 100 % | 96.8 % (1 slide flagged: a false negative, see `docs/limitations.md`) |
| Parser problems seen | equation (2) decoded with unbalanced brackets | equation (4) decoded with invented text appended |

These are two runs on two clean documents. It shows the pipeline works; it is **not** a quality
evaluation. For that, use [`../eval/rubric.md`](../eval/rubric.md).

## A real 3-document course, 20-minute target (MIT 18.05)

`examples/mit1805_bayes/`: Reading 3 (12 pages) + Problem Set 2 + its official solutions,
from MIT OpenCourseWare (CC BY-NC-SA 4.0, downloaded by `scripts/fetch_mit1805_example.sh`,
not committed; outputs are not committed either, since they are derivatives under the same
licence). Initial run on 2026-10-31 with Docling + an LLM + Piper, slides approved without edits:

| | Result |
|---|---|
| Documents | 3, roles and link read from `course.yaml` (file-name guessing also found them all) |
| Problems linked to solutions | 6 of 6 by number; problems 1-3 selected in `course.yaml` |
| Slides | 24: 15 theory, 3 exercise, 6 solution; all valid on the 1st attempt |
| Lecture | 37 frames, 10 parts = the reading's 7 chapters + 3 worked problems |
| Script | 3 batches; 1 retried once because a narration exceeded the length limit |
| **Length** | **target 20 min, actual 22.9 min** (+15 %; the narration averaged 140 words per slide for 125 requested) |
| Alignment | 91.7 % overall, 3 slides flagged for a human look |
| Parse (Docling, CPU, cached afterwards) | Reading 44 min, solutions 24 min, problem set 5 s |
| Slides + script (LLM) | 95 s + 75 s |
| Render + TTS + video | 55 s |

Spot checks against the official solution: blue taxi 1/3, trees of cards E[X] = 26/7 ≈ 3.7143,
base-rate example 8.3 %: all match.

First run, before fixes, for the record: 29.1 min for a 20-min target and 17 "parts", because
sub-headings became parts and the per-chunk slide budget was rounded up. Fixed by mapping
slides to the document's own chapter headings, exact budget rounding, and a narration length
check with retry.

### After the teaching-style change (same course, same model)

Slides now carry keywords and the narration explains with examples: 14 slides, 7.6 words per
bullet, 246 spoken words per slide, 23.4 min for the 20-min target, 8 talking points flagged
for review in `grounding.json`. Details and the before/after table: `docs/teaching_style.md`.
