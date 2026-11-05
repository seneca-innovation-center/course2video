from __future__ import annotations

import json
import sys
from pathlib import Path


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def attempts(chunks: list) -> tuple[int, int]:
    calls = len(chunks)
    first = sum(1 for c in chunks if c and c[0].get("ok"))
    return first, calls


def row(name: str, out: Path) -> dict:
    meta, align, ground = load(out / "meta.json"), load(out / "alignment.json"), load(out / "grounding.json")
    state = load(out / "state.json").get("stage", "not run")
    slides = meta.get("slides", {})
    s_first, s_calls = attempts(slides.get("attempts_per_chunk", []) + slides.get("attempts_per_problem", []))
    sc_first, sc_calls = attempts(meta.get("script", {}).get("attempts_per_batch", []))
    video = meta.get("video", {})
    return {
        "course": name,
        "state": state,
        "model": meta.get("llm", {}).get("model", ""),
        "slides": slides.get("count"),
        "by_kind": slides.get("by_kind"),
        "slides_first_attempt": f"{s_first}/{s_calls}" if s_calls else "",
        "script_first_attempt": f"{sc_first}/{sc_calls}" if sc_calls else "",
        "coverage": align.get("overall_coverage"),
        "spoken_to_slide": align.get("spoken_to_slide_word_ratio"),
        "grounding_flagged_points": meta.get("grounding", {}).get("flagged_talking_points"),
        "grounding_flagged_slides": ground.get("flagged_slides"),
        "minutes": video.get("actual_minutes") or (round(video["duration_s"] / 60, 1)
                                                   if video.get("duration_s") else None),
        "target_minutes": video.get("target_minutes"),
        "timings_s": meta.get("timings_s"),
        "context": meta.get("context"),
    }


def main(root: str) -> int:
    root_p = Path(root)
    rows = [row(d.name, d) for d in sorted(root_p.iterdir()) if d.is_dir() and (d / "state.json").exists()]
    (root_p / "summary.json").write_text(json.dumps(rows, indent=2, ensure_ascii=False), encoding="utf-8")
    lines = ["| Course | State | Slides | Slides valid 1st try | Script valid 1st try | Coverage | "
             "Spoken/slide words | Grounding flags | Minutes (target) | Slides + script time |",
             "|---|---|---|---|---|---|---|---|---|---|"]
    for r in rows:
        t = r["timings_s"] or {}
        times = f"{t.get('slides', '')} s + {t.get('script', '')} s" if t else ""
        target = f" ({r['target_minutes']})" if r["target_minutes"] else ""
        lines.append(f"| {r['course']} | {r['state']} | {r['slides']} | {r['slides_first_attempt']} | "
                     f"{r['script_first_attempt']} | {r['coverage']} | {r['spoken_to_slide']} | "
                     f"{r['grounding_flagged_points']} | {r['minutes']}{target} | {times} |")
    text = "\n".join(lines) + "\n"
    (root_p / "summary.md").write_text(text, encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "out/gptoss"))
