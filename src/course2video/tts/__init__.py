from __future__ import annotations

from ..config import TTSConfig
from .base import TTSBackend, wav_duration

__all__ = ["TTSBackend", "get_tts", "wav_duration"]


def get_tts(cfg: TTSConfig) -> TTSBackend:
    from .backends import PiperTTS, SayTTS, StubTTS

    if cfg.backend == "piper":
        return PiperTTS(cfg.piper_model)
    if cfg.backend == "say":
        return SayTTS(cfg.say_voice, cfg.sample_rate)
    if cfg.backend == "stub":
        return StubTTS()
    raise ValueError(f"unknown tts backend {cfg.backend!r}")
