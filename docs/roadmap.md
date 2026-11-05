# Roadmap

Status: **early development.** Items are listed roughly in order. Nothing below is
implemented unless it says so.

## Done in v0
- [x] Single-document pipeline: PDF → Markdown → validated slide JSON → review → script → alignment → PPTX → TTS → MP4 + SRT
- [x] Pluggable LLM backends: mock (CI), OpenAI-compatible (vLLM / Ollama for gpt-oss)
- [x] Validation with error feedback and bounded retries
- [x] Lecturer review via editable Markdown or JSON
- [x] Lexical coverage check per slide
- [x] Lecture structure: title, outline, part dividers, progress bar, summary
- [x] **Course packages**: lecture + exercises + solutions as one input; roles from `course.yaml`
      or file names; exercises linked to solutions by number; worked-example slides
- [x] **Target length** (`--minutes`) driving slide count and words per slide

## Next
- [x] **Local LLM run:** four example courses and the smoke test with gpt-oss-120b on our internal server (`examples/demo.md`)
- [ ] gpt-oss-20b on modest hardware; score gpt-oss-120b output with `eval/rubric.md`
- [ ] **Link exercises to theory sections** (which part of the lecture a problem uses), and
      several lectures/chapters per course folder with per-chapter exercises
- [ ] Practical sessions (TP/labs): typed already, not yet turned into slides
- [ ] **Parser routing:** rule-based choice between Docling, Marker and MinerU (text-layer presence, share of image-only pages, equation density), evaluated against single-parser output
- [ ] **Scanned documents:** OCRmyPDF before parsing
- [ ] **Hierarchical multi-document retrieval** so theory, exercises and solutions stay consistent
- [ ] **Review UI** (web) instead of editing files
- [ ] **Better alignment metric:** embedding similarity next to the lexical score
- [ ] **Equation narration** checked separately (LaTeX → spoken form)
- [ ] **Translation** (hypothesis): translate with summary + slide JSON + script + glossary as context; ablation with vs. without context, starting with English → French and Spanish
- [ ] **Permissive TTS option** next to Piper (GPL); see LICENSES_THIRD_PARTY.md
- [ ] Word-level subtitle timing

## Not planned
- Generative video models (assembly must stay reproducible)
- Voice cloning without explicit written consent from the speaker
