# Changelog

## 0.2.0 (2026-11-05)

- Bullets revealed as the narration reaches them (`render.reveal_bullets`) (#11)
- Source figures on slides: extracted with Docling or from Markdown, numbered across the
  course, chosen per slide, approved in review, drawn on slide images and in the PPTX (#12)
- French pipeline: voice chosen from the deck language, French problem wording, French
  example course (#14)
- Requests fitted to the model's context; settings for 8k-context servers; theory slides no
  longer keep a model-written `source_doc` (#9)
- `course2video score`: reviewer score sheets, agreement, review time (#10)
- Citation file and changelog (#4)
- Tested end to end with gpt-oss-120b on our internal server; example outputs regenerated
  with it (`examples/*/output/`) and `scripts/run_gpt_oss_eval.sh` to repeat the runs (#9, #2, #3)
- Fixes from the gpt-oss runs: no invented examples, every chapter gets a slide, plain-text
  titles and bullets, brace-less `\mathbf`, `cases` equations, decimal commas in grounding
- `course.yaml` validated, with errors naming the file, the entry and the allowed values (#7)
- Hardening: Docling version stored with the parse cache, pinned local-only Ollama in
  docker-compose, LLM backoff on connection errors, 429 and 5xx (#15)
- Review fixes: English decks use `tts.piper_model`, only numbered chapters set a minimum
  slide count, read timeouts are not retried, Docling temp folder removed

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
