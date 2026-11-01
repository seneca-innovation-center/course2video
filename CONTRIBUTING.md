# Contributing

Thanks for helping. The project is in early development, so issues describing real course
material that breaks the pipeline are as valuable as code.

## Setup

```bash
make setup        # venv + light install (tests, mock demo)
make test         # offline: no GPU, no network
make setup-full   # + Docling, Piper, Piper voice download
```

On macOS with Python 3.14, the editable install's `.pth` file can be skipped if the file
is marked hidden (this happens under iCloud-synced folders). The Makefile and pytest set
`PYTHONPATH=src` so this does not matter; to use the `course2video` command directly, run
`chflags -R nohidden .venv`.

## Ground rules

- **Tests must run without a GPU or network.** Use `MockBackend` (scripted responses for
  edge cases) and `StubTTS`. Real-model tests go behind `@pytest.mark.llm`.
- **Schemas come from the Pydantic models.** If you change `slides/models.py` or
  `script/models.py`, run `make schemas` and commit the JSON files.
- **New components need a row in `LICENSES_THIRD_PARTY.md`**: code licence *and* model or
  data licence. Copyleft or non-commercial terms must be stated plainly.
- **Never commit model weights or course material you do not have the right to share.**
  Sample content must be openly licensed; record its source and licence.
- **Do not claim what is not measured.** README statements about quality need a number from
  `eval/` or a test behind them.

## Adding a backend

| To add | Implement | Register in |
|---|---|---|
| an LLM | `LLMBackend.complete()` in `llm/` | `llm/__init__.py:get_backend` and `config.py` |
| a parser | `Parser.parse()` in `parsing/` | `parsing/__init__.py:get_parser` and `config.py` |
| a TTS engine | `TTSBackend.synthesize()` in `tts/` | `tts/__init__.py:get_tts` and `config.py` |
