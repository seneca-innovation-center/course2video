from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class Equation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    latex: str = Field(..., min_length=1, description="Equation in LaTeX, without $ delimiters.")
    explanation: str = Field(
        ..., min_length=1, description="One or two sentences saying in words what the equation means."
    )


class Slide(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: int = Field(..., ge=1, description="1-based slide number, unique within the deck.")
    title: str = Field(..., min_length=1, max_length=120)
    bullets: list[str] = Field(
        ..., min_length=1, max_length=7, description="Short bullet points shown on the slide."
    )
    equations: list[Equation] = Field(default_factory=list, max_length=3)
    talking_points: list[str] = Field(
        default_factory=list, max_length=8,
        description="What the lecturer explains while the slide is shown and that is NOT written "
                    "on it: intuition, why it matters, a worked example with its numbers, a common "
                    "mistake. Taken from the source documents; reviewed with the slide.",
    )
    notes: str = Field(default="", description="Optional lecturer notes; not shown on the slide.")
    source_section: str = Field(
        default="", description="Heading of the source section this slide was derived from."
    )
    kind: Literal["theory", "exercise", "solution"] = Field(
        default="theory",
        description="theory: from lecture notes; exercise: a problem statement; "
                    "solution: steps of the official solution.",
    )
    figure: str = Field(
        default="",
        description="Id of a source figure shown on this slide, e.g. F3. Only ids that appear as "
                    "[Figure Fn: ...] in the source; empty if none.",
    )
    source_doc: str = Field(
        default="", description="Source document (and problem), e.g. 'Problem Set 2, Problem 2'. "
                                "Set by the pipeline from the course index, not by the LLM.",
    )

    @field_validator("bullets")
    @classmethod
    def _bullets_not_blank(cls, v: list[str]) -> list[str]:
        cleaned = [b.strip() for b in v]
        if any(not b for b in cleaned):
            raise ValueError("bullets must not be empty strings")
        if any(len(b) > 200 for b in cleaned):
            raise ValueError("each bullet must be at most 200 characters")
        return cleaned


class Deck(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = Field(..., min_length=1)
    language: str = Field(default="en", description="BCP-47 language code of the slide text.")
    slides: list[Slide] = Field(..., min_length=1)
    approved: bool = Field(
        default=False, description="Set to true by the lecturer review step, never by the LLM."
    )

    @model_validator(mode="after")
    def _unique_sequential_ids(self) -> "Deck":
        ids = [s.id for s in self.slides]
        if len(set(ids)) != len(ids):
            raise ValueError(f"slide ids must be unique, got {ids}")
        return self


class SlideBatch(BaseModel):
    model_config = ConfigDict(extra="forbid")

    slides: list[Slide] = Field(..., min_length=1)
