# Manual review rubric (0-2)

Use this to compare runs (for example the development runs against gpt-oss-120b, or gpt-oss-120b against gpt-oss-20b) on the
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
