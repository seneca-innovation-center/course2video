import copy
import json
from pathlib import Path

import jsonschema
import pytest
from pydantic import ValidationError

from course2video.cli import main
from course2video.script.models import Script
from course2video.slides.models import Deck

ROOT = Path(__file__).parent.parent


def test_good_deck_passes(good_deck_dict):
    deck = Deck.model_validate(good_deck_dict)
    assert len(deck.slides) == 2
    assert deck.approved is False


@pytest.mark.parametrize(
    "mutate",
    [
        lambda d: d["slides"][0].update(bullets=[]),
        lambda d: d["slides"][0].update(bullets=["x"] * 8),
        lambda d: d["slides"][0].update(bullets=["   "]),
        lambda d: d["slides"][0].update(bullets=["x" * 201]),
        lambda d: d["slides"][0].update(title=""),
        lambda d: d["slides"][1].update(id=1),
        lambda d: d["slides"][0].update(colour="red"),
        lambda d: d["slides"][0]["equations"][0].pop("explanation"),
        lambda d: d.update(slides=[]),
    ],
)
def test_bad_deck_fails(good_deck_dict, mutate):
    d = copy.deepcopy(good_deck_dict)
    mutate(d)
    with pytest.raises(ValidationError):
        Deck.model_validate(d)


def test_committed_schemas_match_models(tmp_path):
    assert main(["schemas", "--out", str(tmp_path)]) == 0
    for name in ("slide", "script"):
        committed = json.loads((ROOT / "schemas" / f"{name}.schema.json").read_text())
        fresh = json.loads((tmp_path / f"{name}.schema.json").read_text())
        assert committed == fresh, f"run `course2video schemas` to update {name}.schema.json"


def test_json_schema_agrees_with_pydantic(good_deck_dict):
    schema = json.loads((ROOT / "schemas" / "slide.schema.json").read_text())
    jsonschema.validate(good_deck_dict, schema)
    bad = copy.deepcopy(good_deck_dict)
    bad["slides"][0]["bullets"] = []
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(bad, schema)


def test_script_model():
    s = Script.model_validate({"slides": [{"slide_id": 1, "text": "Hello."}]})
    assert s.for_slide(1) == "Hello."
    with pytest.raises(KeyError):
        s.for_slide(2)
