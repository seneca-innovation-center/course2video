from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path

from ..config import LectureConfig
from ..script.models import Script
from ..slides.models import Deck, Slide

TEMPLATES = {
    "en": {
        "part": "Part", "of": "of", "outline": "Outline", "summary": "Summary",
        "thanks": "Thank you for watching",
        "welcome": "Welcome. In this lecture we study {title}.",
        "presenter": " Presented by {presenter}.",
        "agenda": "Here is the plan. We will go through {n} parts: {items}.",
        "first_section": "Let's start with part {i}: {name}.",
        "section": "Now we move on to part {i}: {name}.",
        "problem_section": "Part {i}. Time to practise with {doc}: {title}. "
                           "Try it yourself before we look at the solution.",
        "exercise": "Exercise", "solution": "Solution",
        "closing": "That brings us to the end of this lecture. We covered {items}. "
                   "Thank you for watching.",
        "and": "and", "intro": "Introduction",
    },
    "fr": {
        "part": "Partie", "of": "sur", "outline": "Plan", "summary": "Résumé",
        "thanks": "Merci de votre attention",
        "welcome": "Bienvenue. Dans ce cours, nous étudions {title}.",
        "presenter": " Présenté par {presenter}.",
        "agenda": "Voici le plan. Nous allons voir {n} parties : {items}.",
        "first_section": "Commençons par la partie {i} : {name}.",
        "section": "Passons à la partie {i} : {name}.",
        "problem_section": "Partie {i}. Entraînons-nous avec {doc} : {title}. "
                           "Essayez de le résoudre avant de regarder la correction.",
        "exercise": "Exercice", "solution": "Correction",
        "closing": "Nous arrivons à la fin de ce cours. Nous avons vu {items}. "
                   "Merci de votre attention.",
        "and": "et", "intro": "Introduction",
    },
    "es": {
        "part": "Parte", "of": "de", "outline": "Índice", "summary": "Resumen",
        "thanks": "Gracias por su atención",
        "welcome": "Bienvenidos. En esta clase estudiamos {title}.",
        "presenter": " Presentado por {presenter}.",
        "agenda": "Este es el plan. Veremos {n} partes: {items}.",
        "first_section": "Empecemos con la parte {i}: {name}.",
        "section": "Pasamos a la parte {i}: {name}.",
        "problem_section": "Parte {i}. Practiquemos con {doc}: {title}. "
                           "Inténtelo antes de ver la solución.",
        "exercise": "Ejercicio", "solution": "Solución",
        "closing": "Llegamos al final de esta clase. Hemos visto {items}. "
                   "Gracias por su atención.",
        "and": "y", "intro": "Introducción",
    },
}


@dataclass
class Section:
    name: str
    slide_ids: list[int] = field(default_factory=list)


@dataclass
class Frame:
    kind: str
    narration: str
    heading: str = ""
    items: list[str] = field(default_factory=list)
    slide: Slide | None = None
    section_index: int | None = None
    index: int = 0
    total: int = 0


def templates(language: str) -> dict[str, str]:
    return TEMPLATES.get(language.split("-")[0].lower(), TEMPLATES["en"])


def display_section_name(raw: str) -> str:
    name = re.sub(r"^[#\s]*", "", raw)
    name = re.sub(r"^(chapter|section|part)?\s*\d+(\.\d+)*[.):]?\s+", "", name, flags=re.I)
    return name.strip() or raw.strip()


def speakable(text: str) -> str:
    text = re.sub(r"(\w)\^\{?(\w+)\}?", r"\1 \2", text)
    return text.replace("_", " ")


def _join(items: list[str], and_word: str) -> str:
    if len(items) <= 1:
        return "".join(items)
    return ", ".join(items[:-1]) + f" {and_word} " + items[-1]


_TOP_LEVEL = re.compile(r"^[#\s]*(?:chapter|section|part)?\s*\d+(?:[.):]\s*|\s+)(?!\d)", re.I)
_SUB_LEVEL = re.compile(r"^[#\s]*\d+\.\d+")


def group_sections(deck: Deck) -> list[Section]:
    intro = templates(deck.language)["intro"]
    theory = [s.source_section for s in deck.slides if s.kind == "theory" and s.source_section]
    numbered = any(_TOP_LEVEL.match(x) and not _SUB_LEVEL.match(x) for x in theory)
    sections: list[Section] = []
    for s in deck.slides:
        raw = s.source_section
        name = display_section_name(raw) if raw else ""
        if name and name.lower().startswith(deck.title.lower()):
            name = intro
        elif (numbered and s.kind == "theory" and sections and name
              and (_SUB_LEVEL.match(raw) or not _TOP_LEVEL.match(raw))):
            name = ""
        if not sections or (name and name.lower() != sections[-1].name.lower()):
            sections.append(Section(name or intro))
        sections[-1].slide_ids.append(s.id)
    return sections


def build_frames(deck: Deck, script: Script, cfg: LectureConfig) -> list[Frame]:
    t = templates(deck.language)
    sections = group_sections(deck)
    names = [s.name for s in sections]
    structured = len(sections) >= 2
    frames: list[Frame] = []

    if cfg.title_slide:
        narration = t["welcome"].format(title=deck.title)
        if cfg.presenter:
            narration += t["presenter"].format(presenter=cfg.presenter)
        if cfg.subtitle:
            narration += " " + cfg.subtitle.rstrip(".") + "."
        frames.append(Frame("title", speakable(narration), heading=deck.title,
                            items=[x for x in (cfg.subtitle, cfg.presenter, cfg.institution) if x]))
    if cfg.agenda and structured:
        frames.append(Frame("agenda", speakable(t["agenda"].format(
            n=len(names), items=_join(names, t["and"]))), heading=t["outline"], items=names))

    by_id = {s.id: s for s in deck.slides}
    for si, sec in enumerate(sections):
        if cfg.section_dividers and structured:
            first = by_id[sec.slide_ids[0]]
            if first.kind == "exercise":
                ptitle = first.source_section.split(":", 1)[-1].strip()
                text = t["problem_section"].format(i=si + 1, doc=first.source_doc or sec.name,
                                                   title=ptitle)
            else:
                key = "first_section" if si == 0 else "section"
                text = t[key].format(i=si + 1, name=sec.name)
            frames.append(Frame("section", speakable(text),
                                heading=sec.name, items=names, section_index=si))
        for sid in sec.slide_ids:
            frames.append(Frame("content", script.for_slide(sid), heading=by_id[sid].title,
                                slide=by_id[sid], section_index=si if structured else None))

    if cfg.closing:
        frames.append(Frame("closing", speakable(t["closing"].format(items=_join(names, t["and"]))),
                            heading=t["summary"], items=names))

    for i, f in enumerate(frames):
        f.index, f.total = i, len(frames)
    return frames


def section_label(frame: Frame, n_sections: int, language: str) -> str:
    if frame.section_index is None or frame.kind != "content":
        return ""
    t = templates(language)
    return f"{t['part']} {frame.section_index + 1} {t['of']} {n_sections}"


def write_plan(frames: list[Frame], path: Path) -> Path:
    data = []
    for f in frames:
        d = asdict(f)
        d["slide_id"] = f.slide.id if f.slide else None
        d.pop("slide")
        data.append(d)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    return path
