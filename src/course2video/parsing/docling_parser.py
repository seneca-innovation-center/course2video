from __future__ import annotations

from pathlib import Path

from .base import FIGURE_TOKEN, FigureRef, ParsedDocument, Parser


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
        opts.generate_picture_images = True
        opts.images_scale = 2.0
        self._converter = DocumentConverter(
            format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=opts)}
        )

    def parse(self, path: Path) -> ParsedDocument:
        import tempfile

        result = self._converter.convert(str(path))
        doc = result.document
        md = doc.export_to_markdown(image_placeholder="[[FIG]]")
        figures: list[FigureRef] = []
        tmp: Path | None = None
        for pic in doc.pictures:
            image = pic.get_image(doc)
            if image is None:
                continue
            tmp = tmp or Path(tempfile.mkdtemp(prefix="c2v_fig_"))
            out = tmp / f"fig_{len(figures)}.png"
            image.save(out)
            page = pic.prov[0].page_no if pic.prov else None
            figures.append(FigureRef(path=out, caption=pic.caption_text(doc) or "", page=page))
        for k in range(len(figures)):
            md = md.replace("[[FIG]]", FIGURE_TOKEN.format(k), 1)
        md = md.replace("[[FIG]]", "")
        warnings = []
        undecoded = md.count("formula-not-decoded")
        if undecoded:
            warnings.append(f"{undecoded} formula(s) not decoded; equations on slides need review")
        if not md.strip():
            warnings.append("docling returned no text; the PDF may be scanned (OCR not enabled in v0)")
        return ParsedDocument(source=path, markdown=md, parser=self.name, warnings=warnings,
                              figures=figures)
