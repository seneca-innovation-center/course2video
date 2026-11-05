from __future__ import annotations

import json
import os
import time
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
        context_tokens: int | None = None,
        retries: int = 3,
        backoff_s: float = 2.0,
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
        self.retries = retries
        self.backoff_s = backoff_s
        self._sleep = time.sleep
        self._context = context_tokens
        self._context_checked = context_tokens is not None

    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}

    def context_length(self) -> int | None:
        if not self._context_checked:
            self._context_checked = True
            try:
                r = httpx.get(f"{self.base_url}/models", headers=self._headers(), timeout=30)
                for m in r.json().get("data", []):
                    if m.get("id") == self.model:
                        for key in ("max_model_len", "context_length", "context_window"):
                            if isinstance(m.get(key), int):
                                self._context = m[key]
                                break
            except (httpx.HTTPError, ValueError, AttributeError):
                self._context = None
        return self._context

    def _max_tokens_for(self, body: dict[str, Any]) -> int:
        ctx = self.context_length()
        if not ctx:
            return self.max_tokens
        prompt_tokens = int(len(json.dumps(body, ensure_ascii=False)) / 3.0) + 64
        room = ctx - prompt_tokens
        if room < 512:
            raise LLMError(
                f"prompt of about {prompt_tokens} tokens does not fit the model's context of {ctx} "
                "tokens; lower slides.chunk_chars or script.slides_per_call"
            )
        return min(self.max_tokens, room)

    def _post_with_backoff(self, body: dict[str, Any], headers: dict[str, str]) -> httpx.Response:
        for attempt in range(self.retries + 1):
            last = attempt == self.retries
            try:
                r = httpx.post(f"{self.base_url}/chat/completions", json=body, headers=headers,
                               timeout=self.timeout_s)
            except httpx.HTTPError as e:
                if last:
                    raise LLMError(f"cannot reach {self.base_url}: {e}") from e
                self._sleep(self.backoff_s * 2 ** attempt)
                continue
            if r.status_code == 429 or r.status_code >= 500:
                if last:
                    return r
                wait = self.backoff_s * 2 ** attempt
                try:
                    wait = max(wait, min(60.0, float(r.headers.get("retry-after", 0))))
                except ValueError:
                    pass
                self._sleep(wait)
                continue
            return r
        raise LLMError(f"cannot reach {self.base_url}")

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
        body["max_tokens"] = self._max_tokens_for(body)
        headers = self._headers()
        r = self._post_with_backoff(body, headers)
        if r.status_code != 200:
            raise LLMError(f"HTTP {r.status_code} from {self.base_url}: {r.text[:500]}")
        data = r.json()
        try:
            choice = data["choices"][0]
            text = choice["message"].get("content") or ""
        except (KeyError, IndexError) as e:
            raise LLMError(f"unexpected response shape: {str(data)[:500]}") from e
        if choice.get("finish_reason") == "length":
            raise LLMError(
                f"output truncated after {body['max_tokens']} tokens (finish_reason=length); raise "
                "llm.max_tokens, or ask for fewer slides per call on small-context servers"
            )
        if not text.strip():
            raise LLMError("empty response")
        return text
