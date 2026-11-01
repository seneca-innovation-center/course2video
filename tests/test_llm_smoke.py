import json
import os

import pytest

from course2video.config import load_config
from course2video.pipeline import run_stage1, run_stage2

pytestmark = pytest.mark.llm


@pytest.fixture
def cfg():
    path = os.environ.get("C2V_SMOKE_CONFIG")
    if not path:
        pytest.skip("set C2V_SMOKE_CONFIG to a config with a real LLM backend")
    return load_config(path)


def test_real_llm_slides_and_script(cfg, sample_pdf, tmp_path):
    st = run_stage1(sample_pdf, tmp_path, cfg)
    assert st["slides"] >= 3
    deck = json.loads((tmp_path / "slides.json").read_text())
    titles = " ".join(s["title"].lower() for s in deck["slides"])
    assert "subspace" in titles or "basis" in titles or "span" in titles
    assert any(s["equations"] for s in deck["slides"]), "expected at least one equation"

    run_stage2(tmp_path, cfg, video=False)
    report = json.loads((tmp_path / "alignment.json").read_text())
    assert report["overall_coverage"] >= 0.6
