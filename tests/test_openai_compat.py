import httpx
import pytest

from course2video.config import LLMConfig
from course2video.llm import get_backend
from course2video.llm.base import LLMError
from course2video.llm.openai_compat_backend import OpenAICompatBackend
from course2video.slides.models import SlideBatch
from course2video.slides.validate import generate_validated


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
