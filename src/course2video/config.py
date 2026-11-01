from __future__ import annotations

import os
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, Field


class LLMConfig(BaseModel):
    backend: Literal["mock", "openai_compat"] = "mock"
    model: str = ""
    base_url: str = "http://localhost:8000/v1"
    api_key_env: str = ""
    max_tokens: int = 16000
    temperature: float | None = None
    effort: str | None = None
    structured_output: bool = True
    timeout_s: float = 600.0


class ParserConfig(BaseModel):
    backend: Literal["docling", "pypdf", "markdown"] = "pypdf"
    docling_formulas: bool = True


class SlidesConfig(BaseModel):
    chunk_chars: int = 6000
    max_slides_per_chunk: int = 12
    max_retries: int = 3
    max_bullet_words: int = 12


class ScriptConfig(BaseModel):
    slides_per_call: int = 8
    words_per_slide: int = 220
    max_retries: int = 3


class AlignmentConfig(BaseModel):
    item_threshold: float = 0.6
    slide_warn_below: float = 0.8


class TTSConfig(BaseModel):
    backend: Literal["piper", "say", "stub"] = "stub"
    piper_model: str = "models/piper/en_US-ljspeech-medium.onnx"
    say_voice: str = ""
    sample_rate: int = 22050


class RenderConfig(BaseModel):
    renderer: Literal["pillow", "libreoffice"] = "pillow"
    width: int = 1920
    height: int = 1080
    pause_after_slide_s: float = 0.6
    fps: int = 2


class LectureConfig(BaseModel):
    target_minutes: float | None = None
    title_slide: bool = True
    agenda: bool = True
    section_dividers: bool = True
    closing: bool = True
    progress_bar: bool = True
    subtitle: str = ""
    presenter: str = ""
    institution: str = ""


class Config(BaseModel):
    lecture: LectureConfig = Field(default_factory=LectureConfig)
    llm: LLMConfig = Field(default_factory=LLMConfig)
    parser: ParserConfig = Field(default_factory=ParserConfig)
    slides: SlidesConfig = Field(default_factory=SlidesConfig)
    script: ScriptConfig = Field(default_factory=ScriptConfig)
    alignment: AlignmentConfig = Field(default_factory=AlignmentConfig)
    tts: TTSConfig = Field(default_factory=TTSConfig)
    render: RenderConfig = Field(default_factory=RenderConfig)


def load_config(path: str | Path | None = None) -> Config:
    path = path or os.environ.get("C2V_CONFIG")
    if not path:
        return Config()
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
    return Config.model_validate(data)
