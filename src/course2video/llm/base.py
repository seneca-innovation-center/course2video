from __future__ import annotations

import copy
from abc import ABC, abstractmethod
from typing import Any


class LLMError(RuntimeError):
    pass


class LLMBackend(ABC):
    name: str = "base"

    @abstractmethod
    def complete(
        self,
        system: str,
        prompt: str,
        *,
        schema: dict[str, Any] | None = None,
        task: str = "",
    ) -> str:
        ...

    def describe(self) -> dict[str, Any]:
        return {"backend": self.name}


_UNSUPPORTED_KEYS = {
    "minLength", "maxLength", "minimum", "maximum", "exclusiveMinimum", "exclusiveMaximum",
    "multipleOf", "minItems", "maxItems", "uniqueItems", "pattern", "default", "title",
}


def relax_schema(schema: dict[str, Any]) -> dict[str, Any]:
    schema = copy.deepcopy(schema)

    def walk(node: Any) -> Any:
        if isinstance(node, dict):
            for k in list(node):
                if k in _UNSUPPORTED_KEYS:
                    del node[k]
            if node.get("type") == "object" and "properties" in node:
                node["additionalProperties"] = False
                node["required"] = list(node["properties"])
            for k, v in node.items():
                if k in ("properties", "$defs"):
                    for sub in v.values():
                        walk(sub)
                else:
                    walk(v)
        elif isinstance(node, list):
            for v in node:
                walk(v)
        return node

    return walk(schema)
