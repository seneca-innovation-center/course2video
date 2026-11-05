from __future__ import annotations

import json
import logging
import time
from dataclasses import asdict
from pathlib import Path
from typing import Any

import yaml

from .config import Config
from .llm import LLMBackend, get_backend
from .parsing import get_parser
from .review import export_for_review, import_reviewed
from .script.alignment import check_alignment
from .script.generate import generate_script
from .slides.generate import generate_deck, guess_title
from .tts import TTSBackend, get_tts, wav_duration

log = logging.getLogger(__name__)


def _write_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def _state(out: Path) -> dict:
    p = out / "state.json"
    return json.loads(p.read_text()) if p.exists() else {}


def _set_state(out: Path, **kw) -> dict:
    st = _state(out)
    st.update(kw)
    st["updated_at"] = time.strftime("%Y-%m-%dT%H:%M:%S")
    _write_json(out / "state.json", st)
    return st


def number_figures(course, parsed: dict, figures_dir: Path) -> dict[str, dict]:
    import re
    import shutil

    from .parsing.base import FIGURE_TOKEN

    shutil.rmtree(figures_dir, ignore_errors=True)
    index: dict[str, dict] = {}
    for doc in course.documents:
        pd = parsed[doc.path]
        for k, fig in enumerate(pd.figures):
            gid = f"F{len(index) + 1}"
            figures_dir.mkdir(parents=True, exist_ok=True)
            dest = figures_dir / f"{gid}{fig.path.suffix or '.png'}"
            shutil.copyfile(fig.path, dest)
            caption = " ".join(fig.caption.split()) or "no caption"
            index[gid] = {"file": dest.name, "caption": caption, "page": fig.page,
                          "source": doc.label}
            pd.markdown = pd.markdown.replace(FIGURE_TOKEN.format(k), f"[Figure {gid}: {caption}]")
        pd.markdown = re.sub(r"\[\[FIG:\d+\]\]", "", pd.markdown)
    if index:
        _write_json(figures_dir / "figures.json", index)
    return index


def _fit_context(llm: LLMBackend, cfg: Config) -> dict | None:
    from .config import fit_to_context

    ctx = llm.context_length() if hasattr(llm, "context_length") else None
    if not ctx:
        return None
    changes = fit_to_context(cfg, ctx)
    if changes:
        log.warning("model context is %d tokens; adjusted %s", ctx, ", ".join(changes))
    return {"tokens": ctx, "adjusted": changes}


def _attempts(log_: list) -> list[list[dict]]:
    return [[asdict(a) for a in chunk] for chunk in log_]


def _parse(path: Path, cfg: Config):
    if cfg.parser.backend == "docling" and path.suffix.lower() == ".pdf":
        from .parsing.cache import parse_cached

        return parse_cached(path, "docling", docling_formulas=cfg.parser.docling_formulas)
    return get_parser(cfg.parser.backend, path, docling_formulas=cfg.parser.docling_formulas).parse(path)


