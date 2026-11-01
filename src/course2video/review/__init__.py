from __future__ import annotations

import re
from pathlib import Path

from ..slides.models import Deck, Equation, Slide
from ..slides.validate import check_latex, validate_deck_file

MD_HELP = """<!--
Edit this file to correct the slides, then run:
    course2video continue <out-dir> --from md
Format: '## Slide N: Title', then '- ' bullets, '$$ latex $$' followed by a
'> explanation' line for each equation, optional 'Notes:' and 'Source:' lines.
'Say:' lines are talking points: what the lecturer explains out loud (not shown on the slide).
'Kind:' is theory, exercise or solution; 'From:' names the source document and problem.
Delete a whole '## Slide' block to drop a slide. Slides are renumbered in order.
-->
"""


def deck_to_markdown(deck: Deck) -> str:
    out = [f"# {deck.title}", f"<!-- language: {deck.language} -->", MD_HELP]
    for s in deck.slides:
        out.append(f"## Slide {s.id}: {s.title}")
        out += [f"- {b}" for b in s.bullets]
        for eq in s.equations:
            out += ["", f"$$ {eq.latex} $$", f"> {eq.explanation}"]
        if s.talking_points:
            out.append("")
            out += [f"Say: {tp}" for tp in s.talking_points]
        if s.notes:
            out += ["", f"Notes: {s.notes}"]
        if s.source_section:
            out.append(f"Source: {s.source_section}")
        if s.kind != "theory":
            out.append(f"Kind: {s.kind}")
        if s.source_doc:
            out.append(f"From: {s.source_doc}")
        out.append("")
    return "\n".join(out)


def markdown_to_deck(md: str) -> Deck:
    md = re.sub(r"<!--(?!\s*language:).*?-->", "", md, flags=re.S)
    title_m = re.search(r"(?m)^#\s+(.+)$", md)
    lang_m = re.search(r"<!--\s*language:\s*(\S+)\s*-->", md)
    slides: list[dict] = []
    pending_eq: dict | None = None
    for raw in md.splitlines():
        line = raw.strip()
        h = re.match(r"^##\s+Slide\s+\d+\s*:\s*(.+)$", line)
        if h:
            slides.append({"title": h.group(1).strip(), "bullets": [], "equations": [],
                           "notes": "", "source_section": "", "kind": "theory", "source_doc": "",
                           "talking_points": []})
            pending_eq = None
            continue
        if not slides or not line:
            continue
        cur = slides[-1]
        eq = re.match(r"^\$\$\s*(.+?)\s*\$\$$", line)
        if eq:
            pending_eq = {"latex": eq.group(1), "explanation": ""}
            cur["equations"].append(pending_eq)
        elif line.startswith(">") and pending_eq is not None:
            pending_eq["explanation"] = (pending_eq["explanation"] + " " + line[1:].strip()).strip()
        elif line.startswith("- ") or line.startswith("* "):
            cur["bullets"].append(line[2:].strip())
        elif line.startswith("Notes:"):
            cur["notes"] = line[6:].strip()
        elif line.startswith("Source:"):
            cur["source_section"] = line[7:].strip()
        elif line.startswith("Say:"):
            cur["talking_points"].append(line[4:].strip())
        elif line.startswith("Kind:"):
            cur["kind"] = line[5:].strip().lower()
        elif line.startswith("From:"):
            cur["source_doc"] = line[5:].strip()
    deck_slides = []
    for i, s in enumerate(slides, start=1):
        deck_slides.append(
            Slide(id=i, title=s["title"], bullets=s["bullets"],
                  equations=[Equation(**e) for e in s["equations"]],
                  notes=s["notes"], source_section=s["source_section"],
                  kind=s["kind"], source_doc=s["source_doc"],
                  talking_points=s["talking_points"])
        )
    return Deck(
        title=title_m.group(1).strip() if title_m else "Untitled",
        language=lang_m.group(1) if lang_m else "en",
        slides=deck_slides,
    )


def export_for_review(deck: Deck, out_dir: Path) -> tuple[Path, Path]:
    j = out_dir / "slides.json"
    m = out_dir / "slides.md"
    j.write_text(deck.model_dump_json(indent=2), encoding="utf-8")
    m.write_text(deck_to_markdown(deck), encoding="utf-8")
    return j, m


class ReviewError(ValueError):
    pass


def import_reviewed(out_dir: Path, source: str = "json") -> Deck:
    if source == "md":
        try:
            deck = markdown_to_deck((out_dir / "slides.md").read_text(encoding="utf-8"))
        except ValueError as e:
            raise ReviewError(f"slides.md is invalid:\n{e}") from e
        problems = check_latex(deck)
        if problems:
            raise ReviewError("slides.md is invalid:\n" + "\n".join(problems))
    else:
        deck, errors = validate_deck_file((out_dir / "slides.json").read_text(encoding="utf-8"))
        if deck is None:
            raise ReviewError("slides.json is invalid:\n" + "\n".join(errors))
    deck.approved = True
    (out_dir / "slides.json").write_text(deck.model_dump_json(indent=2), encoding="utf-8")
    (out_dir / "slides.md").write_text(deck_to_markdown(deck), encoding="utf-8")
    return deck
