import httpx
import pytest

from app.providers.llm.base import LLMError
from app.providers.llm.openai_compat import OpenAICompatibleProvider

OK = {"choices": [{"message": {"content": "<think>x</think>Merhaba"}}], "usage": {}}


def provider(handler, **kw) -> OpenAICompatibleProvider:
    p = OpenAICompatibleProvider(name="t", base_url="https://llm.test", model="m", **kw)
    p._client = httpx.AsyncClient(
        base_url="https://llm.test", transport=httpx.MockTransport(handler)
    )
    return p


async def test_returns_cleaned_content_and_sends_json_mode() -> None:
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["body"] = request.read()
        return httpx.Response(200, json=OK)

    out = await provider(handler).complete([], purpose="t", json_mode=True)
    assert out == "Merhaba" and b'"json_object"' in seen["body"]


async def test_retries_after_rate_limit(monkeypatch: pytest.MonkeyPatch) -> None:
    sleeps: list[float] = []

    async def fake_sleep(s: float) -> None:
        sleeps.append(s)

    monkeypatch.setattr("app.providers.llm.openai_compat.asyncio.sleep", fake_sleep)
    responses = iter(
        [httpx.Response(429, headers={"retry-after": "2"}), httpx.Response(200, json=OK)]
    )
    out = await provider(lambda r: next(responses)).complete([], purpose="t")
    assert out == "Merhaba" and sleeps == [2.0]


async def test_gives_up_when_retry_wait_too_long() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(429, headers={"retry-after": "60"})

    with pytest.raises(LLMError):
        await provider(handler, max_retry_wait_s=10).complete([], purpose="t")