def run_stage1(
    input_path: Path, out: Path, cfg: Config, llm: LLMBackend | None = None, language: str = "en"
) -> dict:
    from .course import link_problems, load_course
    from .course.budget import plan_budget
    from .slides.models import Deck
    from .slides.problems import generate_problem_slides

    out.mkdir(parents=True, exist_ok=True)
    course = load_course(input_path)
    language = course.language or language
    target = cfg.lecture.target_minutes or course.target_minutes
    if target:
        cfg.lecture.target_minutes = target
    llm = llm or get_backend(cfg.llm)
    context = _fit_context(llm, cfg)
    (out / "config.used.yaml").write_text(yaml.safe_dump(cfg.model_dump()), encoding="utf-8")

    t0 = time.time()
    parsed_dir = out / "parsed"
    parsed_dir.mkdir(exist_ok=True)
    parsed = {}
    for doc in course.documents:
        parsed[doc.path] = _parse(doc.path, cfg)
    figures = number_figures(course, parsed, out / "figures")
    for doc in course.documents:
        (parsed_dir / f"{doc.path.stem}.md").write_text(parsed[doc.path].markdown, encoding="utf-8")
    lecture_md = "\n\n".join(parsed[d.path].markdown for d in course.of_type("lecture"))
    (out / "parsed.md").write_text(lecture_md, encoding="utf-8")
    t_parse = time.time() - t0

    from .render.lecture import templates

    words = templates(language)
    problems, link_warnings = [], []
    for ex in course.of_type("exercises"):
        sol = next((s for s in course.of_type("solutions") if s.solves == ex.path), None)
        ps, w = link_problems(parsed[ex.path].markdown, parsed[sol.path].markdown if sol else None,
                              ex.label, ex.select, word=words["problem"])
        problems += ps
        link_warnings += w
    worked = [p for p in problems if p.selected and p.solution]

    budget = None
    if target:
        source_words = sum(len(p.markdown.split()) for p in parsed.values())
        n_sections = max(1, lecture_md.count("\n## ") + lecture_md.count("\n# "))
        from .slides.generate import count_chapters

        budget = plan_budget(target, source_words=source_words, n_problems=len(worked),
                             n_sections_hint=min(n_sections, 8),
                             min_theory_slides=count_chapters(lecture_md),
                             words_per_slide=cfg.script.words_per_slide)

    _write_json(out / "course_index.json", {
        "title": course.title,
        "root": str(course.root),
        "source": course.source,
        "documents": [{"path": str(d.path.relative_to(course.root.resolve()))
                       if d.path.is_relative_to(course.root.resolve()) else str(d.path),
                       "type": d.type, "label": d.label,
                       "solves": d.solves.name if d.solves else None,
                       "words": len(parsed[d.path].markdown.split()),
                       "parser": parsed[d.path].parser, "warnings": parsed[d.path].warnings}
                      for d in course.documents],
        "problems": [{"ref": p.ref, "title": p.title, "has_solution": p.solution is not None,
                      "selected": p.selected, "used": p in worked,
                      "statement_words": len(p.statement.split()),
                      "solution_words": len((p.solution or "").split())} for p in problems],
        "warnings": course.warnings + link_warnings,
        "budget": budget.as_dict() if budget else None,
    })

    title = course.title if (input_path / "course.yaml").exists() else guess_title(
        lecture_md, course.title)
    t0 = time.time()
    deck, attempts = generate_deck(llm, lecture_md, cfg.slides, title=title, language=language,
                                   total_slides=budget.theory_slides if budget else None)
    problem_attempts = []
    for p in worked:
        batch, att = generate_problem_slides(
            llm, p, n_slides=budget.slides_per_problem if budget else 3,
            language=language, max_retries=cfg.slides.max_retries, worked=words["worked"])
        deck.slides.extend(batch.slides)
        problem_attempts.append(att)
    deck = Deck(title=deck.title, language=deck.language,
                slides=[s.model_copy(update={"id": i}) for i, s in enumerate(deck.slides, 1)])
    t_slides = time.time() - t0
    export_for_review(deck, out)

    from .slides.grounding import check_grounding

    problem_texts = {p.ref: p.statement + "\n" + (p.solution or "") for p in worked}
    _write_json(parsed_dir / "problems.json", problem_texts)
    grounding = check_grounding(deck, lecture_md, problem_texts)
    _write_json(out / "grounding.json", grounding)

    _write_json(
        out / "meta.json",
        {
            "input": str(input_path),
            "documents": len(course.documents),
            "parser": cfg.parser.backend,
            "parser_warnings": [w for p in parsed.values() for w in p.warnings
                                if w != "(from cache)"],
            "llm": llm.describe(),
            "context": context,
            "figures": len(figures),
            "budget": budget.as_dict() if budget else None,
            "slides": {"count": len(deck.slides),
                       "by_kind": {k: sum(s.kind == k for s in deck.slides)
                                   for k in ("theory", "exercise", "solution")},
                       "attempts_per_chunk": _attempts(attempts),
                       "attempts_per_problem": _attempts(problem_attempts)},
            "timings_s": {"parse": round(t_parse, 2), "slides": round(t_slides, 2)},
            "grounding": {"mean_overlap": grounding["mean_overlap"],
                          "flagged_slides": grounding["flagged_slides"],
                          "flagged_talking_points": sum(t["flagged"] for sl in grounding["slides"]
                                                        for t in sl["talking_points"])},
        },
    )
    return _set_state(out, stage="awaiting_review", slides=len(deck.slides),
                      problems=len(worked), warnings=len(course.warnings + link_warnings))


