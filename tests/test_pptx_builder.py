from PIL import Image
from pptx import Presentation

from course2video.config import LectureConfig, RenderConfig
from course2video.render.lecture import build_frames
from course2video.render.pptx_builder import build_pptx
from course2video.render.slide_images import render_frames
from course2video.script.models import Script

SCRIPT = Script.model_validate({"slides": [
    {"slide_id": 1, "text": "Narration one."}, {"slide_id": 2, "text": "Narration two."}]})


def _two_section_deck(good_deck):
    good_deck.slides[1].source_section = "2. Subspaces"
    return good_deck


def test_pptx_follows_lecture_structure(good_deck, tmp_path):
    deck = _two_section_deck(good_deck)
    frames = build_frames(deck, SCRIPT, LectureConfig())
    out = build_pptx(frames, tmp_path / "deck.pptx")
    prs = Presentation(str(out))
    titles = [s.shapes.title.text for s in prs.slides]
    assert titles == ["Vector Spaces", "Outline", "Vectors in R^n", "Vectors in R^n",
                      "Subspaces", "Subspaces", "Summary"]
    notes = [s.notes_slide.notes_text_frame.text for s in prs.slides]
    assert notes[3] == "Narration one."
    assert notes[0].startswith("Welcome.")
    content = prs.slides[3]
    text = " ".join(sh.text_frame.text for sh in content.shapes if sh.has_text_frame)
    assert "component by component" in text
    has_pic = any(sh.shape_type == 13 for sh in content.shapes)
    assert has_pic or "u_1 + v_1" in text


def test_content_only_when_structure_disabled(good_deck, tmp_path):
    cfg = LectureConfig(title_slide=False, agenda=False, section_dividers=False, closing=False)
    frames = build_frames(good_deck, SCRIPT, cfg)
    prs = Presentation(str(build_pptx(frames, tmp_path / "deck.pptx")))
    assert [s.shapes.title.text for s in prs.slides] == ["Vectors in R^n", "Subspaces"]


def test_pillow_renders_one_image_per_frame(good_deck, tmp_path):
    deck = _two_section_deck(good_deck)
    frames = build_frames(deck, SCRIPT, LectureConfig(presenter="Dr. A. Lecturer"))
    paths = render_frames(frames, deck.title, deck.language, tmp_path / "images",
                          RenderConfig(width=960, height=540))
    assert len(paths) == len(frames) == 7
    assert paths[0].name == "frame_001.png"
    img = Image.open(paths[-1])
    assert img.size == (960, 540)
    assert img.getpixel((950, 539)) == (232, 163, 23)
