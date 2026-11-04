import json

import pytest

from course2video.config import Config
from course2video.pipeline import run_stage1, run_stage2
from course2video.render.reveal import reveal_times
from course2video.render.video_assembly import _listing

from .conftest import requires_ffmpeg

NARRATION = ("Let us start with conditional probability. Some intro words follow here. "
             "Then the multiplication rule appears in the middle. Finally Bayes theorem "
             "inverts conditional probabilities at the end.")


def test_bullets_appear_when_the_narration_reaches_them():
    bullets = ["Conditional probability", "Multiplication rule", "Bayes theorem inverts"]
    times = reveal_times(NARRATION, bullets, speech_s=20.0)
    assert times[0] == 0.0
    mult = NARRATION.index("multiplication") / len(NARRATION) * 20
    bayes = NARRATION.index("theorem") / len(NARRATION) * 20
    assert times[1] == pytest.approx(mult, abs=0.5)
    assert times[2] == pytest.approx(bayes, abs=0.5)


def test_reveal_order_and_gaps_hold_when_words_are_missing_or_out_of_order():
    times = reveal_times("Bayes first, then nothing else at all.",
                         ["intro", "never mentioned", "Bayes"], speech_s=10.0)
    assert times[0] == 0.0
    assert all(b - a >= 1.0 - 1e-9 for a, b in zip(times, times[1:], strict=False))
    assert times[-1] <= 9.0


def test_listing_switches_images_within_a_slide(tmp_path):
    a, b1, b2 = tmp_path / "a.png", tmp_path / "b1.png", tmp_path / "b2.png"
    text = _listing([a, b2], [3.0, 5.0], {1: [(b1, 0.0), (b2, 2.0)]})
    lines = text.strip().splitlines()
    assert lines[0].endswith("a.png'") and lines[1] == "duration 3.000000"
    assert lines[2].endswith("b1.png'") and lines[3] == "duration 2.000000"
    assert lines[4].endswith("b2.png'") and lines[5] == "duration 3.000000"
    assert lines[6].endswith("b2.png'")


@requires_ffmpeg
def test_reveal_keeps_the_video_length(sample_pdf, tmp_path):
    cfg = Config()
    cfg.render.width, cfg.render.height = 640, 360
    cfg.render.reveal_bullets = True
    run_stage1(sample_pdf, tmp_path, cfg)
    run_stage2(tmp_path, cfg)
    meta = json.loads((tmp_path / "meta.json").read_text())
    assert meta["reveal"]
    first = next(iter(meta["reveal"].values()))
    assert first[0] == 0.0 and first == sorted(first)
    assert list((tmp_path / "images").glob("frame_*_b1.png"))
    from course2video.tts.base import wav_duration

    n = len(json.loads((tmp_path / "lecture_plan.json").read_text()))
    speech = sum(wav_duration(p) for p in (tmp_path / "audio").glob("*.wav"))
    assert meta["video"]["duration_s"] == pytest.approx(speech + n * 0.6, abs=0.05)
