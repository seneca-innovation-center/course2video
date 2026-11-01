from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class ParsedDocument:
    source: Path
    markdown: str
    parser: str
    warnings: list[str] = field(default_factory=list)


class Parser(ABC):
    name: str = "base"

    @abstractmethod
    def parse(self, path: Path) -> ParsedDocument: ...
