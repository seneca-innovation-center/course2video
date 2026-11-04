# Changelog

## 0.2.0 (unreleased)

- Bullets revealed as the narration reaches them (`render.reveal_bullets`) (#11)
- Source figures on slides: extracted with Docling or from Markdown, numbered across the
  course, chosen per slide, approved in review, drawn on slide images and in the PPTX (#12)
- French pipeline: voice chosen from the deck language, French problem wording, French
  example course (#14)
- Requests fitted to the model's context; settings for 8k-context servers; theory slides no
  longer keep a model-written `source_doc` (#9)
- `course2video score`: reviewer score sheets, agreement, review time (#10)
- Citation file and changelog (#4)

## 0.1.0 (2026-11-04)

- Course folder input (lecture notes, exercises, solutions) with problems linked to their
  solutions by number; roles from `course.yaml` or file names
- Docling parsing with formula decoding and a parse cache
- Slide JSON with talking points, validated and retried; lecturer review in `slides.md`
  (edits never dropped silently)
- Lecture-style narration from approved slides only; coverage and grounding checks
- Lecture structure (title, outline, part dividers, progress bar, summary), PPTX, Piper TTS,
  FFmpeg video with subtitles in sync, optional one video per part
- OpenAI-compatible backend for gpt-oss (vLLM, Ollama) and an offline mock for tests
- `docs/requirements.md`, licence table, offline test suite and CI
