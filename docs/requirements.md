# What you need to run it

Numbers marked **measured** come from runs on an Apple M3 laptop (24 GB unified memory, no
NVIDIA GPU). Model memory figures are the published requirements of the models. Anything not
measured yet says so.

## Which step runs where

| Step | Laptop (CPU / Apple Silicon) | GPU server |
|---|---|---|
| Parsing with Docling, **without** formula decoding | yes, seconds per document | yes |
| Parsing with Docling **with** formula decoding | possible but slow (see below) | recommended |
| LLM: gpt-oss-20b (Ollama) | yes, with 16 GB+ memory | yes |
| LLM: gpt-oss-120b (vLLM) | no | yes, one 80 GB GPU |
| Lecturer review (`slides.md`) | yes | n/a |
| Slide images, PPTX, Piper TTS, FFmpeg | yes, about a minute per course | yes |

## LLM memory

| Model | Server | Memory needed | Notes |
|---|---|---|---|
| gpt-oss-120b | vLLM | one 80 GB GPU (H100 / A100 80GB) | reference model for the on-premises deployment |
| gpt-oss-20b | Ollama or vLLM | about 16 GB (GPU, or Apple Silicon unified memory) | smaller option for testing and modest hardware |
| gpt-oss-20b on CPU only | Ollama | 16 GB+ RAM | works, but much slower; not measured yet |

## Parsing time (Docling, formula decoding on)

**Measured** on the laptop CPU. Each file is parsed once and cached by content
(`~/.cache/course2video/parsed`), so re-runs skip this step.

| Document | Pages | Time |
|---|---|---|
| Sample vector spaces notes | 2 | ~4-7 min |
| Sample probability notes (equations as images) | 3 | 12 min |
| MIT 18.05 Reading 3 | 12 | 44 min |
| MIT 18.05 Problem Set 2 solutions | 6 | 24 min |
| MIT 18.05 Problem Set 2 (no display formulas) | 3 | 5 s |

That is roughly **4 minutes per formula-heavy page on CPU**. On a GPU it is expected to be much
faster; **not measured yet**.

## One typical course, end to end

**Measured** on the MIT 18.05 package (12-page reading + problem set + solutions, 20-minute
target, development run with a hosted LLM API):

| Stage | Time |
|---|---|
| Parsing (CPU, first run only) | 68 min |
| Slides (LLM) | 1.6 min |
| Script (LLM) | 1.8 min |
| Slide images + Piper TTS + FFmpeg | 0.9 min |
| Lecturer review | not measured yet ([#10](https://github.com/seneca-innovation-center/course2video/issues/10)) |

LLM times with gpt-oss-120b / gpt-oss-20b are **not measured yet**
([#9](https://github.com/seneca-innovation-center/course2video/issues/9)).

## Disk space

| Item | Size |
|---|---|
| Python environment with Docling and Piper | 1.7 GB |
| Docling models (downloaded on first use) | 1.1 GB |
| Piper voice | 61 MB |
| gpt-oss-120b weights | about 65 GB |
| gpt-oss-20b weights | about 13 GB |
| Output of one 23-minute course | 110 MB (video 24 MB, per-frame WAV audio 58 MB, images 2 MB) |
