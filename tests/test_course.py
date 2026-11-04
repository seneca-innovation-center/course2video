import json
from pathlib import Path

import pytest

from course2video.config import Config
from course2video.course import link_problems, load_course, split_numbered
from course2video.course.budget import plan_budget, slides_per_chunk
from course2video.course.manifest import guess_role, pretty_label
from course2video.pipeline import run_stage1, run_stage2
from course2video.review import deck_to_markdown, markdown_to_deck
from course2video.slides.models import Deck

COURSE = Path(__file__).parent / "data" / "course_bayes"


@pytest.mark.parametrize("name, role", [
    ("mit18_05_s22_pset02_sol.pdf", "solutions"),
    ("mit18_05_s22_pset02.pdf", "exercises"),
    ("mit18_05_s22_class03-prep.pdf", "lecture"),
    ("TD3_corrige.pdf", "solutions"),
    ("td3.pdf", "exercises"),
    ("cours/chapitre2.pdf", "lecture"),
    ("TP1.pdf", "practical"),
    ("random.pdf", None),
])
def test_guess_role(name, role):
    assert guess_role(Path(name)) == role


def test_pretty_label():
    assert pretty_label(Path("mit18_05_s22_pset02.pdf")) == "Problem Set 2"
    assert pretty_label(Path("td_3.pdf")) == "TD 3"


def test_course_folder_without_manifest():
    course = load_course(COURSE)
    roles = {d.path.name: d.type for d in course.documents}
    assert roles == {"notes_bayes.md": "lecture", "td1.md": "exercises", "td1_sol.md": "solutions"}
    sol = course.of_type("solutions")[0]
    assert sol.solves.name == "td1.md"
    assert any("guessed" in w for w in course.warnings)


def test_manifest_wins(tmp_path):
    (tmp_path / "a.md").write_text("# A\n\nText.")
    (tmp_path / "b.md").write_text("Exercise 1. Do it.")
    (tmp_path / "c.md").write_text("Exercise 1. Done.")
    (tmp_path / "course.yaml").write_text(
        "title: My course\nlanguage: fr\ntarget_minutes: 12\ndocuments:\n"
        "  - {path: a.md, type: lecture}\n"
        "  - {path: b.md, type: exercises, label: Feuille 1, select: [1]}\n"
        "  - {path: c.md, type: solutions, solves: b.md}\n")
    course = load_course(tmp_path)
    assert (course.title, course.language, course.target_minutes) == ("My course", "fr", 12)
    ex = course.of_type("exercises")[0]
    assert ex.label == "Feuille 1" and ex.select == [1]
    assert course.of_type("solutions")[0].solves == ex.path


def test_split_numbered_titles_skip_points():
    md = ("Problem 1. (20: 10,10 pts.) (‘Binary’ paradox)\nText one.\n"
          "Problem 2. (15 pts.) (The blue taxi)\nText two.\n"
          "Problem 3. (20 pts.) (T rees of cards)\nThree.")
    blocks = split_numbered(md)
    assert [blocks[n][0] for n in (1, 2, 3)] == ["Binary paradox", "The blue taxi", "Trees of cards"]
    assert blocks[2][1].startswith("Problem 2.") and "Text two." in blocks[2][1]


def test_link_by_number_with_warnings():
    ex = (COURSE / "exercises/td1.md").read_text()
    sol = (COURSE / "solutions/td1_sol.md").read_text()
    problems, warnings = link_problems(ex, sol, "Exercise sheet 1", select=[1, 2, 9])
    assert [(p.number, p.title, p.solution is not None) for p in problems] == [
        (1, "Two coins", True), (2, "Medical test", True), (3, "Extra", False)]
    assert "1/3" in problems[0].solution and "0.17" in problems[1].solution
    assert problems[1].ref == "Exercise sheet 1, Problem 2"
    assert any("no solution found for problem 3" in w for w in warnings)
    assert any("selected problem 9 does not exist" in w for w in warnings)


def test_budget_for_20_minutes():
    b = plan_budget(20, source_words=6000, n_problems=3, n_sections_hint=8)
    assert 2800 <= b.content_words <= 3200
    assert b.words_per_slide == 220
    assert b.slides_per_problem == 2
    assert 6 <= b.theory_slides <= 10
    assert not b.warnings


def test_budget_warns_when_sources_are_too_short():
    b = plan_budget(20, source_words=900, n_problems=0)
    assert b.warnings and "shorter than the target" in b.warnings[0]


def test_slides_per_chunk_is_proportional():
    assert slides_per_chunk(10, [1000, 3000, 1000]) == [2, 6, 2]
    assert slides_per_chunk(2, [10, 10, 10]) == [1, 1, 1]


def _cfg():
    cfg = Config()
    cfg.render.width, cfg.render.height = 640, 360
    return cfg


def test_course_pipeline_with_mock(tmp_path):
    st = run_stage1(COURSE, tmp_path, _cfg())
    assert st["stage"] == "awaiting_review" and st["problems"] == 2
    index = json.loads((tmp_path / "course_index.json").read_text())
    assert [d["type"] for d in index["documents"]] == ["exercises", "lecture", "solutions"]
    assert [p["used"] for p in index["problems"]] == [True, True, False]
    assert sorted((tmp_path / "parsed").glob("*.md"))

    deck = Deck.model_validate_json((tmp_path / "slides.json").read_text())
    kinds = [s.kind for s in deck.slides]
    assert kinds[0] == "theory"
    assert kinds.count("exercise") == 2 and kinds.count("solution") == 4
    ex2 = [s for s in deck.slides if s.kind == "exercise"][1]
    assert ex2.source_doc == "TD 1, Problem 2"
    assert ex2.source_section == "Worked Problem 2: Medical test"
    assert [s.id for s in deck.slides] == list(range(1, len(deck.slides) + 1))

    assert markdown_to_deck(deck_to_markdown(deck)).model_dump() == deck.model_dump()

    run_stage2(tmp_path, _cfg(), source="md", video=False)
    plan = json.loads((tmp_path / "lecture_plan.json").read_text())
    practise = [f for f in plan if f["kind"] == "section" and "practise" in f["narration"]]
    assert len(practise) == 2
    assert "TD 1, Problem 2" in practise[1]["narration"]


