from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

import yaml

DocType = Literal["lecture", "exercises", "solutions", "practical"]
SUPPORTED = {".pdf", ".md", ".markdown", ".txt"}
SKIP_DIRS = {"output", "out", "parsed", "figures", "images", "audio", "parts"}

ROLE_PATTERNS: list[tuple[DocType, str]] = [
    ("solutions", r"sol(ution)?s?\b|_sol|corrig|answer|\bkey\b"),
    ("exercises", r"pset|problem|exerc|\btd\d*\b|tutorial|sheet|homework|\bhw\d*\b"),
    ("practical", r"\btp\d*\b|\blab\d*\b|practical"),
    ("lecture", r"lecture|cours|notes|reading|chap|prep|slides|class"),
]
_SOL_TOKENS = re.compile(r"[_\-\s]*(sol(ution)?s?|corrig[eé]?|answers?|key)\b", re.I)


@dataclass
class CourseDocument:
    path: Path
    type: DocType
    label: str
    solves: Path | None = None
    select: list[int] | None = None


@dataclass
class Course:
    root: Path
    title: str
    language: str | None = None
    target_minutes: float | None = None
    documents: list[CourseDocument] = field(default_factory=list)
    source: dict = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)

    def of_type(self, t: DocType) -> list[CourseDocument]:
        return [d for d in self.documents if d.type == t]


def guess_role(path: Path) -> DocType | None:
    name = "/".join(path.parts[-2:]).lower()
    for role, pattern in ROLE_PATTERNS:
        if re.search(pattern, name):
            return role
    return None


def pretty_label(path: Path) -> str:
    stem = re.sub(r"^mit\d+_\d+_s\d+_", "", path.stem, flags=re.I)
    stem = re.sub(r"[_\-]+", " ", stem).strip()
    m = re.match(r"(pset|td|hw|tp)\s*0*(\d+)(.*)", stem, re.I)
    if m:
        names = {"pset": "Problem Set", "td": "TD", "hw": "Homework", "tp": "TP"}
        stem = f"{names[m.group(1).lower()]} {m.group(2)}{m.group(3)}"
    return stem[:1].upper() + stem[1:]


def _from_manifest(root: Path, data: dict) -> Course:
    course = Course(
        root=root,
        title=data.get("title") or root.name.replace("_", " "),
        language=data.get("language"),
        target_minutes=data.get("target_minutes"),
        source=data.get("source", {}),
    )
    for d in data.get("documents", []):
        path = (root / d["path"]).resolve()
        if not path.exists():
            course.warnings.append(f"missing file listed in course.yaml: {d['path']}")
            continue
        course.documents.append(CourseDocument(
            path=path, type=d["type"], label=d.get("label") or pretty_label(path),
            solves=(root / d["solves"]).resolve() if d.get("solves") else None,
            select=d.get("select"),
        ))
    return course


def _from_filenames(root: Path) -> Course:
    course = Course(root=root, title=root.name.replace("_", " ").replace("-", " "))
    files = sorted(p for p in root.rglob("*") if p.suffix.lower() in SUPPORTED and p.is_file()
                   and not set(p.relative_to(root).parts[:-1]) & SKIP_DIRS)
    for p in files:
        role = guess_role(p.relative_to(root))
        if role is None:
            course.warnings.append(f"skipped {p.relative_to(root)}: cannot tell its role from the name; "
                                   "add it to course.yaml")
            continue
        course.warnings.append(f"guessed {p.relative_to(root)} = {role} (from its name)")
        course.documents.append(CourseDocument(path=p.resolve(), type=role, label=pretty_label(p)))
    return course


def _pair_solutions(course: Course) -> None:
    exercises = course.of_type("exercises")
    for sol in course.of_type("solutions"):
        if sol.solves is not None:
            continue
        base = _SOL_TOKENS.sub("", sol.path.stem).lower()
        match = [e for e in exercises if e.path.stem.lower() == base]
        if not match and len(exercises) == 1:
            match = exercises
        if match:
            sol.solves = match[0].path
            course.warnings.append(f"paired {sol.path.name} with {match[0].path.name} (by name)")
        else:
            course.warnings.append(f"no exercise document found for {sol.path.name}")


def load_course(path: Path) -> Course:
    path = Path(path)
    if path.is_file():
        return Course(root=path.parent, title=path.stem.replace("_", " "),
                      documents=[CourseDocument(path=path.resolve(), type="lecture",
                                                label=pretty_label(path))])
    manifest = path / "course.yaml"
    if manifest.exists():
        course = _from_manifest(path, yaml.safe_load(manifest.read_text(encoding="utf-8")) or {})
    else:
        course = _from_filenames(path)
    _pair_solutions(course)
    if not course.of_type("lecture"):
        raise ValueError(f"no lecture document found in {path}")
    return course
