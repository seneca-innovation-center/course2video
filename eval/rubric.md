# Manual review rubric (0-2)

Use this to compare runs (for example gpt-oss-120b against gpt-oss-20b, or two versions of the prompts) on the
same source material. Two reviewers score independently; report the disagreements as well
as the averages.

**Define "accurate" before scoring:** a statement is accurate if it is supported by the
source document **and** keeps its notation. Correct-sounding facts that are not in the
source count as *not supported*.

## Per slide

| Criterion | 0 | 1 | 2 |
|---|---|---|---|
| **Factual accuracy** | at least one statement is wrong or unsupported by the source | minor imprecision, nothing wrong | every statement is supported by the source |
| **Completeness** | a key idea of the section is missing | minor omission | the section's key ideas are all there |
| **Formula correctness** | a formula is wrong, or notation differs from the source | correct but badly typeset or partly explained | correct, same notation, explained in words |
| **Clarity** | hard to follow, overloaded | understandable with effort | clear, one idea per bullet |

## Per slide: narration

| Criterion | 0 | 1 | 2 |
|---|---|---|---|
| **Faithfulness to slide** | adds facts that are not on the slide | small additions (examples, transitions) | only what is on the slide |
| **Equation reading** | reads raw LaTeX or misreads | understandable but awkward | natural spoken form |

## Per run

- Number of slides scored, reviewers, date, LLM backend and model, parser
- Mean score per criterion and per reviewer; inter-reviewer disagreements (count, examples)
- `alignment.json` overall coverage and flagged slides: do they agree with the human scores?
- Retry attempts (`meta.json`) and wall-clock time per stage
- Lecturer time to review and correct, compared with making the slides by hand

## Score sheet template

| Slide | Accuracy | Completeness | Formulas | Clarity | Faithfulness | Equation reading | Comment |
|---|---|---|---|---|---|---|---|
| 1 | | | | | | | |

## Running a scoring session

1. Each reviewer copies `eval/templates/score_sheet.csv`, one row per slide of the run
   (`slide_id` as in `slides.md`), and scores each criterion 0, 1 or 2 (empty if not
   applicable, e.g. `formulas` on a slide without formulas).
2. The lecturer who reviews the slides records time and corrections in a copy of
   `eval/templates/review_log.csv`, with an estimate of the time to make the same material by
   hand.
3. Produce the report:

```bash
course2video score anna.csv mohamed.csv --out out/run1 --review-log review_log.csv \
    --report eval/results/run1.md
```

The report gives the mean per criterion and per reviewer, agreement and Cohen's kappa, the
slides where reviewers disagree, whether the slides flagged by `grounding.json` /
`alignment.json` scored lower than the others, and the review time.
