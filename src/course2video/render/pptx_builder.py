from __future__ import annotations

from pathlib import Path

from pptx import Presentation
from pptx.util import Emu, Inches, Pt

from .equations import render_equation_png
from .lecture import Frame
from .text import plain_math

LAYOUT_TITLE, LAYOUT_SECTION, LAYOUT_TITLE_ONLY = 0, 2, 5


def _bullets(slide, items: list[str], top, height, size: int, width=None) -> None:
    box = slide.shapes.add_textbox(Inches(0.7), top, width or Inches(11.9), height)
    tf = box.text_frame
    tf.word_wrap = True
    for i, b in enumerate(items):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.text = b
        p.font.size = Pt(size)
        p.space_after = Pt(10)


def _content(prs, f: Frame, eq_dir: Path, figures_dir: Path | None = None):
    s = f.slide
    slide = prs.slides.add_slide(prs.slide_layouts[LAYOUT_TITLE_ONLY])
    slide.shapes.title.text = plain_math(s.title)
    slide.shapes.title.text_frame.paragraphs[0].font.size = Pt(36)
    body_h = Inches(5.6 - 1.1 * len(s.equations))
    fig = None
    if s.figure and figures_dir is not None:
        fig = next((p for p in sorted(figures_dir.glob(f"{s.figure}.*"))
                    if p.suffix.lower() in (".png", ".jpg", ".jpeg")), None)
    text_w = Inches(6.9) if fig else Inches(11.9)
    _bullets(slide, ["• " + plain_math(b) for b in s.bullets], Inches(1.5), body_h,
             24 if len(s.bullets) <= 4 else 20, width=text_w)
    if fig:
        pic = slide.shapes.add_picture(str(fig), Inches(7.9), Inches(1.6), width=Inches(4.8))
        if pic.height > body_h:
            ratio = body_h / pic.height
            pic.height = Emu(int(body_h))
            pic.width = Emu(int(pic.width * ratio))
    top = Inches(1.5) + body_h
    for eq in s.equations:
        png = render_equation_png(eq.latex, eq_dir)
        if png is not None:
            pic = slide.shapes.add_picture(str(png), Inches(0.9), top, height=Inches(0.8))
            if pic.width > Inches(11.5):
                ratio = Inches(11.5) / pic.width
                pic.width = Inches(11.5)
                pic.height = Emu(int(pic.height * ratio))
        else:
            t = slide.shapes.add_textbox(Inches(0.9), top, Inches(11.5), Inches(0.8))
            t.text_frame.text = eq.latex
            t.text_frame.paragraphs[0].font.size = Pt(22)
        top += Inches(1.1)
    return slide


def build_pptx(frames: list[Frame], out_path: Path, part_word: str = "Part",
               figures_dir: Path | None = None) -> Path:
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    eq_dir = out_path.parent / "equations"

    for f in frames:
        if f.kind == "content":
            slide = _content(prs, f, eq_dir, figures_dir)
        elif f.kind == "title":
            slide = prs.slides.add_slide(prs.slide_layouts[LAYOUT_TITLE])
            slide.shapes.title.text = f.heading
            slide.placeholders[1].text = "\n".join(f.items)
        elif f.kind == "section":
            slide = prs.slides.add_slide(prs.slide_layouts[LAYOUT_SECTION])
            slide.shapes.title.text = f.heading
            slide.placeholders[1].text = f"{part_word} {f.section_index + 1} / {len(f.items)}"
        else:
            slide = prs.slides.add_slide(prs.slide_layouts[LAYOUT_TITLE_ONLY])
            slide.shapes.title.text = f.heading
            mark = "✓" if f.kind == "closing" else None
            _bullets(slide, [f"{mark or str(i + 1) + '.'} {x}" for i, x in enumerate(f.items)],
                     Inches(1.6), Inches(5.4), 26)
        slide.notes_slide.notes_text_frame.text = f.narration

    out_path.parent.mkdir(parents=True, exist_ok=True)
    prs.save(str(out_path))
    return out_path
