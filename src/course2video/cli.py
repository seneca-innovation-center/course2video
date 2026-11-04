from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

from .config import Config, load_config


def _apply_overrides(cfg: Config, a: argparse.Namespace) -> Config:
    if getattr(a, "llm", None):
        cfg.llm.backend = a.llm
    if getattr(a, "model", None):
        cfg.llm.model = a.model
    if getattr(a, "base_url", None):
        cfg.llm.base_url = a.base_url
    if getattr(a, "parser", None):
        cfg.parser.backend = a.parser
    if getattr(a, "tts", None):
        cfg.tts.backend = a.tts
    if getattr(a, "minutes", None):
        cfg.lecture.target_minutes = a.minutes
    return cfg


def _add_common(p: argparse.ArgumentParser) -> None:
    p.add_argument("--config", help="YAML config file (default: $C2V_CONFIG or built-in defaults)")
    p.add_argument("--llm", choices=["mock", "openai_compat"])
    p.add_argument("--model", help="model name for the chosen LLM backend")
    p.add_argument("--base-url", help="openai_compat server URL, e.g. http://localhost:8000/v1")
    p.add_argument("--tts", choices=["piper", "say", "stub"])
    p.add_argument("--no-video", action="store_true", help="stop after script, alignment and pptx")


def cmd_run(a) -> int:
    from .pipeline import run_stage1, run_stage2

    cfg = _apply_overrides(load_config(a.config), a)
    out = Path(a.out)
    st = run_stage1(Path(a.input), out, cfg, language=a.language)
    print(f"[1/2] {st['slides']} slides written to {out/'slides.json'} and {out/'slides.md'}"
          + (f" ({st['problems']} worked problems)" if st.get("problems") else ""))
    if st.get("warnings"):
        print(f"      {st['warnings']} warning(s) about documents and links: see {out/'course_index.json'}")
    if a.until == "slides":
        return 0
    if not a.auto_approve:
        print(
            "\nLecturer review required. Edit slides.md or slides.json, then run:\n"
            f"    course2video continue {out} --from md     (or --from json)"
        )
        return 0
    print("[auto-approve] skipping human review (demo mode)")
    summary = run_stage2(out, cfg, video=not a.no_video)
    print("[2/2] done:", json.dumps(summary, indent=2))
    return 0


def cmd_continue(a) -> int:
    from .pipeline import run_stage2
    from .review import ReviewError

    out = Path(a.out)
    used = out / "config.used.yaml"
    cfg = load_config(a.config or (used if used.exists() else None))
    cfg = _apply_overrides(cfg, a)
    try:
        summary = run_stage2(out, cfg, source=a.source, video=not a.no_video)
    except ReviewError as e:
        print(f"Review edits rejected, nothing was narrated.\n{e}", file=sys.stderr)
        return 2
    print("[2/2] done:", json.dumps(summary, indent=2))
    return 0


def cmd_render(a) -> int:
    from .pipeline import rerender

    out = Path(a.out)
    used = out / "config.used.yaml"
    cfg = _apply_overrides(load_config(a.config or (used if used.exists() else None)), a)
    summary = rerender(out, cfg, video=not a.no_video)
    print("done:", json.dumps(summary, indent=2))
    return 0


def cmd_score(a) -> int:
    from .scoring import report_markdown, score_report

    sheets = {Path(x).stem: Path(x) for x in a.sheets}
    report = score_report(sheets, Path(a.out) if a.out else None,
                          Path(a.review_log) if a.review_log else None)
    text = report_markdown(report)
    if a.report:
        Path(a.report).parent.mkdir(parents=True, exist_ok=True)
        Path(a.report).write_text(text, encoding="utf-8")
        Path(a.report).with_suffix(".json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(text)
    return 0


def cmd_validate(a) -> int:
    from .slides.validate import validate_deck_file

    deck, errors = validate_deck_file(Path(a.file).read_text(encoding="utf-8"))
    if deck is None:
        print("INVALID\n- " + "\n- ".join(errors))
        return 1
    print(f"OK: {len(deck.slides)} slides")
    return 0


def cmd_schemas(a) -> int:
    from .script.models import Script
    from .slides.models import Deck

    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    for name, model in (("slide", Deck), ("script", Script)):
        schema = model.model_json_schema()
        schema["$schema"] = "https://json-schema.org/draft/2020-12/schema"
        (out / f"{name}.schema.json").write_text(json.dumps(schema, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {out}/slide.schema.json and {out}/script.schema.json")
    return 0


def cmd_check_llm(a) -> int:
    from .llm import get_backend

    cfg = _apply_overrides(load_config(a.config), a)
    llm = get_backend(cfg.llm)
    schema = {"type": "object", "properties": {"ok": {"type": "boolean"}}, "required": ["ok"]}
    text = llm.complete("Answer in JSON only.", 'Return {"ok": true}.', schema=schema, task="check")
    print(llm.describe(), "->", text.strip()[:200])
    return 0


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    p = argparse.ArgumentParser(prog="course2video",
                                description="Course documents to reviewed slides and narrated video.",
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)

    r = sub.add_parser("run", help="parse a document and generate slides for review")
    r.add_argument("input", help="a document, or a course folder (lecture notes + exercises + "
                                 "solutions, optionally with course.yaml)")
    r.add_argument("--minutes", type=float, help="target video length (overrides course.yaml)")
    r.add_argument("--out", required=True)
    r.add_argument("--parser", choices=["docling", "pypdf", "markdown"])
    r.add_argument("--language", default="en")
    r.add_argument("--until", choices=["slides", "review"], default="review")
    r.add_argument("--auto-approve", action="store_true",
                   help="DEMO ONLY: skip lecturer review and continue to video")
    _add_common(r)
    r.set_defaults(func=cmd_run)

    c = sub.add_parser("continue", help="after review: script, alignment check, pptx, video")
    c.add_argument("out")
    c.add_argument("--from", dest="source", choices=["json", "md"], default="json")
    _add_common(c)
    c.set_defaults(func=cmd_continue)

    rr = sub.add_parser("render", help="rebuild pptx and video from approved slides + script (no LLM)")
    rr.add_argument("out")
    _add_common(rr)
    rr.set_defaults(func=cmd_render)

    sc = sub.add_parser("score", help="summarise reviewers' score sheets (eval/rubric.md)")
    sc.add_argument("sheets", nargs="+", help="one CSV per reviewer (eval/templates/score_sheet.csv)")
    sc.add_argument("--out", help="run folder, to compare with grounding.json / alignment.json")
    sc.add_argument("--review-log", help="CSV with review times (eval/templates/review_log.csv)")
    sc.add_argument("--report", help="write the report here (.md, plus .json)")
    sc.set_defaults(func=cmd_score)

    v = sub.add_parser("validate", help="validate a slides.json file")
    v.add_argument("file")
    v.set_defaults(func=cmd_validate)

    s = sub.add_parser("schemas", help="regenerate JSON schemas from the Pydantic models")
    s.add_argument("--out", default="schemas")
    s.set_defaults(func=cmd_schemas)

    k = sub.add_parser("check-llm", help="send one tiny request to the configured LLM")
    _add_common(k)
    k.set_defaults(func=cmd_check_llm)

    a = p.parse_args(argv)
    return a.func(a)


if __name__ == "__main__":
    sys.exit(main())
