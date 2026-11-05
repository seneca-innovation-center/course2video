from __future__ import annotations

import re
from fractions import Fraction

from ..script.alignment import content_words
from .models import Deck

MIN_OVERLAP = 0.25
SMALL = {Fraction(n) for n in range(0, 11)}

_FRAC = re.compile(r"\\[dt]?frac\s*\{\s*([\d.\s]+)\}\s*\{\s*([\d.\s]+)\}")
_NUM = re.compile(r"(?<![\w.])(\d+(?:\.\d+)?)(?:\s*/\s*(\d+)(?!\d|\.\d))?(\s*\\?%)?")


def _normalise(text: str) -> str:
    text = _FRAC.sub(lambda m: f"{m.group(1).replace(' ', '')}/{m.group(2).replace(' ', '')}", text)
    text = re.sub(r"(?<=\d)\s+(?=[\d.])|(?<=\.)\s+(?=\d)", "", text)
    return text


DECIMAL_COMMA = {"fr", "es", "de", "it", "pt", "nl"}


def numbers(text: str, decimal_comma: bool = False) -> set[Fraction]:
    out = set()
    if decimal_comma:
        text = re.sub(r"(?<![\d,])(\d+),(\d+)(?![\d,])", r"\1.\2", text)
    for m in _NUM.finditer(_normalise(text)):
        try:
            a = Fraction(m.group(1))
            out.add(a)
            if m.group(2) and "." not in m.group(1):
                b = Fraction(m.group(2))
                out.add(b)
                if b:
                    out.add(a / b)
            if m.group(3):
                out.add(a / 100)
        except (ValueError, ZeroDivisionError):
            continue
    return out


def check_grounding(deck: Deck, lecture_md: str, problem_texts: dict[str, str]) -> dict:
    dc = (deck.language or "en").split("-")[0].lower() in DECIMAL_COMMA
    lecture = (content_words(lecture_md), numbers(lecture_md, dc))
    problems = {ref: (content_words(t), numbers(t, dc)) for ref, t in problem_texts.items()}
    slides, flagged, scores = [], [], []
    for s in deck.slides:
        if s.kind != "theory" and s.source_doc not in problems:
            slides.append({"slide_id": s.id, "kind": s.kind, "talking_points": [],
                           "status": "source text not available"})
            continue
        src_words, src_nums = lecture if s.kind == "theory" else problems[s.source_doc]
        items = []
        for tp in s.talking_points:
            words = content_words(tp)
            overlap = len(words & src_words) / len(words) if words else 1.0
            unsupported = sorted(str(n) for n in numbers(tp, dc) - src_nums - SMALL)
            items.append({
                "text": tp,
                "overlap": round(overlap, 3),
                "numbers_not_in_source": unsupported,
                "flagged": overlap < MIN_OVERLAP or bool(unsupported),
            })
            scores.append(overlap)
        if any(i["flagged"] for i in items):
            flagged.append(s.id)
        slides.append({"slide_id": s.id, "kind": s.kind, "talking_points": items})
    return {
        "method": "numbers must occur in the source (by value); word overlap with the source "
                  f"must be at least {MIN_OVERLAP}",
        "mean_overlap": round(sum(scores) / len(scores), 3) if scores else None,
        "flagged_slides": flagged,
        "slides": slides,
    }
