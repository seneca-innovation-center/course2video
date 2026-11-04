from __future__ import annotations

import re
from pathlib import Path

from .base import FIGURE_TOKEN, FigureRef, ParsedDocument, Parser

_NUMBERED_HEADING = re.compile(r"^(\d+(\.\d+)*)\.?\s+[A-Z].{2,80}$")


class PyPDFParser(Parser):
    name = "pypdf"

    def parse(self, path: Path) -> ParsedDocument:
        from pypdf import PdfReader

        reader = PdfReader(str(path))
        lines: list[str] = []
        empty_pages = 0
        for page in reader.pages:
            text = page.extract_text() or ""
            if not text.strip():
                empty_pages += 1
            for raw in text.splitlines():
                line = raw.strip()
                if not line:
                    continue
                if not lines and len(line) < 100:
                    lines += [f"# {line}", ""]
                elif _NUMBERED_HEADING.match(line):
                    lines += ["", f"## {line}", ""]
                else:
                    lines.append(line)
        warnings = []
        if empty_pages:
            warnings.append(
                f"{empty_pages} page(s) had no text layer (scanned?); OCR is not supported in v0"
            )
        md = re.sub(r"\n{3,}", "\n\n", "\n".join(lines)).strip() + "\n"
        return ParsedDocument(source=path, markdown=md, parser=self.name, warnings=warnings)


class MarkdownParser(Parser):
    name = "markdown"

    def parse(self, path: Path) -> ParsedDocument:
        figures: list[FigureRef] = []
        warnings: list[str] = []

        def figure(m: re.Match) -> str:
            img = (path.parent / m.group(2)).resolve()
            if not img.exists():
                warnings.append(f"figure not found: {m.group(2)}")
                return m.group(0)
            figures.append(FigureRef(path=img, caption=m.group(1).strip()))
            return FIGURE_TOKEN.format(len(figures) - 1)

        md = re.sub(r"!\[([^\]]*)\]\(([^)\s]+)\)", figure, path.read_text(encoding="utf-8"))
        return ParsedDocument(source=path, markdown=md, parser=self.name, warnings=warnings,
                              figures=figures)
