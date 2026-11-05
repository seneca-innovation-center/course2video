from __future__ import annotations

import json
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
'Figure:' shows a source figure on the slide (ids in figures/figures.json); delete the line to remove it.
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
        if s.figure:
            out.append(f"Figure: {s.figure}")
        if s.kind != "theory":
            out.append(f"Kind: {s.kind}")
        if s.source_doc:
            out.append(f"From: {s.source_doc}")
        out.append("")
    return "\n".join(out)


def markdown_to_deck(md: str) -> Deck:
    md = re.sub(r"<!--(?!\s*language:).*?-->", lambda m: "\n" * m.group(0).count("\n"), md,
                flags=re.S)
    title_m = re.search(r"(?m)^#\s+(.+)$", md)
    lang_m = re.search(r"<!--\s*language:\s*(\S+)\s*-->", md)
    slides: list[dict] = []
    errors: list[str] = []
    last: tuple | None = None
    eq_lines: list[str] | None = None
    eq_start = 0

    def add_equation(cur: dict, latex: str) -> tuple:
        eq = {"latex": latex.strip(), "explanation": ""}
        cur["equations"].append(eq)
        return ("explanation", eq)

    for n, raw in enumerate(md.splitlines(), start=1):
        line = raw.strip()
        if eq_lines is not None:
            if line.endswith("$$"):
                eq_lines.append(line[:-2])
                last = add_equation(slides[-1], " ".join(x for x in eq_lines if x.strip()))
                eq_lines = None
            else:
                eq_lines.append(line)
            continue
        h = re.match(r"^##\s+Slide\s+\d+\s*:\s*(.+)$", line)
        if h:
            slides.append({"title": h.group(1).strip(), "bullets": [], "equations": [],
                           "notes": "", "source_section": "", "kind": "theory", "source_doc": "",
                           "talking_points": [], "figure": ""})
            last = None
            continue
        if not line:
            last = None
            continue
        if not slides and (line.startswith("# ") or line.startswith("<!--")):
            continue
        if not slides:
            errors.append(f"line {n}: text before the first '## Slide' heading: {line[:60]!r}")
            continue
        cur = slides[-1]
        if line.startswith("#"):
            errors.append(f"line {n}: headings are not allowed inside a slide: {line[:60]!r}")
            last = None
            continue
        bullet = re.match(r"^(?:[-*]|\d+[.)])\s+(.*)$", line)
        if line.startswith("$$") and line.endswith("$$") and len(line) > 4:
            last = add_equation(cur, line[2:-2])
        elif line.startswith("$$"):
            eq_lines, eq_start = [line[2:]], n
        elif line.startswith(">"):
            if last and last[0] == "explanation":
                eq = last[1]
                eq["explanation"] = (eq["explanation"] + " " + line[1:].strip()).strip()
            else:
                errors.append(f"line {n}: '>' explanation without an equation above it")
        elif bullet:
            cur["bullets"].append(bullet.group(1).strip())
            last = ("bullets", len(cur["bullets"]) - 1)
        elif line.startswith("Say:"):
            cur["talking_points"].append(line[4:].strip())
            last = ("talking_points", len(cur["talking_points"]) - 1)
        elif line.startswith("Notes:"):
            cur["notes"] = line[6:].strip()
            last = ("notes",)
        elif line.startswith("Source:"):
            cur["source_section"] = line[7:].strip()
            last = None
        elif line.startswith("Figure:"):
            cur["figure"] = (line[7:].split() or [""])[0]
            last = None
        elif line.startswith("Kind:"):
            cur["kind"] = line[5:].strip().lower()
            last = None
        elif line.startswith("From:"):
            cur["source_doc"] = line[5:].strip()
            last = None
        elif last and last[0] in ("bullets", "talking_points"):
            items = cur[last[0]]
            items[last[1]] = f"{items[last[1]]} {line}"
        elif last and last[0] == "notes":
            cur["notes"] = f"{cur['notes']} {line}".strip()
        elif last and last[0] == "explanation":
            last[1]["explanation"] = f"{last[1]['explanation']} {line}".strip()
        else:
            errors.append(f"line {n}: not understood (start it with '- ', 'Say:', 'Notes:', "
                          f"'$$' or '>'): {line[:60]!r}")
    if eq_lines is not None:
        errors.append(f"line {eq_start}: equation opened with '$$' is never closed")
    if errors:
        raise ReviewError("these lines would be lost, so nothing was changed:\n" + "\n".join(errors))

    deck_slides = []
    for i, s in enumerate(slides, start=1):
        deck_slides.append(
            Slide(id=i, title=s["title"], bullets=s["bullets"],
                  equations=[Equation(**e) for e in s["equations"]],
                  notes=s["notes"], source_section=s["source_section"],
                  kind=s["kind"], source_doc=s["source_doc"],
                  talking_points=s["talking_points"], figure=s["figure"])
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
    figures_file = out_dir / "figures" / "figures.json"
    known = set(json.loads(figures_file.read_text()).keys()) if figures_file.exists() else set()
    unknown = [f"slide {sl.id}: figure {sl.figure!r} does not exist (known: {sorted(known) or 'none'})"
               for sl in deck.slides if sl.figure and sl.figure not in known]
    if unknown:
        raise ReviewError("slides refer to unknown figures:\n" + "\n".join(unknown))
    deck.approved = True
    (out_dir / "slides.json").write_text(deck.model_dump_json(indent=2), encoding="utf-8")
    (out_dir / "slides.md").write_text(deck_to_markdown(deck), encoding="utf-8")
    return deck
