from __future__ import annotations

import logging

from ..config import TTSConfig
from .base import TTSBackend, wav_duration

__all__ = ["TTSBackend", "get_tts", "piper_voice_for", "wav_duration"]

log = logging.getLogger(__name__)


def piper_voice_for(cfg: TTSConfig, language: str) -> str:
    lang = (language or "en").split("-")[0].lower()
    voice = cfg.piper_voices.get(lang)
    if voice:
        return voice
    log.warning("no Piper voice configured for language %r; using %s", lang, cfg.piper_model)
    return cfg.piper_model


def get_tts(cfg: TTSConfig, language: str = "en") -> TTSBackend:
    from .backends import PiperTTS, SayTTS, StubTTS

    if cfg.backend == "piper":
        return PiperTTS(piper_voice_for(cfg, language))
    if cfg.backend == "say":
        return SayTTS(cfg.say_voice, cfg.sample_rate)
    if cfg.backend == "stub":
        return StubTTS()
    raise ValueError(f"unknown tts backend {cfg.backend!r}")
