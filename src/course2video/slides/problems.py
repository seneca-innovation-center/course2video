from __future__ import annotations

from ..course.linking import Problem
from ..llm.base import LLMBackend
from .models import SlideBatch
from .validate import (
    Attempt,
    check_figures,
    check_latex,
    check_lecture_style,
    generate_validated,
)

SYSTEM = """You turn one exercise and its OFFICIAL solution into slides for a worked example
in a recorded lecture.
Rules:
- The first slide has kind "exercise": the problem statement, faithful to the source,
  shortened if needed. It must not reveal the answer.
- The following slides have kind "solution": follow the official solution step by step,
  with the same method, the same numbers and the same final answers. Do not invent another
  method and do not add results that are not in the official solution.
- Slides show only key points: a short title and 2-4 bullets of at most 12 words each
  (keywords, givens, the result), plus key formulas in `equations` as LaTeX without $
  delimiters, each with a plain-language explanation. Keep the source's notation.
- Everything the professor says goes in `talking_points` (3-6 per slide): on the exercise
  slide, what the problem is really asking and what makes it tricky (without the answer);
  on solution slides, WHY each step of the official solution is done, the numbers worked
  through, and how to check the result. Only use what the official solution supports.
- If the exercise or the solution contains a figure ([Figure F3: caption]), put its id in
  `figure` on the slide it belongs to and explain it in the talking points. Never use an id
  that is not in the text.
- Answer with a single JSON object and nothing else."""

PROMPT = """Make exactly {n_slides} slides for this problem from {ref}: 1 "exercise" slide, then
{n_solution} "solution" slide(s). Write in language: {language}.
If the problem has several parts, cover at most the parts that fit; say which parts on the slides.

<exercise>
{statement}
</exercise>

<official_solution>
{solution}
</official_solution>"""


def _check_kinds(batch: SlideBatch, source: str = "") -> list[str]:
    kinds = [s.kind for s in batch.slides]
    errors = []
    if not kinds or kinds[0] != "exercise":
        errors.append('the first slide must have kind "exercise"')
    if "solution" not in kinds:
        errors.append('at least one slide must have kind "solution"')
    if "theory" in kinds:
        errors.append('use only kinds "exercise" and "solution" here')
    return errors + check_latex(batch) + check_lecture_style(batch, 12) + check_figures(batch, source)


def generate_problem_slides(
    llm: LLMBackend, problem: Problem, *, n_slides: int, language: str, max_retries: int
) -> tuple[SlideBatch, list[Attempt]]:
    if not problem.solution:
        raise ValueError(f"{problem.ref} has no linked solution")
    batch, attempts = generate_validated(
        llm,
        system=SYSTEM,
        prompt=PROMPT.format(n_slides=n_slides, n_solution=n_slides - 1, ref=problem.ref,
                             language=language, statement=problem.statement,
                             solution=problem.solution),
        model_cls=SlideBatch,
        task="problem",
        max_retries=max_retries,
        extra_checks=lambda b: _check_kinds(b, problem.statement + "\n" + problem.solution),
    )
    for s in batch.slides:
        s.source_section = f"Worked {problem.display_title}"
        s.source_doc = problem.ref
    return batch, attempts
