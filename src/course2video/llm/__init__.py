from __future__ import annotations

from ..config import LLMConfig
from .base import LLMBackend, LLMError
from .mock_backend import MockBackend

__all__ = ["LLMBackend", "LLMError", "MockBackend", "get_backend"]


def get_backend(cfg: LLMConfig) -> LLMBackend:
    if cfg.backend == "mock":
        return MockBackend()
    if cfg.backend == "openai_compat":
        from .openai_compat_backend import OpenAICompatBackend

        return OpenAICompatBackend(
            model=cfg.model,
            base_url=cfg.base_url,
            api_key_env=cfg.api_key_env,
            max_tokens=cfg.max_tokens,
            temperature=cfg.temperature,
            effort=cfg.effort,
            structured_output=cfg.structured_output,
            timeout_s=cfg.timeout_s,
            context_tokens=cfg.context_tokens,
        )
    raise ValueError(f"unknown llm backend {cfg.backend!r}")
