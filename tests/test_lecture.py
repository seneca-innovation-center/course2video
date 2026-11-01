from course2video.config import LectureConfig
from course2video.render.lecture import (
    build_frames,
    display_section_name,
    group_sections,
    speakable,
)
from course2video.script.models import Script
from course2video.slides.models import Deck


def _deck(sections: list[str], language: str = "en") -> Deck:
    return Deck.model_validate({
        "title": "Probability", "language": language,
        "slides": [{"id": i + 1, "title": f"S{i + 1}", "bullets": ["b"], "source_section": sec}
                   for i, sec in enumerate(sections)],
    })


def _script(n: int) -> Script:
    return Script.model_validate({"slides": [{"slide_id": i + 1, "text": f"T{i + 1}"}
                                             for i in range(n)]})


def test_display_section_name():
    assert display_section_name("3. Subspaces") == "Subspaces"
    assert display_section_name("## 1.2 Basis and dimension") == "Basis and dimension"
    assert display_section_name("Chapter 4: Random variables") == "Random variables"
    assert display_section_name("Introduction") == "Introduction"


def test_grouping_keeps_order_and_continues_on_empty():
    deck = _deck(["1. Events", "1. Events", "", "2. Conditional probability", "3. Bayes"])
    secs = group_sections(deck)
    assert [s.name for s in secs] == ["Events", "Conditional probability", "Bayes"]
    assert [s.slide_ids for s in secs] == [[1, 2, 3], [4], [5]]


def test_frame_sequence():
    deck = _deck(["1. Events", "1. Events", "2. Bayes"])
    frames = build_frames(deck, _script(3), LectureConfig())
    assert [f.kind for f in frames] == [
        "title", "agenda", "section", "content", "content", "section", "content", "closing"]
    assert frames[1].narration == "Here is the plan. We will go through 2 parts: Events and Bayes."
    assert frames[2].narration == "Let's start with part 1: Events."
    assert frames[5].narration == "Now we move on to part 2: Bayes."
    assert frames[3].narration == "T1"
    assert [f.section_index for f in frames] == [None, None, 0, 0, 0, 1, 1, None]
    assert [f.index for f in frames] == list(range(8))
    assert all(f.total == 8 for f in frames)


def test_single_topic_has_no_outline_or_dividers():
    frames = build_frames(_deck(["Intro", "Intro"]), _script(2), LectureConfig())
    assert [f.kind for f in frames] == ["title", "content", "content", "closing"]


def test_french_templates():
    frames = build_frames(_deck(["1. Événements", "2. Bayes"], "fr"), _script(2), LectureConfig())
    assert frames[0].narration.startswith("Bienvenue.")
    assert frames[2].narration == "Commençons par la partie 1 : Événements."


def test_speakable():
    assert speakable("Vectors in R^n") == "Vectors in R n"
    assert speakable("x^{2}") == "x 2"


def test_section_named_like_course_becomes_introduction():
    deck = _deck(["Probability", "1. Events", "2. Bayes"])
    frames = build_frames(deck, _script(3), LectureConfig())
    assert frames[1].items == ["Introduction", "Events", "Bayes"]


def test_mathtext_normalisation():
    from course2video.render.equations import normalize_for_mathtext

    docling = r"P ( A ) = \sum _ { i = 1 } ^ { n } P ( A \ | \ B _ { i } )"
    assert normalize_for_mathtext(docling) == r"P ( A ) = \sum_{i = 1}^{n} P ( A \ | \ B_{i} )"
    noisy = r"\frac { a } { b } \\ \intertext { a g i v e }"
    assert normalize_for_mathtext(noisy) == r"\frac{a}{b}"


def test_title_heading_with_authors_becomes_introduction():
    deck = _deck(["Probability Class 3, J. Orloff", "1. Events", "2. Bayes"])
    frames = build_frames(deck, _script(3), LectureConfig())
    assert frames[1].items[0] == "Introduction"


def test_subsections_and_unnumbered_headings_stay_in_their_chapter():
    deck = _deck(["1 Goals", "2 Conditional", "2.1 Detail", "Proof of it", "3 Bayes", "3.1 Fallacy"])
    assert [s.name for s in group_sections(deck)] == ["Goals", "Conditional", "Bayes"]
    assert [s.slide_ids for s in group_sections(deck)] == [[1], [2, 3, 4], [5, 6]]


def test_unnumbered_documents_keep_every_heading():
    deck = _deck(["Events", "Bayes", "Bayes"])
    assert [s.name for s in group_sections(deck)] == ["Events", "Bayes"]


def test_chapter_map_follows_the_document():
    from course2video.slides.generate import assign_chapters

    md = ("## 3 Multiplication Rule\n\n## 4 Law of Total Probability\n\n"
          "## Law of Total Probability\n\n## Probability urns\n\n## 5 Trees\n\n## 5.1 Shorthand\n")
    deck = _deck(["Law of Total Probability", "Probability urns", "5.1 Shorthand", "Unknown"])
    assign_chapters(deck.slides, md)
    assert [s.source_section for s in deck.slides] == [
        "4 Law of Total Probability", "4 Law of Total Probability", "5 Trees", "Unknown"]


def test_tfrac_is_rendered_as_frac():
    from course2video.render.equations import normalize_for_mathtext

    assert normalize_for_mathtext(r"\tfrac12\cdot\dfrac{3}{7}") == r"\frac{1}{2}\cdot\frac{3}{7}"


def test_frac_shorthand_forms():
    from course2video.render.equations import normalize_for_mathtext

    assert normalize_for_mathtext(r"\frac1{14}+\frac{3}7") == r"\frac{1}{14}+\frac{3}{7}"
