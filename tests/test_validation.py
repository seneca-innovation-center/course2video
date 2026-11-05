import json

import pytest

from course2video.config import SlidesConfig
from course2video.llm.base import LLMError, relax_schema
from course2video.llm.mock_backend import MockBackend
from course2video.slides.generate import chunk_markdown, generate_deck
from course2video.slides.models import SlideBatch
from course2video.slides.validate import (
    GenerationFailed,
    extract_json,
    generate_validated,
    validate_deck_file,
)

VALID = {"slides": [{"id": 1, "title": "T", "bullets": ["b"], "equations": [],
                     "talking_points": ["Why it matters.", "Example: two coins."]}]}


def _run(llm, retries=2):
    return generate_validated(
        llm, system="s", prompt="p", model_cls=SlideBatch, task="slides", max_retries=retries
    )


def test_extract_json_handles_fences_and_prose():
    assert extract_json('```json\n{"a": 1}\n```') == {"a": 1}
    assert extract_json('Here you go: {"a": 1} hope it helps') == {"a": 1}
    with pytest.raises(json.JSONDecodeError):
        extract_json("no json here")


def test_valid_first_time():
    llm = MockBackend(responses=[VALID])
    batch, attempts = _run(llm)
    assert len(batch.slides) == 1
    assert [a.ok for a in attempts] == [True]


def test_retry_then_success_feeds_errors_back():
    bad_schema = {"slides": [{"id": 1, "title": "T", "bullets": []}]}
    llm = MockBackend(responses=["not json at all", bad_schema, VALID])
    batch, attempts = _run(llm)
    assert [a.ok for a in attempts] == [False, False, True]
    assert "not valid JSON" in attempts[0].errors[0]
    assert any("bullets" in e for e in attempts[1].errors)
    assert "rejected by the validator" in llm.calls[1]["prompt"]
    assert "bullets" in llm.calls[2]["prompt"]


def test_backend_errors_are_retried():
    llm = MockBackend(responses=[LLMError("timeout"), VALID])
    _, attempts = _run(llm)
    assert [a.ok for a in attempts] == [False, True]


def test_gives_up_cleanly_after_max_retries():
    llm = MockBackend(responses=["{}"] * 10)
    with pytest.raises(GenerationFailed) as exc:
        _run(llm, retries=2)
    assert len(exc.value.attempts) == 3
    assert len(llm.calls) == 3


def test_latex_check_rejects_unbalanced_braces():
    bad = {"slides": [{"id": 1, "title": "T", "bullets": ["b"],
                       "equations": [{"latex": r"\frac{a}{b", "explanation": "x"}]}]}
    llm = MockBackend(responses=[bad, VALID])
    from course2video.slides.validate import check_latex

    _, attempts = generate_validated(llm, system="s", prompt="p", model_cls=SlideBatch,
                                     task="slides", max_retries=1, extra_checks=check_latex)
    assert "unbalanced braces" in attempts[0].errors[0]


def test_generate_deck_renumbers_across_chunks():
    md = "# C\n\n## A\n" + "x. " * 50 + "\n\n## B\n" + "y. " * 50
    llm = MockBackend(responses=[VALID, VALID])
    deck, _ = generate_deck(llm, md, SlidesConfig(chunk_chars=200), title="C")
    assert [s.id for s in deck.slides] == [1, 2]


def test_chunking_never_drops_text():
    md = "# T\nintro\n## A\n" + "a" * 500 + "\n## B\nbbb\n## C\nccc\n"
    chunks = chunk_markdown(md, max_chars=200)
    assert "".join(chunks) == md
    assert len(chunks) >= 2


def test_validate_deck_file(good_deck_dict):
    deck, errors = validate_deck_file(json.dumps(good_deck_dict))
    assert deck is not None and not errors
    deck, errors = validate_deck_file("{ broken")
    assert deck is None and "not valid JSON" in errors[0]


def test_relax_schema_strips_constraints():
    relaxed = relax_schema(SlideBatch.model_json_schema())
    text = json.dumps(relaxed)
    for key in ("maxLength", "minItems", "maxItems", "minimum"):
        assert key not in text
    slide = relaxed["$defs"]["Slide"]
    assert slide["additionalProperties"] is False
    assert set(slide["required"]) == set(slide["properties"])
    assert "title" in slide["properties"]
    assert "title" not in slide["properties"]["bullets"]


def test_script_that_is_too_long_is_retried_then_accepted():
    from course2video.config import ScriptConfig
    from course2video.script.generate import generate_script
    from course2video.slides.models import Deck

    deck = Deck.model_validate({"title": "T", "approved": True,
                                "slides": [{"id": 1, "title": "A", "bullets": ["b"]}]})
    long = {"slides": [{"slide_id": 1, "text": "word " * 300}]}
    short = {"slides": [{"slide_id": 1, "text": "A short narration."}]}
    llm = MockBackend(responses=[long, short])
    script, attempts = generate_script(llm, deck, ScriptConfig(), words_per_slide=100)
    assert script.for_slide(1) == "A short narration."
    assert "Shorten every slide by about 67%" in attempts[0][0].errors[0]

    llm = MockBackend(responses=[long, long])
    script, attempts = generate_script(llm, deck, ScriptConfig(), words_per_slide=100)
    assert len(script.for_slide(1).split()) == 300
    assert attempts[0][-1].ok and attempts[0][-1].warnings


def test_lecture_style_sends_long_bullets_back():
    from course2video.slides.validate import check_lecture_style

    wordy = {"slides": [{"id": 1, "title": "T",
                         "bullets": ["this bullet is a long sentence that explains everything in "
                                     "detail instead of showing a key point"],
                         "talking_points": ["one"]}]}
    errors = check_lecture_style(SlideBatch.model_validate(wordy), max_bullet_words=12)
    assert any("move the explanation to talking_points" in e for e in errors)
    assert any("at least 2 points" in e for e in errors)
    assert check_lecture_style(SlideBatch.model_validate(VALID), max_bullet_words=12) == []


def test_invented_example_is_sent_back_once():
    from course2video.slides.validate import check_examples

    invented = {"slides": [{"id": 1, "title": "T", "bullets": ["b"], "talking_points": [
        "Why it matters.", "Example: draw a red card then a king, P = 2/26 = 1/13."]}]}
    source_example = {"slides": [{"id": 1, "title": "T", "bullets": ["b"], "talking_points": [
        "Why it matters.", "Example: a fair die, even result, P(6 | even) = 1/3."]}]}
    source = "Example. A fair die: knowing the result is even, the probability of 6 is 1/3."
    assert check_examples(SlideBatch.model_validate(invented), source)
    assert check_examples(SlideBatch.model_validate(source_example), source) == []


def test_generate_deck_retries_invented_example_then_accepts():
    from course2video.config import SlidesConfig

    invented = {"slides": [{"id": 1, "title": "T", "bullets": ["b"], "talking_points": [
        "Why.", "Example: 70% red balls and 30% blue."]}]}
    llm = MockBackend(responses=[invented, invented])
    deck, attempts = generate_deck(llm, "# C\n\n## A\nSome text.", SlidesConfig(), title="C")
    assert len(llm.calls) == 2 and "not in the source" in llm.calls[1]["prompt"]
    assert attempts[0][-1].ok and attempts[0][-1].warnings
