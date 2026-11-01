from course2video.config import AlignmentConfig
from course2video.script.alignment import check_alignment, content_words
from course2video.script.models import Script


def test_content_words_drops_stopwords_and_plurals():
    assert content_words("The vectors are added") == {"vector", "added"}


def test_full_coverage(good_deck):
    script = Script.model_validate({"slides": [
        {"slide_id": 1, "text": "A vector is an ordered list of n real numbers. Vectors are "
                                "added component by component. Addition works on each "
                                "component separately."},
        {"slide_id": 2, "text": "A subspace contains the zero vector and is closed under "
                                "addition and scalar multiplication."},
    ]})
    r = check_alignment(good_deck, script, AlignmentConfig())
    assert r["overall_coverage"] == 1.0
    assert r["flagged_slides"] == []


def test_partial_coverage_is_flagged(good_deck):
    script = Script.model_validate({"slides": [
        {"slide_id": 1, "text": "A vector is an ordered list of n real numbers."},
        {"slide_id": 2, "text": "Today we talk about the weather in Paris."},
    ]})
    r = check_alignment(good_deck, script, AlignmentConfig())
    s1, s2 = r["slides"]
    assert s1["coverage"] == round(1 / 3, 3)
    assert s2["coverage"] == 0.0
    assert r["flagged_slides"] == [1, 2]
    assert r["overall_coverage"] == 0.2
    assert s2["novel_word_ratio"] > 0.9


def test_missing_script_entry_counts_as_uncovered(good_deck):
    script = Script.model_validate({"slides": [{"slide_id": 1, "text": "x"}]})
    r = check_alignment(good_deck, script, AlignmentConfig())
    assert r["slides"][1]["coverage"] == 0.0
