from __future__ import annotations

import re
from pathlib import Path

from .base import ParsedDocument, Parser

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
        return ParsedDocument(source=path, markdown=path.read_text(encoding="utf-8"), parser=self.name)
