from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class SlideScript(BaseModel):
    model_config = ConfigDict(extra="forbid")

    slide_id: int = Field(..., ge=1)
    text: str = Field(..., min_length=1, description="What the narrator says for this slide.")


class Script(BaseModel):
    model_config = ConfigDict(extra="forbid")

    slides: list[SlideScript] = Field(..., min_length=1)

    def for_slide(self, slide_id: int) -> str:
        for s in self.slides:
            if s.slide_id == slide_id:
                return s.text
        raise KeyError(slide_id)
