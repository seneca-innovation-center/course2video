from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from course2video.slides.models import Deck

DATA = Path(__file__).parent / "data"


@pytest.fixture
def sample_pdf() -> Path:
    return DATA / "vector_spaces.pdf"


@pytest.fixture
def good_deck_dict() -> dict:
    return {
        "title": "Vector Spaces",
        "language": "en",
        "slides": [
            {
                "id": 1,
                "title": "Vectors in R^n",
                "bullets": ["A vector is an ordered list of n real numbers.",
                            "Vectors are added component by component."],
                "equations": [{"latex": r"u + v = (u_1 + v_1, \ldots, u_n + v_n)",
                               "explanation": "Addition works on each component separately."}],
                "notes": "",
                "source_section": "1. Vectors in R^n",
            },
            {
                "id": 2,
                "title": "Subspaces",
                "bullets": ["A subspace contains the zero vector.",
                            "It is closed under addition and scalar multiplication."],
                "equations": [],
            },
        ],
    }


@pytest.fixture
def good_deck(good_deck_dict) -> Deck:
    return Deck.model_validate(good_deck_dict)


requires_ffmpeg = pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="ffmpeg not installed")
