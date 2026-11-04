import httpx
import pytest

from course2video.config import LLMConfig
from course2video.llm import get_backend
from course2video.llm.base import LLMError
from course2video.llm.openai_compat_backend import OpenAICompatBackend
from course2video.slides.models import SlideBatch
from course2video.slides.validate import generate_validated


@pytest.fixture(autouse=True)
def no_models_endpoint(monkeypatch):
    def unreachable(*a, **k):
        raise httpx.ConnectError("offline test")

    monkeypatch.setattr(httpx, "get", unreachable)


class FakePost:
    def __init__(self, *responses):
        self.responses = list(responses)
        self.requests = []

    def __call__(self, url, json, headers, timeout):
        self.requests.append({"url": url, "json": json, "headers": headers})
        status, body = self.responses.pop(0)
        return httpx.Response(status, json=body, request=httpx.Request("POST", url))


def _ok(content, finish="stop"):
    return 200, {"choices": [{"message": {"content": content}, "finish_reason": finish}]}


def test_request_shape_for_gpt_oss(monkeypatch):
    fake = FakePost(_ok('{"slides": [{"id": 1, "title": "T", "bullets": ["b"]}]}'))
    monkeypatch.setattr(httpx, "post", fake)
    llm = get_backend(LLMConfig(backend="openai_compat", model="openai/gpt-oss-120b",
                                base_url="http://gpu:8000/v1/", effort="high"))
    batch, _ = generate_validated(llm, system="sys", prompt="p", model_cls=SlideBatch,
                                  task="slides", max_retries=0)
    assert batch.slides[0].title == "T"
    req = fake.requests[0]
    assert req["url"] == "http://gpu:8000/v1/chat/completions"
    body = req["json"]
    assert body["model"] == "openai/gpt-oss-120b"
    assert body["messages"][0] == {"role": "system", "content": "sys"}
    assert body["reasoning_effort"] == "high"
    fmt = body["response_format"]
    assert fmt["type"] == "json_schema" and fmt["json_schema"]["name"] == "slides"
    assert "maxItems" not in str(fmt)


def test_structured_output_can_be_disabled(monkeypatch):
    fake = FakePost(_ok("{}"))
    monkeypatch.setattr(httpx, "post", fake)
    llm = OpenAICompatBackend(model="m", structured_output=False)
    llm.complete("s", "p", schema={"type": "object"})
    assert "response_format" not in fake.requests[0]["json"]


@pytest.mark.parametrize(
    "response, message",
    [
        ((500, {"error": "boom"}), "HTTP 500"),
        (_ok("{}", finish="length"), "truncated"),
        (_ok(""), "empty"),
        ((200, {"unexpected": True}), "unexpected response"),
    ],
)
def test_errors_become_llm_errors(monkeypatch, response, message):
    monkeypatch.setattr(httpx, "post", FakePost(response))
    with pytest.raises(LLMError, match=message):
        OpenAICompatBackend(model="m").complete("s", "p")


def test_unreachable_server(monkeypatch):
    def refuse(*a, **k):
        raise httpx.ConnectError("refused")

    monkeypatch.setattr(httpx, "post", refuse)
    with pytest.raises(LLMError, match="cannot reach"):
        OpenAICompatBackend(model="m", base_url="http://nowhere:1/v1").complete("s", "p")


def test_context_length_from_models_endpoint(monkeypatch):
    def fake_get(url, headers, timeout):
        assert url.endswith("/v1/models")
        return httpx.Response(200, json={"data": [{"id": "other", "max_model_len": 1},
                                                  {"id": "m", "max_model_len": 8192}]},
                              request=httpx.Request("GET", url))

    monkeypatch.setattr(httpx, "get", fake_get)
    assert OpenAICompatBackend(model="m", base_url="http://gpu/v1").context_length() == 8192


def test_max_tokens_fits_the_context(monkeypatch):
    fake = FakePost(_ok("{}"))
    monkeypatch.setattr(httpx, "post", fake)
    llm = OpenAICompatBackend(model="m", max_tokens=16000, context_tokens=8192)
    llm.complete("s", "p" * 3000)
    sent = fake.requests[0]["json"]["max_tokens"]
    assert sent < 8192 - 1000 and sent > 512


def test_prompt_too_long_for_context_is_a_clear_error(monkeypatch):
    monkeypatch.setattr(httpx, "post", FakePost(_ok("{}")))
    llm = OpenAICompatBackend(model="m", context_tokens=2048)
    with pytest.raises(LLMError, match="does not fit the model's context"):
        llm.complete("s", "x" * 20000)


def test_unknown_context_keeps_configured_max_tokens(monkeypatch):
    def fail_get(*a, **k):
        raise httpx.ConnectError("no models endpoint")

    fake = FakePost(_ok("{}"))
    monkeypatch.setattr(httpx, "get", fail_get)
    monkeypatch.setattr(httpx, "post", fake)
    OpenAICompatBackend(model="m", max_tokens=16000).complete("s", "p")
    assert fake.requests[0]["json"]["max_tokens"] == 16000


def test_fit_to_context_shrinks_settings_for_8k():
    from course2video.config import Config, fit_to_context

    cfg = Config()
    changes = fit_to_context(cfg, 8192)
    assert cfg.slides.max_slides_per_chunk <= 8
    assert cfg.script.slides_per_call <= 8
    assert changes
    big = Config()
    assert fit_to_context(big, 131072) == []


def test_theory_slides_never_keep_a_model_written_source_doc():
    from course2video.config import SlidesConfig
    from course2video.llm.mock_backend import MockBackend
    from course2video.slides.generate import generate_deck

    junk = {"slides": [{"id": 1, "title": "T", "bullets": ["b"], "source_doc": "<document> ...",
                        "talking_points": ["one", "two"]}]}
    deck, _ = generate_deck(MockBackend(responses=[junk]), "# C\n\n## A\ntext", SlidesConfig(), title="C")
    assert deck.slides[0].source_doc == ""
