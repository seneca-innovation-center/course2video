from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

from .base import ParsedDocument


def default_cache_dir() -> Path:
    return Path(os.environ.get("C2V_CACHE_DIR", Path.home() / ".cache" / "course2video" / "parsed"))


def cache_key(path: Path, parser: str, docling_formulas: bool) -> str:
    h = hashlib.sha256(path.read_bytes()).hexdigest()
    return f"{h[:24]}-{parser}-{'f' if docling_formulas else 'nf'}"


def parse_cached(path: Path, parser: str, *, docling_formulas: bool = True,
                 cache_dir: Path | None = None) -> ParsedDocument:
    from . import get_parser

    cache_dir = cache_dir or default_cache_dir()
    key = cache_key(path, parser, docling_formulas)
    md_file, meta_file = cache_dir / f"{key}.md", cache_dir / f"{key}.json"
    if md_file.exists() and meta_file.exists():
        meta = json.loads(meta_file.read_text(encoding="utf-8"))
        return ParsedDocument(source=path, markdown=md_file.read_text(encoding="utf-8"),
                              parser=meta["parser"], warnings=meta["warnings"] + ["(from cache)"])
    doc = get_parser(parser, path, docling_formulas=docling_formulas).parse(path)
    cache_dir.mkdir(parents=True, exist_ok=True)
    md_file.write_text(doc.markdown, encoding="utf-8")
    meta_file.write_text(json.dumps({"parser": doc.parser, "warnings": doc.warnings,
                                     "source": str(path)}), encoding="utf-8")
    return doc
