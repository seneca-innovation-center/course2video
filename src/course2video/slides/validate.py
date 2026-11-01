from __future__ import annotations

import json
import logging
import re
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import TypeVar

from pydantic import BaseModel, ValidationError

from ..llm.base import LLMBackend, LLMError
from .models import Deck

log = logging.getLogger(__name__)

M = TypeVar("M", bound=BaseModel)


class GenerationFailed(RuntimeError):
    def __init__(self, message: str, attempts: list["Attempt"]):
        super().__init__(message)
        self.attempts = attempts


@dataclass
class Attempt:
    number: int
    ok: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def extract_json(text: str) -> object:
    text = text.strip()
    fence = re.search(r"```(?:json)?\s*(.*?)```", text, re.S)
    if fence:
        text = fence.group(1).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end > start:
        return json.loads(text[start : end + 1])
    raise json.JSONDecodeError("no JSON object found", text, 0)


def format_validation_error(e: ValidationError) -> list[str]:
    out = []
    for err in e.errors()[:20]:
        loc = ".".join(str(p) for p in err["loc"])
        out.append(f"{loc}: {err['msg']}")
    return out


def check_latex(deck_or_slides) -> list[str]:
    problems = []
    for s in deck_or_slides.slides:
        for i, eq in enumerate(s.equations):
            if eq.latex.count("{") != eq.latex.count("}"):
                problems.append(f"slides[id={s.id}].equations.{i}.latex: unbalanced braces")
            if "$" in eq.latex:
                problems.append(f"slides[id={s.id}].equations.{i}.latex: remove $ delimiters")
    return problems


def check_lecture_style(batch, max_bullet_words: int, min_talking_points: int = 2) -> list[str]:
    problems = []
    for s in batch.slides:
        for i, b in enumerate(s.bullets):
            n = len(b.split())
            if n > max_bullet_words + 3:
                problems.append(f"slides[id={s.id}].bullets.{i}: {n} words; keep at most "
                                f"{max_bullet_words} (move the explanation to talking_points)")
        if len(s.talking_points) < min_talking_points:
            problems.append(f"slides[id={s.id}].talking_points: give at least {min_talking_points} "
                            "points the lecturer will explain out loud")
    return problems


def generate_validated(
    llm: LLMBackend,
    *,
    system: str,
    prompt: str,
    model_cls: type[M],
    task: str,
    max_retries: int,
    extra_checks: Callable[[M], list[str]] | None = None,
    soft_checks: Callable[[M], list[str]] | None = None,
    soft_retries: int = 1,
) -> tuple[M, list[Attempt]]:
    attempts: list[Attempt] = []
    schema = model_cls.model_json_schema()
    current_prompt = prompt
    soft_used = 0
    for n in range(1, max_retries + 2):
        errors: list[str] = []
        try:
            raw = llm.complete(system, current_prompt, schema=schema, task=task)
            data = extract_json(raw)
            obj = model_cls.model_validate(data)
            if extra_checks:
                errors = extra_checks(obj)
            if not errors:
                soft = soft_checks(obj) if soft_checks else []
                if not soft or soft_used >= soft_retries or n == max_retries + 1:
                    attempts.append(Attempt(n, True, warnings=soft))
                    if soft:
                        log.warning("%s accepted with warnings: %s", task, "; ".join(soft))
                    return obj, attempts
                soft_used += 1
                errors = soft
        except LLMError as e:
            errors = [f"backend error: {e}"]
        except json.JSONDecodeError as e:
            errors = [f"output is not valid JSON: {e.msg}"]
        except ValidationError as e:
            errors = format_validation_error(e)
        log.warning("%s attempt %d failed: %s", task, n, "; ".join(errors))
        attempts.append(Attempt(n, False, errors))
        current_prompt = (
            prompt
            + "\n\nYour previous answer was rejected by the validator with these errors:\n- "
            + "\n- ".join(errors)
            + "\nReturn a corrected JSON object only."
        )
    raise GenerationFailed(
        f"{task}: no valid output after {len(attempts)} attempts; last errors: {attempts[-1].errors}",
        attempts,
    )


def validate_deck_file(text: str) -> tuple[Deck | None, list[str]]:
    try:
        deck = Deck.model_validate(extract_json(text))
    except json.JSONDecodeError as e:
        return None, [f"not valid JSON: {e.msg} (line {e.lineno})"]
    except ValidationError as e:
        return None, format_validation_error(e)
    problems = check_latex(deck)
    return (deck if not problems else None), problems
