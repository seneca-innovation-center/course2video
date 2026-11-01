from __future__ import annotations

import shutil
import subprocess
import tempfile
import wave
from pathlib import Path

from .base import TTSBackend


class PiperTTS(TTSBackend):
    name = "piper"

    def __init__(self, model_path: str) -> None:
        try:
            from piper import PiperVoice
        except ImportError as e:
            raise RuntimeError("pip install 'course2video[piper]' to use Piper") from e
        if not Path(model_path).exists():
            raise FileNotFoundError(
                f"Piper voice not found at {model_path}; run `make models` (scripts/download_models.sh)"
            )
        self.voice = PiperVoice.load(model_path)

    def synthesize(self, text: str, out_wav: Path) -> Path:
        out_wav.parent.mkdir(parents=True, exist_ok=True)
        with wave.open(str(out_wav), "wb") as wf:
            if hasattr(self.voice, "synthesize_wav"):
                self.voice.synthesize_wav(text, wf)
            else:
                self.voice.synthesize(text, wf)
        return out_wav


class SayTTS(TTSBackend):
    name = "say"

    def __init__(self, voice: str = "", sample_rate: int = 22050) -> None:
        if not shutil.which("say"):
            raise RuntimeError("`say` is only available on macOS")
        if not shutil.which("ffmpeg"):
            raise RuntimeError("ffmpeg is required to convert `say` output to WAV")
        self.voice = voice
        self.sample_rate = sample_rate

    def synthesize(self, text: str, out_wav: Path) -> Path:
        out_wav.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory() as tmp:
            aiff = Path(tmp) / "out.aiff"
            txt = Path(tmp) / "in.txt"
            txt.write_text(text, encoding="utf-8")
            cmd = ["say", "-o", str(aiff), "-f", str(txt)]
            if self.voice:
                cmd += ["-v", self.voice]
            subprocess.run(cmd, check=True)
            subprocess.run(
                ["ffmpeg", "-y", "-loglevel", "error", "-i", str(aiff),
                 "-ac", "1", "-ar", str(self.sample_rate), "-sample_fmt", "s16", str(out_wav)],
                check=True,
            )
        return out_wav


class StubTTS(TTSBackend):
    name = "stub"

    def __init__(self, sample_rate: int = 16000, words_per_second: float = 2.5) -> None:
        self.sample_rate = sample_rate
        self.wps = words_per_second

    def synthesize(self, text: str, out_wav: Path) -> Path:
        out_wav.parent.mkdir(parents=True, exist_ok=True)
        seconds = max(1.0, len(text.split()) / self.wps)
        frames = int(seconds * self.sample_rate)
        with wave.open(str(out_wav), "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(self.sample_rate)
            w.writeframes(b"\x00\x00" * frames)
        return out_wav
