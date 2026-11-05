from __future__ import annotations

import math
from dataclasses import asdict, dataclass

DEFAULT_WPM = 163
STRUCTURE_WORDS_PER_FRAME = 15
PAUSE_S = 0.6


@dataclass
class Budget:
    target_minutes: float
    words_per_minute: int
    content_words: int
    words_per_slide: int
    theory_slides: int
    slides_per_problem: int
    problems: int
    warnings: list[str]

    def as_dict(self) -> dict:
        return asdict(self)


def plan_budget(
    target_minutes: float,
    *,
    source_words: int,
    n_problems: int,
    n_sections_hint: int = 6,
    words_per_minute: int = DEFAULT_WPM,
    words_per_slide: int = 220,
    problem_share: float = 0.35,
    min_theory_slides: int = 0,
) -> Budget:
    warnings = []
    n_parts = n_sections_hint + n_problems
    structure_frames = 3 + n_parts
    speech_s = target_minutes * 60 - PAUSE_S * (structure_frames + 25)
    total_words = int(speech_s / 60 * words_per_minute)
    content_words = max(0, total_words - STRUCTURE_WORDS_PER_FRAME * structure_frames)

    share = problem_share if n_problems else 0.0
    problem_words = content_words * share
    slides_per_problem = 0
    if n_problems:
        slides_per_problem = max(2, min(4, round(problem_words / n_problems / words_per_slide)))
    theory_words = content_words - n_problems * slides_per_problem * words_per_slide
    theory_slides = max(3, round(theory_words / words_per_slide))
    if theory_slides < min_theory_slides:
        warnings.append(
            f"the lecture has {min_theory_slides} chapters; giving each one a slide makes the video "
            f"longer than the {target_minutes:g}-minute target"
        )
        theory_slides = min_theory_slides

    if source_words < content_words * 0.8:
        warnings.append(
            f"sources have {source_words} words but a {target_minutes:g}-minute video needs about "
            f"{content_words} words of narration; the video will likely be shorter than the target"
        )
    return Budget(target_minutes, words_per_minute, content_words, words_per_slide,
                  theory_slides, slides_per_problem, n_problems, warnings)


def slides_per_chunk(total_slides: int, chunk_lengths: list[int]) -> list[int]:
    total = sum(chunk_lengths) or 1
    exact = [total_slides * n / total for n in chunk_lengths]
    shares = [max(1, math.floor(x)) for x in exact]
    by_remainder = sorted(range(len(exact)), key=lambda i: exact[i] - math.floor(exact[i]),
                          reverse=True)
    for i in by_remainder:
        if sum(shares) >= total_slides:
            break
        shares[i] += 1
    return shares
