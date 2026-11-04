# Known limitations (v0)

Being explicit about gaps is part of the design. Each item says how it shows up and how
the pipeline currently detects it, if at all.

## Input documents

| Limitation | How it shows up | Detected? |
|---|---|---|
| **Scanned PDFs / handwriting** | pypdf finds no text; Docling output is empty or poor | `parser_warnings` in `meta.json` when pages have no text layer. OCR (OCRmyPDF) is a roadmap item |
| **Equations depend on the parser** | Without formula enrichment, Docling writes `<!-- formula-not-decoded -->`. With it, LaTeX can still be wrong (see below) | Undecoded formulas are counted in `parser_warnings`. Wrong-but-valid LaTeX is **not** detected automatically: lecturer review is required |
| **Figures depend on the parser** | Docling extracts pictures with their page; many PDFs have no machine-readable captions, so the LLM sees "[Figure F3: no caption]" and chooses from the surrounding text. Markdown sources use `![caption](file)` | Every figure is listed in `figures/figures.json`; the lecturer approves each `Figure:` line |
| **Rights to reuse source figures** | A figure from a third-party document is shown on the slide as it is | No: the lecturer must check that the figure may be reused, and remove the `Figure:` line otherwise |
| **Tables** | Docling extracts them as Markdown; the slide schema has no table type, so the LLM summarises them as bullets | No |
| **Exercise ↔ solution links by number only** | "Problem 2" in the sheet is linked to "Problem 2" in the solutions. Different numbering, or solutions in a format without "Problem/Exercise N" headings, are not linked | Yes: unmatched problems and solutions are listed in `course_index.json` warnings |
| **Roles from file names** without `course.yaml` | A file named e.g. `week3.pdf` cannot be typed and is skipped | Yes: every guess and every skipped file is a warning; use `course.yaml` |
| **Worked problems are placed after the theory**, not next to the section they use | n/a | No (roadmap) |
| **Target length is an estimate** | Speaking rate measured for one Piper voice (163 words/min); the LLM does not hit word counts exactly | Target vs actual minutes in `meta.json`; short sources give a warning, not padding |
| **pypdf parser** | Text layer only; headings guessed from numbered lines; equation layout lost | Use Docling for real material |

### Observed example: formula decoding on the sample PDF

Running Docling with formula enrichment on `examples/sample_course/vector_spaces.pdf`
(equations typeset as plain monospace lines) produced:

| Source equation | Docling LaTeX |
|---|---|
| `u + v = (u1 + v1, ..., un + vn)` | `\mathbf u \, + \, \mathbf v \, = \, ( \mathbf u { 1 } \, + \, \mathbf v { 1 } \, , \ \dots , \ \mathbf u { n } \, + \, \mathbf v { n } )` |
| `a u = (a u1, ..., a un)` | `a ( u ) = ( a ( u 1 , \dots , a ( u n ) ) \quad ( 2 )`, which has **unbalanced parentheses** and includes the equation number |
| `a(u + v) = a u + a v` | `a ( u + v ) \, = \, a \, u \, + \, a \, v \quad ( 3 )` |

Without formula enrichment, the LLM received no formulas at all. It reconstructed them
from the prose and **said so in the slide notes**, but it also changed the scalar name from
`a` to `c`. Both cases show why equations need human review, and why "valid JSON" says
nothing about correctness.

Equations typeset **as images** (`examples/probability_course/probability.pdf`, 8 equations)
were decoded much better, but one came back with **invented text appended**:

```
P ( A \, | \, B ) = \frac { P ( A \cap B ) } { P ( B ) } \\ \intertext { a g i v e , t h e m u l i n i o t i o n ...
```

In the development run the LLM dropped the garbage when it made the slide, and the renderer now strips
`\intertext` and fixes Docling's spacing (`\sum _ { i = 1 }`), which matplotlib otherwise
draws wrongly. Nothing flags such noise automatically yet.

Formula enrichment is slow without a GPU. On an Apple Silicon laptop the formula model ran
on CPU:

| Document | Pages | Docling time (CPU, formula decoding on) |
|---|---|---|
| Sample vector spaces notes | 2 | ~4-7 min |
| MIT 18.05 Reading 3 | 12 | **44 min** |
| MIT 18.05 Problem Set 2 solutions | 6 | 24 min |
| MIT 18.05 Problem Set 2 | 3 | 5 s (no display formulas) |

Parsed documents are cached by content (`~/.cache/course2video/parsed`), so this is paid
once per file, but a real archive needs a GPU server for the parsing step.

## Generation

| Limitation | How it shows up | Detected? |
|---|---|---|
| LLM output is not deterministic | Two runs give different slides | By design: review approves one version, and assembly is deterministic from there |
| Schema-valid but wrong content | Wrong fact, changed notation, invented example | Lecturer review; `eval/rubric.md` for measurement |
| Talking points go beyond the source | The lecturer-style explanation adds framing, and the model may re-derive steps whose source is a figure the parser dropped | Yes: `grounding.json` flags numbers not found in the source and low word overlap (8 of ~70 points on the MIT run) |
| Narration adds or omits material | Script mentions things not on the slide | Partly: `alignment.json` (coverage, `novel_word_ratio`) |
| Long sections | One section longer than `slides.chunk_chars` is sent whole, never cut | Large prompts may hit a local model's context limit; reduce chunk size |

## Alignment metric

Lexical content-word overlap. Paraphrases with different words count as **misses**;
mentioning the right words in a wrong statement counts as a **hit**. It is a cheap
smoke detector, not a correctness measure. Embedding similarity is on the roadmap.

Observed false negative (development run on the sample, slide 3): the bullet
*"Non-example: y = 2x + 1 is not, since it lacks the zero vector"* scored 0.5, although
the narration says *"the line y equals two x plus one is not a subspace, because it does
not contain the zero vector"*. Formulas are spoken as words ("two x plus one"), and
"lacks" is paraphrased, so the words do not match. Equation-to-speech normalisation would
fix this case. The probability run shows the same pattern: *"P of the intersection is the
product of the probabilities"* was narrated as *"P of A intersect B equals P of A times P of
B"* and scored 0.5.

## Audio and video

| Limitation | Notes |
|---|---|
| Equation reading | The script is asked to say formulas in words; TTS reads whatever it gets. No separate check yet |
| Voices | English (`en_US-ljspeech-medium`) and French (`fr_FR-siwis-medium`), chosen from the deck's language (`tts.piper_voices`). Other languages fall back to the default voice with a warning |
| Subtitle timing | Proportional to text length within each slide, not word-aligned |
| Pillow renderer | Simple layout; equations use matplotlib mathtext (a LaTeX subset). Unsupported LaTeX falls back to raw text |

## Licensing

Piper (`piper-tts`) is GPL-3.0-or-later and FFmpeg builds with libx264 are GPL. Both are
optional or external, but they matter for anyone redistributing a bundle. See
`LICENSES_THIRD_PARTY.md`.
