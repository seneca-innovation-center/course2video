from __future__ import annotations

import re
from dataclasses import dataclass

_HEAD = re.compile(
    r"(?m)^[#>\s*_]*(?:Problem|Exercise|Exercice|Ejercicio|Question|Aufgabe)\s+(\d+)\b[.:)]?[*_]*\s*(.*)$",
    re.I,
)


@dataclass
class Problem:
    number: int
    title: str
    statement: str
    solution: str | None
    doc_label: str
    selected: bool = True
    word: str = "Problem"

    @property
    def ref(self) -> str:
        return f"{self.doc_label}, {self.word} {self.number}"

    @property
    def display_title(self) -> str:
        return f"{self.word} {self.number}: {self.title}" if self.title else f"{self.word} {self.number}"


def _title(rest: str) -> str:
    groups = [g.strip() for g in re.findall(r"\(([^()]{2,80})\)", rest)]
    groups = [g for g in groups if not re.search(r"\bpts?\b|points?|marks?|\d+\s*:", g, re.I)]
    title = groups[0] if groups else ""
    title = re.sub(r"\s+", " ", title).strip()
    title = re.sub(r"(^|\s)['\"‘“](\w[^'\"’”]*)['\"’”]", r"\1\2", title)
    return re.sub(r"\bT rees\b", "Trees", title)


def split_numbered(md: str) -> dict[int, tuple[str, str]]:
    heads = list(_HEAD.finditer(md))
    out: dict[int, tuple[str, str]] = {}
    for i, m in enumerate(heads):
        n = int(m.group(1))
        end = heads[i + 1].start() if i + 1 < len(heads) else len(md)
        if n not in out:
            out[n] = (_title(m.group(2)), md[m.start():end].strip())
    return out


def link_problems(
    exercises_md: str, solutions_md: str | None, doc_label: str, select: list[int] | None = None,
    word: str = "Problem",
) -> tuple[list[Problem], list[str]]:
    warnings = []
    ex = split_numbered(exercises_md)
    sol = split_numbered(solutions_md) if solutions_md else {}
    if not ex:
        warnings.append(f"{doc_label}: no 'Problem N' / 'Exercise N' headings found")
    problems = []
    for n, (title, text) in sorted(ex.items()):
        s = sol.get(n)
        if solutions_md and s is None:
            warnings.append(f"{doc_label}: no solution found for problem {n}")
        problems.append(Problem(
            number=n, title=title or (s[0] if s else ""), statement=text,
            solution=s[1] if s else None, doc_label=doc_label,
            selected=(select is None or n in select), word=word,
        ))
    for n in sorted(set(sol) - set(ex)):
        warnings.append(f"{doc_label}: solution {n} has no matching problem")
    if select:
        for n in sorted(set(select) - set(ex)):
            warnings.append(f"{doc_label}: selected problem {n} does not exist")
    return problems, warnings
