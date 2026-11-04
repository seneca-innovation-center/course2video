import json

import pytest
from PIL import Image
from pptx import Presentation

from course2video.config import Config
from course2video.llm.mock_backend import MockBackend
from course2video.parsing import get_parser
from course2video.pipeline import run_stage1, run_stage2
from course2video.review import ReviewError
from course2video.slides.models import Deck, SlideBatch
from course2video.slides.validate import check_figures, generate_validated


def _course(tmp_path):
    src = tmp_path / "course"
    src.mkdir()
    Image.new("RGB", (300, 200), (200, 30, 30)).save(src / "tree.png")
    (src / "notes.md").write_text(
        "# Trees\n\n## 1. Probability trees\n\nA tree organises a two-stage experiment. "
        "Each branch carries a conditional probability.\n\n![A two-stage tree](tree.png)\n\n"
        "## 2. Independence\n\nTwo events are independent when one does not change the other.\n")
    return src


def _cfg():
    cfg = Config()
    cfg.render.width, cfg.render.height = 640, 360
    return cfg


def test_markdown_figures_are_extracted(tmp_path):
    src = _course(tmp_path)
    doc = get_parser("markdown", src / "notes.md").parse(src / "notes.md")
    assert len(doc.figures) == 1 and doc.figures[0].caption == "A two-stage tree"
    assert "[[FIG:0]]" in doc.markdown


def test_figures_are_numbered_and_reach_the_slide(tmp_path):
    out = tmp_path / "out"
    run_stage1(_course(tmp_path), out, _cfg())
    index = json.loads((out / "figures" / "figures.json").read_text())
    assert index["F1"]["caption"] == "A two-stage tree"
    assert "[Figure F1: A two-stage tree]" in (out / "parsed.md").read_text()
    deck = Deck.model_validate_json((out / "slides.json").read_text())
    assert [s.figure for s in deck.slides] == ["F1", ""]
    assert "Figure: F1" in (out / "slides.md").read_text()


def test_figure_is_drawn_on_the_slide_and_in_the_pptx(tmp_path):
    out = tmp_path / "out"
    run_stage1(_course(tmp_path), out, _cfg())
    run_stage2(out, _cfg())
    plan = json.loads((out / "lecture_plan.json").read_text())
    i = next(f["index"] for f in plan if f["kind"] == "content" and f["heading"])
    img = Image.open(out / "images" / f"frame_{i + 1:03d}.png").convert("RGB")
    assert img.getpixel((int(640 * 0.78), 180)) == (200, 30, 30)
    prs = Presentation(str(out / "deck.pptx"))
    assert any(sh.shape_type == 13 for sh in prs.slides[i].shapes)


def test_unknown_figure_in_review_is_rejected(tmp_path):
    out = tmp_path / "out"
    run_stage1(_course(tmp_path), out, _cfg())
    md = (out / "slides.md").read_text().replace("Figure: F1", "Figure: F9")
    (out / "slides.md").write_text(md)
    with pytest.raises(ReviewError, match="F9"):
        run_stage2(out, _cfg(), source="md", video=False)


def test_model_cannot_invent_a_figure_id():
    bad = {"slides": [{"id": 1, "title": "T", "bullets": ["b"], "figure": "F7",
                       "talking_points": ["a", "b"]}]}
    good = {"slides": [{"id": 1, "title": "T", "bullets": ["b"], "figure": "F1",
                        "talking_points": ["a", "b"]}]}
    source = "text [Figure F1: a tree] more text"
    batch, attempts = generate_validated(
        MockBackend(responses=[bad, good]), system="s", prompt="p", model_cls=SlideBatch,
        task="slides", max_retries=1, extra_checks=lambda b: check_figures(b, source))
    assert batch.slides[0].figure == "F1"
    assert "F7" in attempts[0].errors[0]


def test_narration_is_told_which_figure_is_on_screen():
    from course2video.config import ScriptConfig
    from course2video.script.generate import generate_script

    deck = Deck.model_validate({"title": "T", "approved": True, "slides": [
        {"id": 1, "title": "A", "bullets": ["b"], "figure": "F1"}]})
    llm = MockBackend(responses=[{"slides": [{"slide_id": 1, "text": "Look at the tree."}]}])
    generate_script(llm, deck, ScriptConfig(), figures={"F1": "A two-stage tree"})
    assert '"figure_on_screen": "A two-stage tree"' in llm.calls[0]["prompt"]


def test_figure_markers_are_not_allowed_in_bullets():
    copied = SlideBatch.model_validate({"slides": [{"id": 1, "title": "T", "figure": "F1",
                                                    "bullets": ["[Figure F1: a tree]"],
                                                    "talking_points": ["a", "b"]}]})
    errors = check_figures(copied, "[Figure F1: a tree]")
    assert any("do not copy" in e for e in errors)
