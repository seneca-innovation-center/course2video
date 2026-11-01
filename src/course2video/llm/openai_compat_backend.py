from __future__ import annotations

import os
from typing import Any

import httpx

from .base import LLMBackend, LLMError, relax_schema


class OpenAICompatBackend(LLMBackend):
    name = "openai_compat"

    def __init__(
        self,
        model: str,
        base_url: str = "http://localhost:8000/v1",
        api_key_env: str = "",
        max_tokens: int = 16000,
        temperature: float | None = None,
        effort: str | None = None,
        structured_output: bool = True,
        timeout_s: float = 600.0,
    ) -> None:
        if not model:
            raise LLMError("llm.model is required for the openai_compat backend")
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.api_key = os.environ.get(api_key_env, "") if api_key_env else ""
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.effort = effort
        self.structured_output = structured_output
        self.timeout_s = timeout_s

    def describe(self) -> dict[str, Any]:
        return {"backend": self.name, "model": self.model, "base_url": self.base_url}

    def complete(self, system, prompt, *, schema=None, task=""):
        body: dict[str, Any] = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
            "max_tokens": self.max_tokens,
        }
        if self.temperature is not None:
            body["temperature"] = self.temperature
        if self.effort:
            body["reasoning_effort"] = self.effort
        if schema is not None and self.structured_output:
            body["response_format"] = {
                "type": "json_schema",
                "json_schema": {"name": task or "output", "schema": relax_schema(schema)},
            }
        headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}
        try:
            r = httpx.post(
                f"{self.base_url}/chat/completions", json=body, headers=headers, timeout=self.timeout_s
            )
        except httpx.HTTPError as e:
            raise LLMError(f"cannot reach {self.base_url}: {e}") from e
        if r.status_code != 200:
            raise LLMError(f"HTTP {r.status_code} from {self.base_url}: {r.text[:500]}")
        data = r.json()
        try:
            choice = data["choices"][0]
            text = choice["message"].get("content") or ""
        except (KeyError, IndexError) as e:
            raise LLMError(f"unexpected response shape: {str(data)[:500]}") from e
        if choice.get("finish_reason") == "length":
            raise LLMError("output truncated (finish_reason=length); raise llm.max_tokens")
        if not text.strip():
            raise LLMError("empty response")
        return text
