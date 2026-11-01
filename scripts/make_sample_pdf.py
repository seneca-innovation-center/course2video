from __future__ import annotations

import re
import sys
from datetime import datetime, timezone
from pathlib import Path

from fpdf import FPDF

ROOT = Path(__file__).resolve().parent.parent
SAMPLES = {
    ROOT / "examples/sample_course/vector_spaces.md": ("text", [
        ROOT / "examples/sample_course/vector_spaces.pdf", ROOT / "tests/data/vector_spaces.pdf"]),
    ROOT / "examples/probability_course/probability.md": ("image", [
        ROOT / "examples/probability_course/probability.pdf"]),
}

LATEX_TO_TEXT = [
    (r"\ldots", "..."), (r"\cdots", "..."), ("_", ""), ("{", ""), ("}", ""),
]


def latex_plain(s: str) -> str:
    for a, b in LATEX_TO_TEXT:
        s = s.replace(a, b)
    return re.sub(r"\s+", " ", s).strip()


def equation_png(latex: str, out_dir: Path, n: int) -> Path:
    import matplotlib

    matplotlib.use("Agg")
    from matplotlib import mathtext
    from matplotlib.font_manager import FontProperties

    path = out_dir / f"eq{n}.png"
    mathtext.math_to_image(f"${latex}$", str(path), prop=FontProperties(size=13), dpi=300)
    return path


def build(src: Path, eq_style: str, outs: list[Path]) -> None:
    import tempfile

    tmp = Path(tempfile.mkdtemp())
    pdf = FPDF(format="A4")
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.set_creation_date(datetime(2026, 1, 1, tzinfo=timezone.utc))
    pdf.add_page()
    pdf.set_margins(22, 20, 22)
    eq_no = 0
    for line in src.read_text(encoding="utf-8").splitlines():
        if line.startswith("# "):
            pdf.set_font("Helvetica", "B", 18)
            pdf.multi_cell(0, 10, line[2:], new_x="LMARGIN", new_y="NEXT")
            pdf.ln(2)
        elif line.startswith("## "):
            pdf.ln(3)
            pdf.set_font("Helvetica", "B", 13)
            pdf.multi_cell(0, 8, line[3:], new_x="LMARGIN", new_y="NEXT")
        elif line.startswith("$$"):
            eq_no += 1
            latex = line.strip("$ ")
            if eq_style == "image":
                png = equation_png(latex, tmp, eq_no)
                from PIL import Image

                w_px, h_px = Image.open(png).size
                w_mm, h_mm = w_px / 300 * 25.4, h_px / 300 * 25.4
                pdf.ln(2)
                y = pdf.get_y()
                pdf.image(str(png), x=(210 - w_mm) / 2, y=y, w=w_mm, h=h_mm)
                pdf.set_font("Helvetica", "", 11)
                pdf.set_xy(210 - 22 - 12, y + h_mm / 2 - 3)
                pdf.cell(12, 6, f"({eq_no})", align="R")
                pdf.set_y(y + h_mm + 3)
            else:
                pdf.set_font("Courier", "", 11)
                pdf.cell(0, 8, f"    {latex_plain(latex)}    ({eq_no})",
                         new_x="LMARGIN", new_y="NEXT")
        elif line.strip():
            pdf.set_font("Helvetica", "", 11)
            pdf.multi_cell(0, 6, line, new_x="LMARGIN", new_y="NEXT")
            pdf.ln(1)
    for out in outs:
        out.parent.mkdir(parents=True, exist_ok=True)
        pdf.output(str(out))
        print("wrote", out.relative_to(ROOT))


def main() -> int:
    for src, (eq_style, outs) in SAMPLES.items():
        build(src, eq_style, outs)
    return 0


if __name__ == "__main__":
    sys.exit(main())
