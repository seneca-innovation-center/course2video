# Schemas

The Pydantic models are the schema; the JSON files are generated from them:

| Model | Source | Generated file |
|---|---|---|
| `Deck` (contains `Slide`, `Equation`) | `src/course2video/slides/models.py` | `schemas/slide.schema.json` |
| `Script` (contains `SlideScript`) | `src/course2video/script/models.py` | `schemas/script.schema.json` |

After changing a model run `make schemas`. A test (`test_committed_schemas_match_models`)
fails if the committed files are out of date.

## Slide deck

```json
{
  "title": "Vector Spaces: A Short Introduction",
  "language": "en",
  "approved": false,
  "slides": [
    {
      "id": 1,
      "title": "Vectors in R^n",
      "bullets": ["A vector is an ordered list of n real numbers", "..."],
      "equations": [
        {"latex": "u + v = (u_1 + v_1, \\ldots, u_n + v_n)",
         "explanation": "Two vectors are added component by component."}
      ],
      "notes": "",
      "source_section": "1. Vectors in R^n"
    }
  ]
}
```

| Field | Rule |
|---|---|
| `slides` | at least 1; `id` unique |
| `title` | 1-120 characters |
| `bullets` | 1-7 items, each non-blank and at most 200 characters |
| `equations` | at most 3; `latex` without `$`, balanced braces; `explanation` required |
| `approved` | set only by the review step, never by the LLM |
| extra fields | rejected (`additionalProperties: false`) |

## What the LLM is asked for

The LLM returns a `SlideBatch` (`{"slides": [...]}`) per chunk of the document. When a
server supports constrained decoding, a *relaxed* copy of the schema is sent
(`llm/base.py:relax_schema`): length and count limits are removed because many decoders
reject them. Those limits are still enforced by Pydantic afterwards, and violations
trigger a retry with the error messages.

## Script

```json
{"slides": [{"slide_id": 1, "text": "Let us start with vectors in R n ..."}]}
```

The script must contain exactly the slide ids it was asked for; otherwise it is retried.
