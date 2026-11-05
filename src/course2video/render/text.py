from __future__ import annotations

import re

_SYMBOLS = {
    r"\cap": "∩", r"\cup": "∪", r"\mid": "|", r"\leq": "≤", r"\le": "≤", r"\geq": "≥",
    r"\ge": "≥", r"\neq": "≠", r"\cdot": "·", r"\times": "×", r"\ldots": "…", r"\cdots": "…",
    r"\dots": "…", r"\in": "∈", r"\subseteq": "⊆", r"\subset": "⊂", r"\emptyset": "∅",
    r"\infty": "∞", r"\sum": "Σ", r"\to": "→", r"\approx": "≈", r"\Omega": "Ω",
    r"\alpha": "α", r"\beta": "β", r"\lambda": "λ", r"\mu": "μ", r"\sigma": "σ",
}
_BB = {"R": "ℝ", "N": "ℕ", "Z": "ℤ", "Q": "ℚ", "C": "ℂ"}


def plain_math(text: str) -> str:
    if "\\" not in text and "$" not in text:
        return text
    text = re.sub(r"\\[()\[\]]", "", text).replace("$", "")
    text = re.sub(r"\\mathbb\s*\{?([A-Z])\}?", lambda m: _BB.get(m.group(1), m.group(1)), text)
    text = re.sub(r"\\(?:mathbf|mathrm|mathit|boldsymbol|text|operatorname)\s*\{([^{}]*)\}", r"\1", text)
    text = re.sub(r"\\(?:mathbf|mathrm|mathit|boldsymbol)\s+(\w)", r"\1", text)
    text = re.sub(r"\\[dt]?frac\s*\{([^{}]*)\}\s*\{([^{}]*)\}", r"\1/\2", text)
    for cmd in sorted(_SYMBOLS, key=len, reverse=True):
        text = re.sub(re.escape(cmd) + r"(?![A-Za-z])", _SYMBOLS[cmd], text)
    text = re.sub(r"_\{([^{}]*)\}", r"\1", text)
    text = re.sub(r"\\,|\;|\\!|\\ ", " ", text)
    return re.sub(r"\s{2,}", " ", text).strip()
