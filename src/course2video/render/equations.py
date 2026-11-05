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
        mathtext.math_to_image(
            f"${latex}$", str(out), prop=FontProperties(size=fontsize), dpi=100, format="png"
        )
    except Exception as e:
        log.warning("could not render equation %r: %s", latex, e)
        out.unlink(missing_ok=True)
        return None
    return out
