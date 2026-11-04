from __future__ import annotations

import math
import re

from ..script.alignment import content_words

MIN_GAP_S = 1.0


def _positions(narration: str) -> list[tuple[int, str]]:
    out = []
    for m in re.finditer(r"[^\W_]+", narration):
        words = content_words(m.group(0))
        if words:
            out.append((m.start(), next(iter(words))))
    return out


def reveal_times(narration: str, bullets: list[str], speech_s: float,
                 share: float = 0.5) -> list[float]:
    if not bullets:
        return []
    tokens = _positions(narration)
    length = max(1, len(narration))
    times = [0.0]
    for bullet in bullets[1:]:
        target = content_words(bullet)
        need = max(1, math.ceil(share * len(target))) if target else 0
        seen: set[str] = set()
        found = None
        for pos, word in tokens:
            if word in target:
                seen.add(word)
                if len(seen) >= need:
                    found = speech_s * pos / length
                    break
        times.append(found)
    known = [(i, t) for i, t in enumerate(times) if t is not None]
    for i, t in enumerate(times):
        if t is None:
            nxt = next((kt for ki, kt in known if ki > i), speech_s)
            prv = times[i - 1]
            times[i] = (prv + nxt) / 2
    for i in range(1, len(times)):
        times[i] = max(times[i], times[i - 1] + MIN_GAP_S)
    last_allowed = max(0.0, speech_s - MIN_GAP_S)
    for i in range(len(times) - 1, 0, -1):
        times[i] = min(times[i], last_allowed if i == len(times) - 1 else times[i + 1] - MIN_GAP_S)
    return [max(0.0, round(t, 3)) for t in times]