def test_target_minutes_flows_into_budget(tmp_path):
    cfg = _cfg()
    cfg.lecture.target_minutes = 5
    run_stage1(COURSE, tmp_path, cfg)
    meta = json.loads((tmp_path / "meta.json").read_text())
    assert meta["budget"]["target_minutes"] == 5
    assert meta["budget"]["warnings"]


def test_titles_keep_apostrophes_but_drop_wrapping_quotes():
    blocks = split_numbered("Problem 1. (20 pts.) ('Binary' paradox)\nx\nProblem 2. (Bayes' rule)\ny")
    assert blocks[1][0] == "Binary paradox"
    assert blocks[2][0] == "Bayes' rule"


def test_grounding_flags_unsupported_talking_points():
    from course2video.slides.grounding import check_grounding

    deck = Deck.model_validate({"title": "T", "slides": [
        {"id": 1, "title": "A", "bullets": ["b"],
         "talking_points": ["The prior is updated into the posterior.",
                            "Quantum entanglement explains the coffee market."]},
        {"id": 2, "title": "P", "bullets": ["b"], "kind": "solution", "source_doc": "TD 1, Problem 1",
         "talking_points": ["So the answer is 2/6, the same as one third.",
                            "So the answer is 0.37."]}]})
    lecture = (COURSE / "lecture/notes_bayes.md").read_text()
    source = r"So the answer is one third, \frac { 1 } { 3 } , the same in both."
    report = check_grounding(deck, lecture, {"TD 1, Problem 1": source})
    tps = report["slides"][0]["talking_points"]
    assert not tps[0]["flagged"] and tps[1]["flagged"]
    sol = report["slides"][1]["talking_points"]
    assert not sol[0]["flagged"]
    assert sol[1]["numbers_not_in_source"] == ["0.37"] or "37/100" in sol[1]["numbers_not_in_source"]
    assert report["flagged_slides"] == [1, 2]


def test_numbers_are_read_from_docling_latex():
    from fractions import Fraction

    from course2video.slides.grounding import numbers

    assert Fraction(32, 49) in numbers(r"= \frac { 3 2 } { 4 9 } ,")
    assert Fraction("0.99") in numbers("0 . 9 9 times")
    assert Fraction(83, 1000) in numbers("about 8.3%")
    assert Fraction(83, 1000) in numbers(r"\approx 8 . 3 \%")
    assert Fraction(20, 217) not in numbers("0.9 × 0.005 / 0.05425")
    assert Fraction(3, 8) in numbers("We know that P(A) = 3/8. Since")


def test_cli_language_is_used_for_a_folder_without_language(tmp_path):
    run_stage1(COURSE, tmp_path, _cfg(), language="fr")
    assert Deck.model_validate_json((tmp_path / "slides.json").read_text()).language == "fr"


def test_course_yaml_language_wins_over_cli(tmp_path):
    src = tmp_path / "course"
    src.mkdir()
    (src / "notes.md").write_text("# T\n\n## 1. A\n\nSome text here. More text there.")
    (src / "course.yaml").write_text("title: T\nlanguage: es\ndocuments:\n"
                                     "  - {path: notes.md, type: lecture}\n")
    run_stage1(src, tmp_path / "out", _cfg(), language="fr")
    assert Deck.model_validate_json((tmp_path / "out/slides.json").read_text()).language == "es"


FRENCH = Path(__file__).parent.parent / "examples" / "cours_probabilites"


def test_french_course_folder_end_to_end_with_mock(tmp_path):
    import shutil

    src = tmp_path / "cours"
    shutil.copytree(FRENCH, src)
    (src / "course.yaml").unlink()
    run_stage1(src, tmp_path / "out", _cfg(), language="fr")
    out = tmp_path / "out"
    index = json.loads((out / "course_index.json").read_text())
    assert sorted(d["type"] for d in index["documents"]) == ["exercises", "lecture", "solutions"]
    assert [p["used"] for p in index["problems"]] == [True, True, True]
    deck = Deck.model_validate_json((out / "slides.json").read_text())
    assert deck.language == "fr"
    ex2 = [s for s in deck.slides if s.kind == "exercise"][1]
    assert ex2.source_doc == "TD 3, Exercice 2"
    assert ex2.source_section == "Exercice corrigé 2: Test de dépistage"
    run_stage2(out, _cfg(), video=False)
    plan = json.loads((out / "lecture_plan.json").read_text())
    assert plan[0]["narration"].startswith("Bienvenue.")
    practise = [f["narration"] for f in plan if f["kind"] == "section" and "Entraînons" in f["narration"]]
    assert len(practise) == 3 and "TD 3, Exercice 2 : Test de dépistage" in practise[1]


def test_voice_follows_the_course_language():
    from course2video.config import TTSConfig
    from course2video.tts import piper_voice_for

    cfg = TTSConfig()
    assert piper_voice_for(cfg, "fr").endswith("fr_FR-siwis-medium.onnx")
    assert piper_voice_for(cfg, "en-GB").endswith("en_US-ljspeech-medium.onnx")
    assert piper_voice_for(cfg, "de") == cfg.piper_model
