from __future__ import annotations

import re
from pathlib import Path

MAX_WORDS = 14


def _cues(text: str) -> list[str]:
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    cues = []
    for s in sentences:
        words = s.split()
        for i in range(0, len(words), MAX_WORDS):
            cues.append(" ".join(words[i : i + MAX_WORDS]))
    return [c for c in cues if c]


def _ts(t: float) -> str:
    ms = int(round(t * 1000))
    h, ms = divmod(ms, 3_600_000)
    m, ms = divmod(ms, 60_000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def build_srt(texts: list[str], durations: list[float], speech_durations: list[float]) -> str:
    out = []
    n = 1
    offset = 0.0
    for text, seg, speech in zip(texts, durations, speech_durations, strict=True):
        cues = _cues(text)
        total_chars = sum(len(c) for c in cues) or 1
        t = offset
        for c in cues:
            dt = speech * len(c) / total_chars
            out.append(f"{n}\n{_ts(t)} --> {_ts(t + dt)}\n{c}\n")
            n += 1
            t += dt
        offset += seg
    return "\n".join(out)


def write_srt(texts: list[str], durations: list[float], speech: list[float], path: Path) -> Path:
    path.write_text(build_srt(texts, durations, speech), encoding="utf-8")
    return path
