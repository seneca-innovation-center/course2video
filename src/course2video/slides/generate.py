from __future__ import annotations

import re

from ..config import SlidesConfig
from ..llm.base import LLMBackend
from .models import Deck, SlideBatch
from .validate import Attempt, check_latex, check_lecture_style, generate_validated

SYSTEM = """You prepare a university lecture from course material: the slides a professor
shows AND the talking points the professor explains while each slide is on screen.

How good lecturers use slides (follow this):
- The slide shows only the key points: a short title and 2-4 bullets of at most
  {max_bullet_words} words each, written as keywords or short phrases, not sentences.
  Formulas go in `equations` (LaTeX without $ delimiters) with a plain-language explanation.
- Everything else is SAID, not written. Put it in `talking_points` (3-6 per slide), each a
  sentence or two the professor will develop out loud:
    * why this idea matters / the question it answers;
    * the intuition behind the definition or formula;
    * a concrete example FROM THE SOURCE, with its numbers, worked step by step
      (start that point with "Example:");
    * a common mistake or a subtle point the source warns about;
    * how it connects to the previous or next idea.
- Prefer fewer, richer slides: each slide is on screen for over a minute while the
  professor explains it.

Rules:
- Use only facts, examples and numbers present in the source document. Do not add outside
  knowledge, examples or numbers of your own.
- Follow the document's order. Sub-sections may share a slide with their chapter.
- Keep notation exactly as in the source.
- `source_section` is the exact heading text of the section the slide comes from.
- Answer with a single JSON object and nothing else."""

PROMPT = """Create at most {max_slides} slides for the following part of the course "{title}".
Number slides from 1. Write in language: {language}.

<document>
{chunk}
</document>"""


def chunk_markdown(md: str, max_chars: int) -> list[str]:
    sections = re.split(r"(?m)^(?=#{1,3}\s)", md)
    chunks: list[str] = []
    current = ""
    for sec in sections:
        if not sec.strip():
            continue
        if current and len(current) + len(sec) > max_chars:
            chunks.append(current)
            current = ""
        current += sec
    if current.strip():
        chunks.append(current)
    return chunks


def guess_title(md: str, fallback: str) -> str:
    m = re.search(r"(?m)^#{1,2}\s+(.+)$", md)
    return m.group(1).strip() if m else fallback


def chapter_map(md: str) -> dict[str, str]:
    from ..render.lecture import _SUB_LEVEL, _TOP_LEVEL, display_section_name

    headings = re.findall(r"(?m)^#{1,3}\s+(.+?)\s*$", md)
    numbered = any(_TOP_LEVEL.match(h) and not _SUB_LEVEL.match(h) for h in headings)
    out: dict[str, str] = {}
    current = None
    for h in headings:
        if numbered and _TOP_LEVEL.match(h) and not _SUB_LEVEL.match(h):
            current = h
        chapter = (current or h) if numbered else h
        out.setdefault(display_section_name(h).lower(), chapter)
    return out


def assign_chapters(slides, md: str) -> None:
    from ..render.lecture import display_section_name

    chapters = chapter_map(md)
    for s in slides:
        key = display_section_name(s.source_section).lower() if s.source_section else ""
        if key in chapters:
            s.source_section = chapters[key]


def generate_deck(
    llm: LLMBackend,
    markdown: str,
    cfg: SlidesConfig,
    *,
    title: str,
    language: str = "en",
    total_slides: int | None = None,
) -> tuple[Deck, list[list[Attempt]]]:
    from ..course.budget import slides_per_chunk

    chunks = chunk_markdown(markdown, cfg.chunk_chars)
    if total_slides:
        limits = slides_per_chunk(total_slides, [len(c) for c in chunks])
    else:
        limits = [cfg.max_slides_per_chunk] * len(chunks)
    all_slides = []
    attempt_log: list[list[Attempt]] = []
    for chunk, limit in zip(chunks, limits, strict=True):
        prompt = PROMPT.format(max_slides=limit, title=title, language=language, chunk=chunk)
        if total_slides:
            prompt += f"\nAim for about {limit} slides: this part is planned to fill that much time."
        batch, attempts = generate_validated(
            llm,
            system=SYSTEM.format(max_bullet_words=cfg.max_bullet_words),
            prompt=prompt,
            model_cls=SlideBatch,
            task="slides",
            max_retries=cfg.max_retries,
            extra_checks=lambda b: check_latex(b) + check_lecture_style(b, cfg.max_bullet_words),
        )
        attempt_log.append(attempts)
        for sl in batch.slides:
            sl.kind = "theory"
            sl.source_doc = ""
        all_slides.extend(batch.slides)
    assign_chapters(all_slides, markdown)
    for i, sl in enumerate(all_slides, start=1):
        sl.id = i
    return Deck(title=title, language=language, slides=all_slides), attempt_log
