from __future__ import annotations

import json

from ..config import ScriptConfig
from ..llm.base import LLMBackend
from ..slides.models import Deck
from ..slides.validate import Attempt, generate_validated
from .models import Script

SYSTEM = """You are a university professor recording a lecture. For each slide, write what
you SAY while the slide is on screen.

The slide shows only key points. Do NOT read the bullets out: viewers can see them, and
narration that repeats on-screen text hurts learning. Use the bullets as your outline and
explain them, mainly by developing the slide's `talking_points`. Teach like this:
- Open with the question or problem the slide answers, or a short story that sets it up.
- Explain the intuition in plain words before or after the formal statement.
- Work through the example (talking points starting with "Example:") step by step with its
  numbers, as you would at the board: "So we take 0.05 times 0.99, which gives ...".
- Ask the viewer a question now and then, and answer it ("Can we get P(B) from this? Yes ...").
- Point out the common mistake or subtle point when there is one.
- Read formulas aloud the way you would say them; never output raw LaTeX.
- If a slide has `figure_on_screen`, that figure is shown next to the bullets: point the viewer
  to it and explain what it shows, using only the slide and its talking points.
- End with one sentence that sums up the idea or leads to the next slide.

Rules:
- Use ONLY what is on the slide and in its talking points. Do not add facts, examples or
  numbers of your own.
- Plain spoken prose: no markdown, no bullet characters, no headings.
- Length: about {words} words per slide, never more than {hi}.
- The video already has its own welcome, outline, "Part N" announcements and closing. Do NOT
  greet or say goodbye. Link each slide to the previous one in a natural way.
- `kind` "exercise": present the problem and what makes it interesting, then invite the viewer
  to pause the video and try it. `kind` "solution": explain why each step is taken, then state
  the result clearly. Mention `source_doc` (e.g. "problem 2 of problem set 2") the first time.
- Answer with a single JSON object and nothing else."""

PROMPT = """Write the narration for these slides of the course "{title}" in language: {language}.
Return one entry per slide, using the same slide ids: {ids}.
{previous}

<slides>
{slides_json}
</slides>"""


def generate_script(
    llm: LLMBackend, deck: Deck, cfg: ScriptConfig, words_per_slide: int | None = None,
    figures: dict[str, str] | None = None,
) -> tuple[Script, list[list[Attempt]]]:
    if not deck.approved:
        raise PermissionError("deck is not approved; run the review step first")
    entries = []
    attempt_log: list[list[Attempt]] = []
    n = max(1, cfg.slides_per_call)
    for i in range(0, len(deck.slides), n):
        batch = deck.slides[i : i + n]
        ids = [s.id for s in batch]
        dumped = []
        for s in batch:
            d = s.model_dump(exclude={"notes", "figure"})
            if s.figure:
                d["figure_on_screen"] = (figures or {}).get(s.figure) or "a figure from the source"
            dumped.append(d)
        slides_json = json.dumps(
            dumped,
            ensure_ascii=False,
            indent=1,
        )
        previous = (
            f'The previous slide (already narrated) was titled "{deck.slides[i - 1].title}".'
            if i > 0 else "These are the first slides of the lecture, right after the outline."
        )

        w = words_per_slide or cfg.words_per_slide
        limit = int(w * 1.2)

        def ids_match(script: Script, expected=ids) -> list[str]:
            got = [e.slide_id for e in script.slides]
            if sorted(got) != sorted(expected):
                return [f"slide ids must be exactly {expected}, got {got}"]
            return []

        def length(script: Script, w=w, limit=limit) -> list[str]:
            counts = [len(e.text.split()) for e in script.slides]
            mean = sum(counts) / len(counts)
            if mean <= limit:
                return []
            cut = round(100 * (1 - w / mean))
            return [f"narration averages {mean:.0f} words per slide; the budget is about {w}. "
                    f"Shorten every slide by about {cut}% while keeping its example, its "
                    "question to the viewer and its numbers"]

        part, attempts = generate_validated(
            llm,
            system=SYSTEM.format(words=w, hi=int(w * 1.15)),
            prompt=PROMPT.format(
                title=deck.title, language=deck.language, ids=ids, slides_json=slides_json,
                previous=previous,
            ),
            model_cls=Script,
            task="script",
            max_retries=cfg.max_retries,
            extra_checks=ids_match,
            soft_checks=length,
        )
        attempt_log.append(attempts)
        entries.extend(sorted(part.slides, key=lambda e: e.slide_id))
    return Script(slides=entries), attempt_log