def run_stage2(
    out: Path,
    cfg: Config,
    *,
    source: str = "json",
    llm: LLMBackend | None = None,
    tts: TTSBackend | None = None,
    video: bool = True,
) -> dict:
    st = _state(out)
    if st.get("stage") not in {"awaiting_review", "approved", "done", "script_done"}:
        raise RuntimeError(f"{out} has no slides awaiting review; run `course2video run` first")
    deck = import_reviewed(out, source)
    _set_state(out, stage="approved")
    meta = json.loads((out / "meta.json").read_text()) if (out / "meta.json").exists() else {}

    if (out / "parsed.md").exists():
        from .slides.grounding import check_grounding

        problems_file = out / "parsed" / "problems.json"
        problem_texts = json.loads(problems_file.read_text()) if problems_file.exists() else {}
        grounding = check_grounding(deck, (out / "parsed.md").read_text(encoding="utf-8"),
                                    problem_texts)
        _write_json(out / "grounding.json", grounding)
        meta["grounding"] = {"mean_overlap": grounding["mean_overlap"],
                             "flagged_slides": grounding["flagged_slides"],
                             "flagged_talking_points": sum(
                                 t["flagged"] for sl in grounding["slides"]
                                 for t in sl["talking_points"])}

    llm = llm or get_backend(cfg.llm)
    stage2_context = _fit_context(llm, cfg)
    if stage2_context:
        meta["context"] = stage2_context
    t0 = time.time()
    budget = meta.get("budget")
    figures_file = out / "figures" / "figures.json"
    captions = ({k: v["caption"] for k, v in json.loads(figures_file.read_text()).items()}
                if figures_file.exists() else {})
    script, attempts = generate_script(llm, deck, cfg.script,
                                       words_per_slide=budget["words_per_slide"] if budget else None,
                                       figures=captions)
    meta.setdefault("timings_s", {})["script"] = round(time.time() - t0, 2)
    meta["script"] = {"llm": llm.describe(), "attempts_per_batch": _attempts(attempts)}
    (out / "script.json").write_text(script.model_dump_json(indent=2), encoding="utf-8")
    (out / "script.md").write_text(
        "\n\n".join(f"## Slide {e.slide_id}\n{e.text}" for e in script.slides), encoding="utf-8"
    )

    report = check_alignment(deck, script, cfg.alignment)
    _write_json(out / "alignment.json", report)
    meta["alignment"] = {
        "spoken_to_slide_word_ratio": report["spoken_to_slide_word_ratio"],
        "overall_coverage": report["overall_coverage"],
        "flagged_slides": report["flagged_slides"],
    }

    summary = render_outputs(out, cfg, deck, script, meta, tts=tts, video=video)
    _write_json(out / "meta.json", meta)
    _set_state(out, stage="done" if video else "script_done")
    return summary


