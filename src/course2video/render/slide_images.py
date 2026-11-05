from __future__ import annotations

import re
import shutil
import subprocess
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from ..config import RenderConfig
from .equations import render_equation_png
from .lecture import Frame, section_label

BG = (255, 255, 255)
BAND = (24, 54, 92)
ACCENT = (232, 163, 23)
TITLE_FG = (255, 255, 255)
BAND_MUTED = (170, 190, 215)
TEXT = (30, 30, 30)
MUTED = (120, 120, 120)
TRACK = (225, 229, 235)
KIND_BAND = {"theory": BAND, "exercise": (21, 101, 72), "solution": (88, 52, 128)}


def _font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    name = "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"
    candidates = []
    try:
        import matplotlib

        candidates.append(Path(matplotlib.get_data_path()) / "fonts" / "ttf" / name)
    except ImportError:
        pass
    candidates += [
        Path("/usr/share/fonts/truetype/dejavu/") / name,
        Path("/System/Library/Fonts/Supplemental/" + ("Arial Bold.ttf" if bold else "Arial.ttf")),
    ]
    for c in candidates:
        if c.exists():
            return ImageFont.truetype(str(c), size)
    return ImageFont.load_default(size=size)


_SUPERSCRIPT = str.maketrans("0123456789n+-", "⁰¹²³⁴⁵⁶⁷⁸⁹ⁿ⁺⁻")


def pretty(text: str) -> str:
    from .text import plain_math

    text = plain_math(text)
    return re.sub(r"\^\{?([0-9n+-])\}?(?![\w{])", lambda m: m.group(1).translate(_SUPERSCRIPT), text)


def _wrap(draw: ImageDraw.ImageDraw, text: str, font, max_w: int) -> list[str]:
    text = pretty(text)
    lines, cur = [], ""
    for word in text.split():
        trial = f"{cur} {word}".strip()
        if draw.textlength(trial, font=font) <= max_w or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


