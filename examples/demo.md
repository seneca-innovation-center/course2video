# Demo: course documents to narrated video with gpt-oss-120b

All results on this page come from **gpt-oss-120b served on our internal server** through an
OpenAI-compatible API (8k context, `configs/gpt-oss-120b-8k.yaml`), with Docling parsing and
Piper TTS, run on 2026-11-05 with `scripts/run_gpt_oss_eval.sh`. Slides were approved without
edits. Output files are in each course's `output/` folder (the MIT course's are not committed:
its licence does not allow it).

| Course | Documents | Language | Equations |
|---|---|---|---|
| [`sample_course/`](sample_course/) Vector spaces | 1 PDF, 2 pages | English | 4, as text lines |
| [`probability_course/`](probability_course/) Introduction to probability | 1 PDF, 3 pages | English | 8, typeset as images |
| [`cours_probabilites/`](cours_probabilites/) Probabilités conditionnelles | lecture + TD + corrigé (Markdown) | **French** | 4 |
| [`mit1805_bayes/`](mit1805_bayes/SOURCE.md) MIT 18.05 Reading 3 | lecture + problem set + official solutions (PDF) | English | many, plus 10 figures |

## Results

| Course | Slides (theory / exercise / solution) | Video frames | Slides valid on 1st try | Script valid on 1st try | Coverage | Spoken words per slide word | Length (target) |
|---|---|---|---|---|---|---|---|
| Vector spaces | 6 / 0 / 0 | 15 | 1/1 | 2/2 | 84 % | 7.3 | 8.2 min |
| Probability | 7 / 0 / 0 | 15 | 2/2 | 2/3 | 82 % | 13.7 | 9.9 min |
| French course | 4 / 3 / 3 | 20 | 4/4 | 4/4 | 84 % | 8.0 | 11.2 min (10) |
| MIT 18.05 | 11 / 3 / 3 | 29 | 10/12 | 6/6 | 72 % | 9.1 | 23.9 min (20) |

- **Retries.** Every failed first attempt was fixed by the automatic retry: one empty answer
  from the server, one slide with 6 equations (limit 3), one narration batch above the length
  budget.
- **Correctness (MIT 18.05, checked against the official solutions):** blue taxi 1/3; trees of
  cards pmf 3/14, 2/7, 1/7, 2/7, 1/14 and E[X] = 26/7 ≈ 3.714; base-rate example 8.3 %. All match.
- **Figures.** 10 figures were extracted from the MIT documents; 8 slides show one, e.g. MIT's
  own probability tree on the "trees of cards" solution slide and the base-rate tree.
- **Grounding** (`grounding.json`): vector spaces 0 flagged talking points, probability 1,
  French 12, MIT 8. The flags are lecturer phrasing with little word overlap ("Intuition : …")
  and correct derived numbers (0.0297, 0.33 ≈ 1/3); no invented examples.
- **Length.** The French course is above its 10-minute target because every chapter gets a
  slide; the MIT course is 20 % above, because the model writes longer narration than requested.

## What the first gpt-oss run found, and what was fixed

The courses were run twice. The first run exposed four problems, fixed before the second:

| Problem in the first run | Fix | Second run |
|---|---|---|
| Invented examples with their own numbers (a card example, an urn with 70 % red balls) | prompt rule "no example rather than an invented one" and a soft check on `Example:` talking points | none |
| A chapter without a slide (French course, 10-minute target, 3 exercises) | every numbered chapter gets at least one slide in the length budget | all 4 chapters |
| `\mathbf u` without braces not rendered (8 equations) | normalised before rendering | 0 failures |
| LaTeX in titles and bullets (`Vectors in \(\mathbb{R}^n\)`) | prompt asks for plain text; leftovers shown as ℝⁿ, ∩, 1/6 | 0 |

Two display issues found in the second run were fixed without a new LLM call (the outputs were
re-rendered): a `\begin{cases}` pmf is now drawn as stacked rows, and the grounding check reads
French decimal commas.

## Parsing time

Docling with formula decoding, on a laptop CPU (Apple M3), cached by content afterwards:

| Document | Time |
|---|---|
| Vector spaces (2 pages) | 4 min |
| Probability (3 pages) | 7 min |
| MIT Problem Set 2 (3 pages) | 3 s |
| MIT Problem Set 2 solutions (6 pages) | 16 min |
| MIT Reading 3 (12 pages) | 28 min |

## Run it yourself

```bash
make setup-full
export GPTOSS_BASE_URL=http://<server>:<port>/v1
read -s "GPTOSS_API_KEY?API key: "; export GPTOSS_API_KEY
./scripts/run_gpt_oss_eval.sh
```

Or step by step, with the lecturer review in between:

```bash
course2video run examples/cours_probabilites --out out/run1 --config configs/gpt-oss-120b-8k.yaml \
    --base-url "$GPTOSS_BASE_URL" --model gpt-oss-120b
# review and edit out/run1/slides.md
course2video continue out/run1 --from md
```

Edits that cannot be placed are rejected with their line number, and nothing is narrated until
the review passes. To change the layout later without calling the LLM again:
`course2video render out/run1`.

These are four runs on openly licensed material, with slides approved as generated. They show
that the pipeline works end to end with an open-weight model on premises; they are **not** a
quality evaluation. For that, see [`../eval/rubric.md`](../eval/rubric.md).
