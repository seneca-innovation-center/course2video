# Third-party components and licences

This project's own code is Apache-2.0 (see `LICENSE`). Each component below keeps its
own licence. **Do not read this table as legal advice.** It is a working audit for
institutions evaluating the pipeline. Model-weight licences and terms change over time,
so re-check before every release.

Status: **v0 draft (2026-10-29).** Code licences of Python packages were read from the
installed package metadata. Rows marked *verify* have not been checked against the
primary source yet.

## Runtime: always installed

| Component | Used for | Code licence | Model / data licence | Notes |
|---|---|---|---|---|
| pydantic | slide/script schemas | MIT | n/a | |
| PyYAML | config | MIT | n/a | |
| python-pptx | .pptx output | MIT | n/a | |
| Pillow | slide images | MIT-CMU | n/a | |
| pypdf | lightweight PDF text parser | BSD-3-Clause | n/a | |
| httpx | OpenAI-compatible client | BSD-3-Clause | n/a | |

## Optional extras

| Component | Extra | Code licence | Model / data licence | Notes |
|---|---|---|---|---|
| Docling (+ docling-core, docling-ibm-models) | `docling` | MIT | Layout/table/formula models are downloaded from Hugging Face at first use: *verify* each model card | Pulls in PyTorch (BSD-style) and transformers (Apache-2.0) |
| matplotlib | `math` | Matplotlib licence (PSF-based, BSD-compatible) | n/a | Equation rendering (mathtext), bundled DejaVu fonts |
| **piper-tts** | `piper` | **GPL-3.0-or-later** | Voice: see below | **Copyleft.** Kept optional and loaded only when `tts.backend: piper`. Distributing a bundle that includes it (e.g. the Docker image built with `EXTRAS=piper`) brings GPL obligations for that bundle. Uses espeak-ng for phonemes (GPL-3.0) |
| onnxruntime | (via piper) | MIT | n/a | |

## External programs (not installed by pip)

| Component | Used for | Licence | Notes |
|---|---|---|---|
| FFmpeg | video assembly | LGPL-2.1+ **or GPL**, depending on the build | Builds with libx264 (most distro and Homebrew builds) are GPL. We call it as a separate program and never link to it |
| LibreOffice (optional renderer) | pptx to images | MPL-2.0 | Called as a separate program |

## Models

| Model | Where it runs | Licence | Notes |
|---|---|---|---|
| **gpt-oss-120b / gpt-oss-20b** (OpenAI) | **on-premises** via vLLM or Ollama | Apache-2.0 (weights) plus the gpt-oss usage policy | Target LLM for the self-hosted deployment. *verify* the current usage policy |
| Piper voice `en_US-ljspeech-medium` | local | Dataset: LJ Speech, **public domain** (from the voice's MODEL_CARD). Licence of the trained voice weights is not stated in the model card: *verify* | Downloaded by `scripts/download_models.sh`, never committed |
| Piper voice `fr_FR-siwis-medium` | local | Dataset: SIWIS French speech synthesis database, **CC BY 4.0** (from the voice's MODEL_CARD). The voice is **fine-tuned from the English `lessac` voice**, whose dataset has its own terms: *verify both* before redistribution | Downloaded by `scripts/download_models.sh`, used for decks with `language: fr` |

## Development only

| Component | Licence | Notes |
|---|---|---|
| pytest | MIT | |
| jsonschema | MIT | |
| fpdf2 | LGPL-3.0-only | Only used by `scripts/make_sample_pdf.py` to build the sample PDF |
| ruff | MIT | |

## Content

| Item | Licence |
|---|---|
| `examples/sample_course/vector_spaces.md` and the PDFs built from it | CC-BY-4.0, written for this project |
| `examples/probability_course/probability.md` and the PDF built from it | CC-BY-4.0, written for this project |
| `examples/cours_probabilites/` (French course, TD and corrigé) | CC-BY-4.0, written for this project |
| MIT 18.05 Spring 2022 reading 3, problem set 2 and solutions (`examples/mit1805_bayes/`) | **CC BY-NC-SA 4.0**, © MIT / J. Orloff, J. Bloom. **Not committed**: downloaded by `scripts/fetch_mit1805_example.sh`. Outputs made from them must keep CC BY-NC-SA and attribution |

## Before claiming "fully open source / permissive"

- [ ] Verify every Docling model card (layout, TableFormer, formula model).
- [ ] Verify the licence of the Piper voice weights, or pick a voice with an explicit licence.
- [ ] Decide whether GPL TTS (Piper) is acceptable, or add a permissive TTS alternative.
- [ ] Re-check the gpt-oss usage policy.
- [ ] Document which FFmpeg build the Docker image ships.
