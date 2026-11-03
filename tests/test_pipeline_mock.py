import json

import pytest

from course2video.cli import main
from course2video.config import Config
from course2video.pipeline import run_stage1, run_stage2
from course2video.render.subtitles import build_srt
from course2video.review import ReviewError, deck_to_markdown, markdown_to_deck
from course2video.tts.base import wav_duration

from .conftest import requires_ffmpeg


def _cfg() -> Config:
    cfg = Config()
    cfg.render.width, cfg.render.height = 640, 360
    return cfg


def test_stage1_stops_for_review(sample_pdf, tmp_path):
    st = run_stage1(sample_pdf, tmp_path, _cfg())
    assert st["stage"] == "awaiting_review"
    deck = json.loads((tmp_path / "slides.json").read_text())
    assert deck["approved"] is False
    assert deck["title"] == "Vector Spaces: A Short Introduction"
    assert len(deck["slides"]) >= 5
    assert (tmp_path / "slides.md").exists()
    assert not (tmp_path / "script.json").exists()


def test_invalid_review_edit_is_rejected(sample_pdf, tmp_path):
    run_stage1(sample_pdf, tmp_path, _cfg())
    d = json.loads((tmp_path / "slides.json").read_text())
    d["slides"][0]["bullets"] = []
    (tmp_path / "slides.json").write_text(json.dumps(d))
    with pytest.raises(ReviewError):
        run_stage2(tmp_path, _cfg(), video=False)
    assert not (tmp_path / "script.json").exists()


def test_markdown_review_roundtrip(good_deck):
    md = deck_to_markdown(good_deck)
    back = markdown_to_deck(md)
    assert back.model_dump() == good_deck.model_dump()


def test_markdown_edit_is_applied(sample_pdf, tmp_path):
    run_stage1(sample_pdf, tmp_path, _cfg())
    md = (tmp_path / "slides.md").read_text()
    md = md.replace("## Slide 1:", "## Slide 1: EDITED", 1)
    (tmp_path / "slides.md").write_text(md)
    run_stage2(tmp_path, _cfg(), source="md", video=False)
    deck = json.loads((tmp_path / "slides.json").read_text())
    assert deck["approved"] is True
    assert deck["slides"][0]["title"].startswith("EDITED")
    assert (tmp_path / "deck.pptx").exists()
    assert json.loads((tmp_path / "alignment.json").read_text())["overall_coverage"] > 0.9


@requires_ffmpeg
def test_full_pipeline_produces_video(sample_pdf, tmp_path):
    out = tmp_path / "out"
    rc = main(["run", str(sample_pdf), "--out", str(out), "--auto-approve", "--llm", "mock",
               "--tts", "stub"])
    assert rc == 0
    for name in ("parsed.md", "slides.json", "script.json", "alignment.json", "deck.pptx",
                 "video.mp4", "subtitles.srt", "meta.json"):
        assert (out / name).exists(), name
    meta = json.loads((out / "meta.json").read_text())
    plan = json.loads((out / "lecture_plan.json").read_text())
    kinds = [f["kind"] for f in plan]
    assert kinds[:3] == ["title", "agenda", "section"] and kinds[-1] == "closing"
    assert kinds.count("content") == meta["slides"]["count"]
    assert kinds.count("section") >= 5
    n = len(plan)
    assert len(list((out / "images").glob("*.png"))) == n
    assert len(list((out / "audio").glob("*.wav"))) == n
    speech = sum(wav_duration(p) for p in (out / "audio").glob("*.wav"))
    assert meta["video"]["duration_s"] == pytest.approx(speech + n * 0.6, abs=0.05)
    srt = (out / "subtitles.srt").read_text()
    assert srt.split("\n")[2].startswith("Welcome.")
    assert json.loads((out / "state.json").read_text())["stage"] == "done"


def test_srt_timing():
    texts = ["First sentence. Second one.", "Third."]
    srt = build_srt(texts, durations=[4.0, 2.0], speech_durations=[3.0, 1.5])
    blocks = srt.strip().split("\n\n")
    assert len(blocks) == 3
    assert blocks[0].splitlines()[1].startswith("00:00:00,000 --> ")
    assert blocks[2].splitlines()[1] == "00:00:04,000 --> 00:00:05,500"


