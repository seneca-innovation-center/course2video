from __future__ import annotations

from pathlib import Path

from .base import ParsedDocument, Parser

__all__ = ["ParsedDocument", "Parser", "get_parser"]


def get_parser(name: str, path: Path | None = None, *, docling_formulas: bool = True) -> Parser:
    if path is not None and path.suffix.lower() in {".md", ".markdown", ".txt"}:
        name = "markdown"
    if name == "docling":
        from .docling_parser import DoclingParser

        return DoclingParser(formula_enrichment=docling_formulas)
    if name == "pypdf":
        from .simple_parsers import PyPDFParser

        return PyPDFParser()
    if name == "markdown":
        from .simple_parsers import MarkdownParser

        return MarkdownParser()
    raise ValueError(f"unknown parser {name!r}")
