from __future__ import annotations

from pathlib import Path

from .base import ParsedDocument, Parser


class DoclingParser(Parser):
    name = "docling"

    def __init__(self, formula_enrichment: bool = True) -> None:
        try:
            from docling.datamodel.base_models import InputFormat
            from docling.datamodel.pipeline_options import PdfPipelineOptions
            from docling.document_converter import DocumentConverter, PdfFormatOption
        except ImportError as e:
            raise RuntimeError("pip install 'course2video[docling]' to use the docling parser") from e
        opts = PdfPipelineOptions()
        opts.do_formula_enrichment = formula_enrichment
        self._converter = DocumentConverter(
            format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=opts)}
        )

    def parse(self, path: Path) -> ParsedDocument:
        result = self._converter.convert(str(path))
        md = result.document.export_to_markdown()
        warnings = []
        undecoded = md.count("formula-not-decoded")
        if undecoded:
            warnings.append(f"{undecoded} formula(s) not decoded; equations on slides need review")
        if not md.strip():
            warnings.append("docling returned no text; the PDF may be scanned (OCR not enabled in v0)")
        return ParsedDocument(source=path, markdown=md, parser=self.name, warnings=warnings)
