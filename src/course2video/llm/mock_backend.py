from __future__ import annotations

import json
import re
from typing import Any

from .base import LLMBackend

_DOC_RE = re.compile(r"<document>\n?(.*?)\n?</document>", re.S)
_SLIDES_RE = re.compile(r"<slides>\n?(.*?)\n?</slides>", re.S)
_EX_RE = re.compile(r"<exercise>\n?(.*?)\n?</exercise>", re.S)
_SOL_RE = re.compile(r"<official_solution>\n?(.*?)\n?</official_solution>", re.S)
_N_RE = re.compile(r"Make exactly (\d+) slides")


class MockBackend(LLMBackend):
    name = "mock"

    def __init__(self, responses: list[Any] | None = None, max_slides: int = 6) -> None:
        self.responses = list(responses) if responses is not None else None
        self.max_slides = max_slides
        self.calls: list[dict[str, str]] = []

    def complete(self, system, prompt, *, schema=None, task=""):
        self.calls.append({"task": task, "prompt": prompt})
        if self.responses is not None:
            if not self.responses:
                raise AssertionError("MockBackend ran out of scripted responses")
            item = self.responses.pop(0)
            if isinstance(item, BaseException):
                raise item
            return item if isinstance(item, str) else json.dumps(item)
        if task == "slides":
            return json.dumps(self._slides(prompt))
        if task == "script":
            return json.dumps(self._script(prompt))
        if task == "problem":
            return json.dumps(self._problem(prompt))
        raise ValueError(f"MockBackend has no heuristic for task {task!r}")

    def _slides(self, prompt: str) -> dict:
        m = _DOC_RE.search(prompt)
        doc = m.group(1) if m else prompt
        sections = _split_sections(doc)
        slides = []
        for title, body in sections[: self.max_slides]:
            equations = []
            text_lines = []
            for line in body.splitlines():
                eq = re.match(r"\s*\$\$\s*(.+?)\s*\$\$\s*$", line) or re.match(
                    r"\s*(.+=.+?)\s+\(\d+\)\s*$", line
                )
                if eq and len(equations) < 2:
                    latex = eq.group(1).strip()
                    equations.append(
                        {"latex": latex, "explanation": f"This equation states that {latex}."}
                    )
                elif "[Figure " not in line:
                    text_lines.append(line)
            fig = re.search(r"\[Figure (F\d+):", body)
            sentences = _sentences(" ".join(text_lines))
            bullets = [" ".join(s.split()[:10]) for s in sentences[:3]] or [title]
            talking = sentences[:5] or [title, title]
            slides.append(
                {
                    "id": len(slides) + 1,
                    "title": title[:120],
                    "bullets": bullets,
                    "equations": equations,
                    "figure": fig.group(1) if fig else "",
                    "talking_points": talking if len(talking) >= 2 else talking * 2,
                    "notes": "",
                    "source_section": title,
                }
            )
        if not slides:
            slides = [{"id": 1, "title": "Overview", "bullets": ["(empty document)"],
                       "equations": [], "notes": "", "source_section": ""}]
        return {"slides": slides}

    def _problem(self, prompt: str) -> dict:
        ex = _sentences(_EX_RE.search(prompt).group(1))
        sol = _sentences(_SOL_RE.search(prompt).group(1))
        n = int(_N_RE.search(prompt).group(1))
        slides = [{"id": 1, "kind": "exercise", "title": "Exercise",
                   "bullets": [" ".join(x.split()[:10]) for x in ex[:3]] or ["(no statement)"],
                   "talking_points": (ex[:4] + ["Try it before the solution."] * 2)[:max(2, len(ex[:4]))]}]
        per = max(1, len(sol) // max(1, n - 1))
        for k in range(n - 1):
            part = sol[k * per:(k + 1) * per][:4] or sol[-1:] or ["(no solution)"]
            slides.append({"id": k + 2, "kind": "solution", "title": f"Solution, step {k + 1}",
                           "bullets": [" ".join(x.split()[:10]) for x in part],
                           "talking_points": (part * 2)[:max(2, len(part))]})
        return {"slides": slides}

    def _script(self, prompt: str) -> dict:
        m = _SLIDES_RE.search(prompt)
        slides = json.loads(m.group(1)) if m else []
        out = []
        for s in slides:
            parts = [f"This slide is about {s['title']}."]
            parts += [b if b.endswith(".") else b + "." for b in s["bullets"]]
            parts += [e["explanation"] for e in s.get("equations", [])]
            parts += s.get("talking_points", [])
            out.append({"slide_id": s["id"], "text": " ".join(parts)})
        return {"slides": out}


def _split_sections(md: str) -> list[tuple[str, str]]:
    sections: list[tuple[str, list[str]]] = []
    for line in md.splitlines():
        h = re.match(r"^#{1,3}\s+(.+)", line)
        if h:
            sections.append((h.group(1).strip(), []))
        elif line.strip():
            if not sections:
                sections.append(("Introduction", []))
            sections[-1][1].append(line)
    return [(t, "\n".join(b)) for t, b in sections if b]


def _sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!?])\s+", re.sub(r"\s+", " ", text).strip())
    return [p.strip() for p in parts if len(p.strip()) > 3]