class _Canvas:
    def __init__(self, cfg: RenderConfig):
        self.W, self.H = cfg.width, cfg.height
        self.s = cfg.width / 1920
        self.margin = self.px(110)
        self.img = Image.new("RGB", (self.W, self.H), BG)
        self.d = ImageDraw.Draw(self.img)

    def px(self, v: float) -> int:
        return int(v * self.s)

    def centered(self, y: int, text: str, font, fill) -> None:
        text = pretty(text)
        self.d.text(((self.W - self.d.textlength(text, font=font)) // 2, y), text, font=font, fill=fill)


def _progress(c: _Canvas, frame: Frame, section_starts: list[int], show: bool) -> None:
    if not show or frame.total < 2:
        return
    h = c.px(10)
    y = c.H - h
    c.d.rectangle([0, y, c.W, c.H], fill=TRACK)
    c.d.rectangle([0, y, int(c.W * (frame.index + 1) / frame.total), c.H], fill=ACCENT)
    for start in section_starts:
        x = int(c.W * start / frame.total)
        c.d.rectangle([x - c.px(2), y - c.px(6), x + c.px(2), c.H], fill=BAND)


def _footer(c: _Canvas, frame: Frame, deck_title: str) -> None:
    f = _font(c.px(26))
    y = c.H - c.px(62)
    if frame.kind != "section":
        c.d.text((c.margin, y), pretty(deck_title), font=f, fill=MUTED)
    num = f"{frame.index + 1} / {frame.total}"
    c.d.text((c.W - c.margin - c.d.textlength(num, font=f), y), num, font=f, fill=MUTED)


def _header(c: _Canvas, title: str, label: str, band=BAND) -> int:
    band_h = c.px(190)
    c.d.rectangle([0, 0, c.W, band_h], fill=band)
    c.d.rectangle([0, band_h, c.W, band_h + c.px(6)], fill=ACCENT)
    tfont = _font(c.px(58), bold=True)
    lines = _wrap(c.d, title, tfont, c.W - 2 * c.margin)[:2]
    lfont = _font(c.px(26), bold=True)
    block = (c.px(40) if label else 0) + len(lines) * c.px(68)
    y = (band_h - block) // 2
    if label:
        c.d.text((c.margin, y), label.upper(), font=lfont, fill=ACCENT)
        y += c.px(40)
    for line in lines:
        c.d.text((c.margin, y), line, font=tfont, fill=TITLE_FG)
        y += c.px(68)
    return band_h + c.px(6)


def _figure_image(figures_dir: Path | None, fid: str) -> Image.Image | None:
    if not fid or figures_dir is None:
        return None
    found = sorted(figures_dir.glob(f"{fid}.*"))
    found = [f for f in found if f.suffix.lower() in (".png", ".jpg", ".jpeg")]
    if not found:
        return None
    img = Image.open(found[0]).convert("RGBA")
    flat = Image.new("RGB", img.size, BG)
    flat.paste(img, (0, 0), img)
    return flat


def _content(c: _Canvas, frame: Frame, label: str, eq_dir: Path, visible: int | None = None,
             figures_dir: Path | None = None) -> None:
    s = frame.slide
    top = _header(c, s.title, label, KIND_BAND.get(s.kind, BAND))
    W, H, sx, margin = c.W, c.H, c.s, c.margin

    eq_imgs = []
    for eq in s.equations:
        png = render_equation_png(eq.latex, eq_dir, fontsize=int(44 * sx))
        eq_imgs.append(Image.open(png).convert("RGBA") if png else eq.latex)
    eq_h = sum((e.height if isinstance(e, Image.Image) else c.px(60)) + c.px(30) for e in eq_imgs)
    footer_h = c.px(90)
    avail = H - top - c.px(50) - eq_h - footer_h

    fig = _figure_image(figures_dir, s.figure)
    text_right = int(W * 0.55) if fig else W - margin
    if fig:
        x0, y0 = text_right + c.px(30), top + c.px(40)
        box_w, box_h = W - margin - x0, H - footer_h - eq_h - c.px(20) - y0
        if box_w > 0 and box_h > 0:
            r = min(box_w / fig.width, box_h / fig.height)
            fig = fig.resize((max(1, int(fig.width * r)), max(1, int(fig.height * r))))
            c.img.paste(fig, (x0 + (box_w - fig.width) // 2, y0 + (box_h - fig.height) // 2))
    for size in (44, 40, 36, 33, 30, 27, 24):
        bfont = _font(int(size * sx))
        line_h = int(size * 1.35 * sx)
        wrapped = [_wrap(c.d, b, bfont, text_right - margin - c.px(50)) for b in s.bullets]
        need = sum(len(w) * line_h + int(size * 0.6 * sx) for w in wrapped)
        if need <= avail:
            break
    y = top + c.px(50)
    for i, lines in enumerate(wrapped):
        shown = visible is None or i < visible
        r = c.px(7)
        if shown:
            c.d.ellipse([margin, y + line_h // 2 - r, margin + 2 * r, y + line_h // 2 + r],
                        fill=BAND)
        for line in lines:
            if shown:
                c.d.text((margin + c.px(50), y), line, font=bfont, fill=TEXT)
            y += line_h
        y += int(size * 0.6 * sx)

    y = max(y + c.px(20), H - footer_h - eq_h)
    for e in eq_imgs:
        if isinstance(e, Image.Image):
            if e.width > W - 2 * margin:
                r = (W - 2 * margin) / e.width
                e = e.resize((int(e.width * r), int(e.height * r)))
            c.img.paste(e, ((W - e.width) // 2, y), e)
            y += e.height + c.px(30)
        else:
            c.centered(y, e, _font(c.px(36)), TEXT)
            y += c.px(90)


def _title(c: _Canvas, frame: Frame) -> None:
    c.d.rectangle([0, 0, c.W, c.H], fill=BAND)
    tfont = _font(c.px(84), bold=True)
    lines = _wrap(c.d, frame.heading, tfont, c.W - 2 * c.margin)
    y = c.H // 2 - len(lines) * c.px(100) // 2 - c.px(60)
    for line in lines:
        c.centered(y, line, tfont, TITLE_FG)
        y += c.px(100)
    c.d.rectangle([c.W // 2 - c.px(120), y + c.px(20), c.W // 2 + c.px(120), y + c.px(28)], fill=ACCENT)
    y += c.px(70)
    sfont = _font(c.px(38))
    for item in frame.items:
        c.centered(y, item, sfont, BAND_MUTED)
        y += c.px(56)


def _outline(c: _Canvas, frame: Frame, heading: str, current: int | None, done_upto: int,
             check: bool = False) -> None:
    top = _header(c, heading, "")
    n = len(frame.items)
    size = 44 if n <= 6 else 36 if n <= 9 else 30
    f, fb = _font(c.px(size)), _font(c.px(size), bold=True)
    step = min(c.px(size * 2.0), (c.H - top - c.px(200)) // max(n, 1))
    y = top + c.px(60)
    for i, name in enumerate(frame.items):
        is_cur = i == current
        color = BAND if is_cur else (MUTED if i < done_upto else TEXT)
        if is_cur:
            c.d.rectangle([c.margin - c.px(30), y - c.px(14), c.W - c.margin, y + step - c.px(22)],
                          fill=(245, 236, 214))
            c.d.rectangle([c.margin - c.px(30), y - c.px(14), c.margin - c.px(22), y + step - c.px(22)],
                          fill=ACCENT)
        marker = "✓" if (check or i < done_upto) else f"{i + 1}."
        c.d.text((c.margin, y), marker, font=fb, fill=ACCENT if marker == "✓" else color)
        c.d.text((c.margin + c.px(90), y), pretty(name), font=fb if is_cur else f, fill=color)
        y += step


def _section(c: _Canvas, frame: Frame, part_word: str) -> None:
    split = int(c.W * 0.42)
    c.d.rectangle([0, 0, split, c.H], fill=BAND)
    c.d.rectangle([split, 0, split + c.px(8), c.H], fill=ACCENT)
    pfont = _font(c.px(40), bold=True)
    c.d.text((c.margin, c.H // 2 - c.px(170)), f"{part_word.upper()} {frame.section_index + 1}",
             font=pfont, fill=ACCENT)
    nfont = _font(c.px(66), bold=True)
    y = c.H // 2 - c.px(100)
    for line in _wrap(c.d, frame.heading, nfont, split - c.margin - c.px(60))[:4]:
        c.d.text((c.margin, y), line, font=nfont, fill=TITLE_FG)
        y += c.px(80)
    n = len(frame.items)
    size = 34 if n <= 8 else 28
    f, fb = _font(c.px(size)), _font(c.px(size), bold=True)
    step = min(c.px(size * 2.1), (c.H - c.px(260)) // max(n, 1))
    y = (c.H - step * n) // 2
    x = split + c.px(90)
    for i, name in enumerate(frame.items):
        cur = i == frame.section_index
        color = BAND if cur else (MUTED if i < frame.section_index else TEXT)
        marker = "✓" if i < frame.section_index else ("▶" if cur else f"{i + 1}.")
        c.d.text((x, y), marker, font=fb, fill=ACCENT if cur or i < frame.section_index else color)
        line = _wrap(c.d, name, fb if cur else f, c.W - x - c.px(170))[0]
        c.d.text((x + c.px(70), y), line, font=fb if cur else f, fill=color)
        y += step


class _Context:
    def __init__(self, frames: list[Frame], deck_title: str, language: str, out_dir: Path,
                 cfg: RenderConfig, progress_bar: bool):
        from .lecture import templates

        self.frames, self.deck_title, self.language = frames, deck_title, language
        self.cfg, self.progress_bar = cfg, progress_bar
        self.eq_dir = out_dir.parent / "equations"
        self.figures_dir = out_dir.parent / "figures"
        self.t = templates(language)
        self.n_sections = len({f.section_index for f in frames if f.section_index is not None})
        self.starts = []
        seen = set()
        for f in frames:
            if f.section_index is not None and f.section_index not in seen:
                seen.add(f.section_index)
                self.starts.append(f.index)


def _draw(f: Frame, x: _Context, visible: int | None = None) -> Image.Image:
    c = _Canvas(x.cfg)
    t = x.t
    if f.kind == "content" and f.slide.kind != "theory":
        word = t["exercise"] if f.slide.kind == "exercise" else t["solution"]
        label = f"{word}  \u00b7  {f.slide.source_doc}" if f.slide.source_doc else word
        _content(c, f, label, x.eq_dir, visible, x.figures_dir)
    elif f.kind == "content":
        label = section_label(f, x.n_sections, x.language)
        if label:
            sec = next((y.heading for y in x.frames
                        if y.kind == "section" and y.section_index == f.section_index), "")
            label = f"{label}  \u00b7  {sec}" if sec else label
        _content(c, f, label, x.eq_dir, visible, x.figures_dir)
    elif f.kind == "title":
        _title(c, f)
    elif f.kind == "agenda":
        _outline(c, f, f.heading, current=None, done_upto=0)
    elif f.kind == "section":
        _section(c, f, t["part"])
    elif f.kind == "closing":
        _outline(c, f, f.heading, current=None, done_upto=0, check=True)
        c.centered(c.H - c.px(190), t["thanks"], _font(c.px(44), bold=True), BAND)
    if f.kind != "title":
        _footer(c, f, x.deck_title)
    _progress(c, f, x.starts, x.progress_bar)
    return c.img


def render_frames(frames: list[Frame], deck_title: str, language: str, out_dir: Path,
                  cfg: RenderConfig, progress_bar: bool = True) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    for old in out_dir.glob("*.png"):
        old.unlink()
    x = _Context(frames, deck_title, language, out_dir, cfg, progress_bar)
    paths = []
    for f in frames:
        p = out_dir / f"frame_{f.index + 1:03d}.png"
        _draw(f, x).save(p)
        paths.append(p)
    return paths


def render_reveal_states(frames: list[Frame], deck_title: str, language: str, out_dir: Path,
                         cfg: RenderConfig, progress_bar: bool = True) -> dict[int, list[Path]]:
    x = _Context(frames, deck_title, language, out_dir, cfg, progress_bar)
    states: dict[int, list[Path]] = {}
    for f in frames:
        if f.kind != "content" or len(f.slide.bullets) < 2:
            continue
        paths = []
        for k in range(1, len(f.slide.bullets)):
            p = out_dir / f"frame_{f.index + 1:03d}_b{k}.png"
            _draw(f, x, visible=k).save(p)
            paths.append(p)
        paths.append(out_dir / f"frame_{f.index + 1:03d}.png")
        states[f.index] = paths
    return states


def render_libreoffice(pptx: Path, out_dir: Path, cfg: RenderConfig) -> list[Path]:
    soffice = shutil.which("soffice") or shutil.which("libreoffice")
    if not soffice:
        raise RuntimeError("LibreOffice (soffice) not found; use render.renderer: pillow")
    try:
        import pypdfium2 as pdfium
    except ImportError as e:
        raise RuntimeError("pip install pypdfium2 to rasterise LibreOffice output") from e
    out_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        subprocess.run(
            [soffice, "--headless", "--convert-to", "pdf", "--outdir", tmp, str(pptx)],
            check=True, capture_output=True,
        )
        pdf = pdfium.PdfDocument(str(Path(tmp) / (pptx.stem + ".pdf")))
        paths = []
        for i, page in enumerate(pdf, start=1):
            scale = cfg.width / page.get_width()
            img = page.render(scale=scale).to_pil().convert("RGB").resize((cfg.width, cfg.height))
            p = out_dir / f"frame_{i:03d}.png"
            img.save(p)
            paths.append(p)
    return paths
