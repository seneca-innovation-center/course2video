from __future__ import annotations

import wave
from abc import ABC, abstractmethod
from pathlib import Path


class TTSBackend(ABC):
    name: str = "base"

    @abstractmethod
    def synthesize(self, text: str, out_wav: Path) -> Path: ...


def wav_duration(path: Path) -> float:
    with wave.open(str(path), "rb") as w:
        return w.getnframes() / float(w.getframerate())