def render_outputs(
    out: Path, cfg: Config, deck, script, meta: dict, *, tts: TTSBackend | None = None,
    video: bool = True,
) -> dict:
    from .render.lecture import build_frames, templates, write_plan
    from .render.pptx_builder import build_pptx

    frames = build_frames(deck, script, cfg.lecture)
    write_plan(frames, out / "lecture_plan.json")
    meta["lecture"] = {"frames": len(frames),
                       "kinds": [f.kind for f in frames]}
    pptx = build_pptx(frames, out / "deck.pptx", templates(deck.language)["part"],
                      figures_dir=out / "figures")
    summary: dict[str, Any] = {"pptx": str(pptx), "frames": len(frames),
                               "alignment": meta.get("alignment")}

    if video:
        from .render.slide_images import render_frames, render_libreoffice
        from .render.subtitles import write_srt
        from .render.video_assembly import assemble_video

        t0 = time.time()
        if cfg.render.renderer == "libreoffice":
            images = render_libreoffice(pptx, out / "images", cfg.render)
        else:
            images = render_frames(frames, deck.title, deck.language, out / "images", cfg.render,
                                   progress_bar=cfg.lecture.progress_bar)
        tts = tts or get_tts(cfg.tts, deck.language)
        audio_dir = out / "audio"
        for old in audio_dir.glob("*.wav"):
            old.unlink()
        audios = [tts.synthesize(f.narration, audio_dir / f"frame_{f.index + 1:03d}.wav")
                  for f in frames]
        speech = [wav_duration(a) for a in audios]
        states = {}
        if cfg.render.reveal_bullets and cfg.render.renderer == "pillow":
            from .render.reveal import reveal_times
            from .render.slide_images import render_reveal_states

            state_images = render_reveal_states(frames, deck.title, deck.language, out / "images",
                                                cfg.render, progress_bar=cfg.lecture.progress_bar)
            for i, paths in state_images.items():
                times = reveal_times(frames[i].narration, frames[i].slide.bullets, speech[i])
                states[i] = list(zip(paths, times, strict=True))
            meta["reveal"] = {str(i + 1): [t for _, t in v] for i, v in states.items()}
        elif cfg.render.reveal_bullets:
            log.warning("reveal_bullets needs render.renderer: pillow; showing full slides")
        durations = assemble_video(
            images, audios, out / "video.mp4",
            pause_s=cfg.render.pause_after_slide_s, fps=cfg.render.fps, states=states,
        )
        write_srt([f.narration for f in frames], durations, speech, out / "subtitles.srt")
        import shutil

        shutil.rmtree(out / "segments", ignore_errors=True)
        if cfg.render.per_part_videos:
            from .render.parts import write_part_videos

            parts = write_part_videos(frames, images, audios, out / "parts",
                                      pause_s=cfg.render.pause_after_slide_s, fps=cfg.render.fps,
                                      states=states)
            meta["parts"] = parts
            if not parts:
                meta["parts_note"] = "fewer than 2 parts: only the full video was written"
            summary["parts"] = len(parts)
        else:
            shutil.rmtree(out / "parts", ignore_errors=True)
            meta.pop("parts", None)
        meta.setdefault("timings_s", {})["render_tts_video"] = round(time.time() - t0, 2)
        meta["video"] = {"tts": tts.name, "renderer": cfg.render.renderer,
                         "duration_s": round(sum(durations), 2)}
        summary.update(video=str(out / "video.mp4"), subtitles=str(out / "subtitles.srt"),
                       duration_s=round(sum(durations), 2))
        if cfg.lecture.target_minutes:
            minutes = sum(durations) / 60
            meta["video"]["target_minutes"] = cfg.lecture.target_minutes
            meta["video"]["actual_minutes"] = round(minutes, 1)
            summary["minutes"] = {"target": cfg.lecture.target_minutes, "actual": round(minutes, 1)}

    return summary


def rerender(out: Path, cfg: Config, *, video: bool = True) -> dict:
    from .script.models import Script
    from .slides.models import Deck

    deck = Deck.model_validate_json((out / "slides.json").read_text(encoding="utf-8"))
    if not deck.approved or not (out / "script.json").exists():
        raise RuntimeError(f"{out} has no approved slides and script; run `continue` first")
    script = Script.model_validate_json((out / "script.json").read_text(encoding="utf-8"))
    meta = json.loads((out / "meta.json").read_text()) if (out / "meta.json").exists() else {}
    summary = render_outputs(out, cfg, deck, script, meta, video=video)
    _write_json(out / "meta.json", meta)
    return summary
