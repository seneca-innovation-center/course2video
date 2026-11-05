from __future__ import annotations

import hashlib
import logging
import re
from pathlib import Path

log = logging.getLogger(__name__)


def normalize_for_mathtext(latex: str) -> str:
    latex = re.sub(r"\\[td]frac(?![a-zA-Z])", r"\\frac", latex)
    latex = re.sub(r"\\frac\s*(\w)\s*(\w)", r"\\frac{\1}{\2}", latex)
    latex = re.sub(r"\\frac\s*(\w)\s*\{", r"\\frac{\1}{", latex)
    latex = re.sub(r"\\frac\s*(\{[^{}]*\})\s*(\w)", r"\\frac\1{\2}", latex)
    latex = re.sub(r"\\boldsymbol", r"\\mathbf", latex)
    latex = re.sub(r"\\(mathbf|mathrm|mathit|mathcal|mathbb)\s+([A-Za-z0-9])", r"\\\1{\2}", latex)
    latex = re.sub(r"\s*([_^])\s*", r"\1", latex)
    latex = re.sub(r"(\\[A-Za-z]+)\s+\{", r"\1{", latex)
    latex = re.sub(r"\{\s+", "{", latex)
    latex = re.sub(r"\s+\}", "}", latex)
    latex = re.sub(r"\}\s+\{", "}{", latex)
    latex = re.sub(r"\\intertext\{.*$", "", latex)
    return latex.strip().rstrip("\\").strip()


_ENV = re.compile(r"\\begin\{(cases|aligned|align\*?|gathered|array)\}(?:\{[^}]*\})?(.*?)\\end\{\1\}",
                  re.S)


def split_rows(latex: str) -> list[str]:
    m = _ENV.search(latex)
    if not m:
        return [latex]
    prefix = latex[:m.start()].strip()
    suffix = latex[m.end():].strip()
    rows = [r.strip() for r in re.split(r"\\\\", m.group(2)) if r.strip()]
    out = []
    for i, row in enumerate(rows):
        cells = [c.strip() for c in row.split("&")]
        if m.group(1) == "cases" and len(cells) > 1:
            body = cells[0] + r",\quad " + " ".join(cells[1:])
        else:
            body = " ".join(cells)
        out.append(f"{prefix} {body}".strip() if i == 0 else body)
    if suffix:
        out[-1] = f"{out[-1]} {suffix}"
    return out


def _stack_rows(rows: list[str], out: Path, mathtext, prop) -> None:
    import tempfile

    from PIL import Image

    images = []
    with tempfile.TemporaryDirectory() as tmp:
        for k, row in enumerate(rows):
            path = Path(tmp) / f"row{k}.png"
            mathtext.math_to_image(f"${row}$", str(path), prop=prop, dpi=100, format="png")
            images.append(Image.open(path).convert("RGBA"))
        gap = max(4, images[0].height // 3)
        width = max(i.width for i in images)
        height = sum(i.height for i in images) + gap * (len(images) - 1)
        canvas = Image.new("RGBA", (width, height), (255, 255, 255, 0))
        y = 0
        for img in images:
            canvas.paste(img, (0, y), img)
            y += img.height + gap
        canvas.save(out)


def render_equation_png(latex: str, out_dir: Path, fontsize: int = 40) -> Path | None:
    latex = normalize_for_mathtext(latex)
    try:
        import matplotlib

        matplotlib.use("Agg")
        from matplotlib import mathtext
        from matplotlib.font_manager import FontProperties
    except ImportError:
        return None
    out_dir.mkdir(parents=True, exist_ok=True)
    digest = hashlib.sha1(f"{fontsize}:{latex}".encode()).hexdigest()[:12]
    out = out_dir / f"eq_{digest}.png"
    if out.exists():
        return out
    try:
        rows = split_rows(latex)
        if len(rows) == 1:
            mathtext.math_to_image(
                f"${latex}$", str(out), prop=FontProperties(size=fontsize), dpi=100, format="png"
            )
        else:
            _stack_rows(rows, out, mathtext, FontProperties(size=fontsize))
    except Exception as e:
        log.warning("could not render equation %r: %s", latex, e)
        out.unlink(missing_ok=True)
        return None
    return out
