from __future__ import annotations

import hashlib
import json
import os
import shutil
from pathlib import Path

from .base import FigureRef, ParsedDocument

CACHE_FORMAT = 2


def default_cache_dir() -> Path:
    return Path(os.environ.get("C2V_CACHE_DIR", Path.home() / ".cache" / "course2video" / "parsed"))


def cache_key(path: Path, parser: str, docling_formulas: bool) -> str:
    h = hashlib.sha256(path.read_bytes()).hexdigest()
    return f"{h[:24]}-{parser}-{'f' if docling_formulas else 'nf'}-v{CACHE_FORMAT}"


def parser_version(parser: str) -> str | None:
    import importlib.metadata

    try:
        return importlib.metadata.version(parser) if parser == "docling" else None
    except importlib.metadata.PackageNotFoundError:
        return None


def parse_cached(path: Path, parser: str, *, docling_formulas: bool = True,
                 cache_dir: Path | None = None) -> ParsedDocument:
    from . import get_parser

    cache_dir = cache_dir or default_cache_dir()
    key = cache_key(path, parser, docling_formulas)
    md_file, meta_file = cache_dir / f"{key}.md", cache_dir / f"{key}.json"
    version = parser_version(parser)
    meta = json.loads(meta_file.read_text(encoding="utf-8")) if meta_file.exists() else None
    if meta is not None and meta.get("parser_version") not in (None, version):
        meta = None
    if md_file.exists() and meta is not None:
        figures = [FigureRef(path=cache_dir / f["file"], caption=f["caption"], page=f["page"])
                   for f in meta.get("figures", [])]
        return ParsedDocument(source=path, markdown=md_file.read_text(encoding="utf-8"),
                              parser=meta["parser"], warnings=meta["warnings"] + ["(from cache)"],
                              figures=figures)
    doc = get_parser(parser, path, docling_formulas=docling_formulas).parse(path)
    cache_dir.mkdir(parents=True, exist_ok=True)
    stored = []
    temp_dirs = set()
    for k, fig in enumerate(doc.figures):
        name = f"{key}-fig{k}{fig.path.suffix or '.png'}"
        shutil.copyfile(fig.path, cache_dir / name)
        stored.append({"file": name, "caption": fig.caption, "page": fig.page})
        if fig.path.parent.name.startswith("c2v_fig_"):
            temp_dirs.add(fig.path.parent)
        fig.path = cache_dir / name
    for d in temp_dirs:
        shutil.rmtree(d, ignore_errors=True)
    md_file.write_text(doc.markdown, encoding="utf-8")
    meta_file.write_text(json.dumps({"parser": doc.parser, "warnings": doc.warnings,
                                     "source": str(path), "figures": stored,
                                     "parser_version": version}), encoding="utf-8")
    return doc
