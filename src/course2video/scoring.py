from __future__ import annotations

import csv
import json
from pathlib import Path

CRITERIA = ["accuracy", "completeness", "formulas", "clarity", "faithfulness", "equation_reading"]


def read_sheet(path: Path) -> dict[int, dict[str, int | None]]:
    rows: dict[int, dict[str, int | None]] = {}
    with open(path, newline="", encoding="utf-8") as f:
        for n, row in enumerate(csv.DictReader(f), start=2):
            if not (row.get("slide_id") or "").strip():
                continue
            scores: dict[str, int | None] = {}
            for c in CRITERIA:
                v = (row.get(c) or "").strip()
                if v == "":
                    scores[c] = None
                elif v in ("0", "1", "2"):
                    scores[c] = int(v)
                else:
                    raise ValueError(f"{path.name} line {n}: {c} must be 0, 1, 2 or empty, got {v!r}")
            rows[int(row["slide_id"])] = scores
    return rows


def cohen_kappa(a: list[int], b: list[int]) -> float | None:
    n = len(a)
    if n == 0:
        return None
    observed = sum(x == y for x, y in zip(a, b, strict=True)) / n
    expected = sum((a.count(k) / n) * (b.count(k) / n) for k in (0, 1, 2))
    if expected == 1:
        return 1.0 if observed == 1 else None
    return round((observed - expected) / (1 - expected), 3)


def _mean(values: list[int]) -> float | None:
    return round(sum(values) / len(values), 2) if values else None


def score_report(sheets: dict[str, Path], out_dir: Path | None = None,
                 review_log: Path | None = None) -> dict:
    data = {name: read_sheet(p) for name, p in sheets.items()}
    names = list(data)
    slides = sorted(set().union(*[set(d) for d in data.values()]))
    report: dict = {"reviewers": names, "slides_scored": len(slides), "criteria": {}}
    for c in CRITERIA:
        per = {r: _mean([d[s][c] for s in d if d[s][c] is not None]) for r, d in data.items()}
        allv = [d[s][c] for d in data.values() for s in d if d[s][c] is not None]
        entry = {"mean": _mean(allv), "per_reviewer": per}
        if len(names) == 2:
            a, b = data[names[0]], data[names[1]]
            pairs = [(a[s][c], b[s][c]) for s in slides
                     if s in a and s in b and a[s][c] is not None and b[s][c] is not None]
            entry["agreement"] = round(sum(x == y for x, y in pairs) / len(pairs), 3) if pairs else None
            entry["kappa"] = cohen_kappa([x for x, _ in pairs], [y for _, y in pairs])
            entry["disagreements"] = [s for s in slides if s in a and s in b
                                      and a[s][c] is not None and b[s][c] is not None
                                      and abs(a[s][c] - b[s][c]) >= 1]
        report["criteria"][c] = entry

    totals = {}
    for s in slides:
        vals = [d[s][c] for d in data.values() if s in d for c in CRITERIA if d[s][c] is not None]
        totals[s] = _mean(vals)
    report["slide_means"] = totals

    if out_dir is not None:
        flags = {}
        for name in ("grounding", "alignment"):
            f = out_dir / f"{name}.json"
            if f.exists():
                flags[name] = set(json.loads(f.read_text()).get("flagged_slides", []))
        checks = {}
        for name, flagged in flags.items():
            in_flag = [totals[s] for s in slides if s in flagged and totals[s] is not None]
            out_flag = [totals[s] for s in slides if s not in flagged and totals[s] is not None]
            checks[name] = {"flagged": sorted(flagged & set(slides)),
                            "mean_score_flagged": _mean(in_flag),
                            "mean_score_not_flagged": _mean(out_flag)}
        report["automatic_checks"] = checks

    if review_log is not None and review_log.exists():
        with open(review_log, newline="", encoding="utf-8") as f:
            rows = [r for r in csv.DictReader(f) if (r.get("reviewer") or "").strip()]
        report["review_time"] = [{k: r[k] for k in r} for r in rows]
    return report


def report_markdown(report: dict) -> str:
    names = report["reviewers"]
    lines = ["# Scoring report", "",
             f"Reviewers: {', '.join(names)}. Slides scored: {report['slides_scored']}.", "",
             "| Criterion | Mean (0-2) | " + " | ".join(names)
             + (" | Agreement | Kappa | Disagreements |" if len(names) == 2 else " |"),
             "|---|---|" + "---|" * len(names) + ("---|---|---|" if len(names) == 2 else "")]
    for c, e in report["criteria"].items():
        row = f"| {c} | {e['mean']} | " + " | ".join(str(e["per_reviewer"][r]) for r in names)
        if len(names) == 2:
            row += f" | {e['agreement']} | {e['kappa']} | {', '.join(map(str, e['disagreements'])) or '-'} |"
        else:
            row += " |"
        lines.append(row)
    checks = report.get("automatic_checks") or {}
    if checks:
        lines += ["", "## Do the automatic checks point at the weak slides?", "",
                  "| Check | Flagged slides | Mean score flagged | Mean score not flagged |",
                  "|---|---|---|---|"]
        for name, e in checks.items():
            lines.append(f"| {name}.json | {', '.join(map(str, e['flagged'])) or '-'} | "
                         f"{e['mean_score_flagged']} | {e['mean_score_not_flagged']} |")
    if report.get("review_time"):
        lines += ["", "## Review time", "",
                  "| Reviewer | Course | Slides | Review (min) | Corrections | Kinds "
                  "| Manual estimate (min) |",
                  "|---|---|---|---|---|---|---|"]
        for r in report["review_time"]:
            lines.append(f"| {r.get('reviewer', '')} | {r.get('course', '')} | {r.get('slides', '')} | "
                         f"{r.get('review_minutes', '')} | {r.get('corrections', '')} | "
                         f"{r.get('correction_kinds', '')} | {r.get('manual_estimate_minutes', '')} |")
    return "\n".join(lines) + "\n"