def test_render_command_rebuilds_without_llm(sample_pdf, tmp_path, monkeypatch):
    from course2video.llm.mock_backend import MockBackend

    run_stage1(sample_pdf, tmp_path, _cfg())
    run_stage2(tmp_path, _cfg(), video=False)
    script_before = (tmp_path / "script.json").read_text()
    import course2video.pipeline as pipeline

    monkeypatch.setattr(pipeline, "get_backend", lambda cfg: MockBackend(responses=[]))
    cfg = _cfg()
    cfg.lecture.agenda = False
    assert main(["render", str(tmp_path), "--no-video"]) == 0
    assert (tmp_path / "script.json").read_text() == script_before
    plan = json.loads((tmp_path / "lecture_plan.json").read_text())
    assert plan[0]["kind"] == "title"


def test_continue_can_be_retried_after_a_stage2_failure(sample_pdf, tmp_path):
    from course2video.llm.base import LLMError
    from course2video.llm.mock_backend import MockBackend
    from course2video.slides.validate import GenerationFailed

    run_stage1(sample_pdf, tmp_path, _cfg())
    with pytest.raises(GenerationFailed):
        run_stage2(tmp_path, _cfg(), llm=MockBackend(responses=[LLMError("timeout")] * 10),
                   video=False)
    assert json.loads((tmp_path / "state.json").read_text())["stage"] == "approved"
    run_stage2(tmp_path, _cfg(), video=False)
    assert json.loads((tmp_path / "state.json").read_text())["stage"] == "script_done"


@requires_ffmpeg
def test_video_audio_and_subtitles_stay_in_sync(tmp_path):
    import subprocess

    from course2video.render.video_assembly import assemble_video
    from course2video.tts.backends import StubTTS

    folder = tmp_path / "Lecturer's course"
    tts = StubTTS(sample_rate=22050)
    from PIL import Image

    images, audios = [], []
    for i in range(30):
        img = folder / f"f{i}.png"
        folder.mkdir(exist_ok=True)
        Image.new("RGB", (64, 36), (i * 8, 0, 0)).save(img)
        images.append(img)
        audios.append(tts.synthesize("word " * (3 + i % 7), folder / f"a{i}.wav"))
    out = folder / "video.mp4"
    durations = assemble_video(images, audios, out, pause_s=0.6, fps=5)

    def probe(stream):
        r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", stream, "-show_entries",
                            "stream=duration", "-of", "csv=p=0", str(out)],
                           capture_output=True, text=True, check=True)
        return float(r.stdout.split()[0])

    total = sum(durations)
    assert probe("a:0") == pytest.approx(total, abs=0.05)
    assert probe("v:0") == pytest.approx(total, abs=0.25)
    assert not list(folder.glob("*.frames.txt")) and not (folder / "video.wav").exists()


def test_split_parts_groups_frames_by_section():
    from course2video.render.lecture import Frame
    from course2video.render.parts import split_parts

    kinds = ["title", "agenda", "section", "content", "section", "content", "content", "closing"]
    frames = [Frame(k, "x", index=i) for i, k in enumerate(kinds)]
    assert split_parts(frames) == [[0, 1, 2, 3], [4, 5, 6, 7]]
    assert split_parts([Frame("title", "x", index=0), Frame("content", "x", index=1)]) == []


@requires_ffmpeg
def test_one_video_per_part(sample_pdf, tmp_path):
    cfg = _cfg()
    cfg.render.per_part_videos = True
    run_stage1(sample_pdf, tmp_path, cfg)
    run_stage2(tmp_path, cfg)
    meta = json.loads((tmp_path / "meta.json").read_text())
    parts = meta["parts"]
    assert len(parts) >= 5
    assert all((tmp_path / "parts" / f"part_{p['part']:02d}.mp4").exists() for p in parts)
    assert all((tmp_path / "parts" / f"part_{p['part']:02d}.srt").exists() for p in parts)
    assert sum(p["duration_s"] for p in parts) == pytest.approx(meta["video"]["duration_s"], abs=0.1)
