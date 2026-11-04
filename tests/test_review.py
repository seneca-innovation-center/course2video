import pytest

from course2video.review import ReviewError, deck_to_markdown, markdown_to_deck

HEAD = "# Course\n<!-- language: en -->\n\n## Slide 1: First\n"


def test_continuation_lines_are_kept():
    deck = markdown_to_deck(HEAD + "- a bullet\n  that goes on\nSay: a talking point\nwith a second line\n"
                            "Notes: a note\nand more\n")
    s = deck.slides[0]
    assert s.bullets == ["a bullet that goes on"]
    assert s.talking_points == ["a talking point with a second line"]
    assert s.notes == "a note and more"


def test_multiline_equation_and_explanation():
    deck = markdown_to_deck(HEAD + "- b\n\n$$\nP(A|B) =\n\\frac{P(A \\cap B)}{P(B)}\n$$\n"
                            "> conditional probability\n> continued\n")
    eq = deck.slides[0].equations[0]
    assert eq.latex == "P(A|B) = \\frac{P(A \\cap B)}{P(B)}"
    assert eq.explanation == "conditional probability continued"


def test_numbered_lists_become_bullets():
    deck = markdown_to_deck(HEAD + "1. first\n2) second\n")
    assert deck.slides[0].bullets == ["first", "second"]


def test_free_text_under_a_title_is_rejected_with_its_line_number():
    with pytest.raises(ReviewError) as e:
        markdown_to_deck(HEAD + "this sentence belongs nowhere\n- b\n")
    assert "line 5" in str(e.value) and "belongs nowhere" in str(e.value)


def test_unclosed_equation_and_orphan_explanation_are_rejected():
    with pytest.raises(ReviewError) as e:
        markdown_to_deck(HEAD + "- b\n> explains nothing\n$$ x = 1\n")
    msg = str(e.value)
    assert "line 6" in msg and "without an equation" in msg
    assert "line 7" in msg and "never closed" in msg


def test_line_numbers_match_the_file_with_the_help_comment(good_deck):
    md = deck_to_markdown(good_deck)
    lines = md.splitlines()
    bad_line = next(i for i, x in enumerate(lines, 1) if x.startswith("## Slide 2"))
    lines.insert(bad_line, "stray text")
    with pytest.raises(ReviewError) as e:
        markdown_to_deck("\n".join(lines))
    assert f"line {bad_line + 1}" in str(e.value)


def test_roundtrip_still_exact(good_deck):
    good_deck.slides[0].talking_points = ["Why it matters.", "Example: two coins."]
    assert markdown_to_deck(deck_to_markdown(good_deck)).model_dump() == good_deck.model_dump()


def test_blank_line_ends_a_field():
    with pytest.raises(ReviewError) as e:
        markdown_to_deck(HEAD + "- short bullet\nSay: a talking point\n\n"
                         "The lecturer adds a new paragraph here.\n")
    assert "line 8" in str(e.value) and "new paragraph" in str(e.value)


def test_heading_inside_a_slide_is_rejected():
    with pytest.raises(ReviewError) as e:
        markdown_to_deck(HEAD + "- short bullet\n### Remark\n")
    assert "line 6" in str(e.value) and "Remark" in str(e.value)


def test_explanation_right_after_its_equation_still_works():
    deck = markdown_to_deck(HEAD + "- b\n\n$$ x = 1 $$\n> one\n")
    assert deck.slides[0].equations[0].explanation == "one"
