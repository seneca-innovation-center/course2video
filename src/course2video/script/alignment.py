from __future__ import annotations

import re
from typing import Any

from ..config import AlignmentConfig
from ..slides.models import Deck
from .models import Script

_STOPWORDS = set(
    """a an the and or of to in on for with by from at as is are was were be been being this
    that these those it its we our you your they their he she his her them there here which
    who whom what when where why how not no can may might must shall should will would do does
    did done has have had any all each every some such than then also into onto over under
    between about after before more most less least very just only so if but because while
    let lets one two le la les des du de et un une est en au aux pour par sur dans que qui""".split()
)


def content_words(text: str) -> set[str]:
    words = re.findall(r"[^\W_]+", text.lower())
    out = set()
    for w in words:
        if len(w) < 3 or w in _STOPWORDS:
            continue
        if len(w) > 4 and w.endswith("s") and not w.endswith("ss"):
            w = w[:-1]
        out.add(w)
    return out


def item_score(item: str, script_words: set[str]) -> float:
    words = content_words(item)
    if not words:
        return 1.0
    return len(words & script_words) / len(words)


def check_alignment(deck: Deck, script: Script, cfg: AlignmentConfig) -> dict[str, Any]:
    per_slide = []
    total_items = 0
    total_covered = 0
    for slide in deck.slides:
        try:
            text = script.for_slide(slide.id)
        except KeyError:
            text = ""
        sw = content_words(text)
        items = ([("bullet", b) for b in slide.bullets]
                 + [("equation", e.explanation) for e in slide.equations]
                 + [("talking_point", t) for t in slide.talking_points])
        results = []
        for kind, item in items:
            score = item_score(item, sw)
            results.append(
                {
                    "kind": kind,
                    "text": item,
                    "score": round(score, 3),
                    "covered": score >= cfg.item_threshold,
                }
            )
        covered = sum(r["covered"] for r in results)
        coverage = covered / len(results) if results else 1.0
        slide_words = content_words(" ".join([slide.title] + [i for _, i in items]))
        novel = len(sw - slide_words) / len(sw) if sw else 0.0
        per_slide.append(
            {
                "slide_id": slide.id,
                "title": slide.title,
                "coverage": round(coverage, 3),
                "flagged": coverage < cfg.slide_warn_below,
                "novel_word_ratio": round(novel, 3),
                "items": results,
            }
        )
        total_items += len(results)
        total_covered += covered
    slide_words = sum(len(" ".join(s.bullets + [s.title]).split()) for s in deck.slides)
    spoken_words = sum(len(e.text.split()) for e in script.slides)
    return {
        "method": "lexical content-word overlap (v0)",
        "spoken_to_slide_word_ratio": round(spoken_words / slide_words, 1) if slide_words else None,
        "item_threshold": cfg.item_threshold,
        "slide_warn_below": cfg.slide_warn_below,
        "overall_coverage": round(total_covered / total_items, 3) if total_items else 1.0,
        "flagged_slides": [s["slide_id"] for s in per_slide if s["flagged"]],
        "slides": per_slide,
    }
