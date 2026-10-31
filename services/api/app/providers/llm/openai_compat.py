import asyncio
import time

import httpx
import structlog

from app.providers.llm.base import LLMError, Message, clean_text

log = structlog.get_logger()

DEFAULT_MAX_TOKENS = 512


class OpenAICompatibleProvider:
    """OpenAI uyumlu /chat/completions uç noktası (Groq, Ollama)."""

    def __init__(
        self,
        *,
        name: str,
        base_url: str,
        model: str,
        api_key: str = "",
        timeout_s: float = 30.0,
        max_retry_wait_s: float = 10.0,
        extra_body: dict | None = None,
    ) -> None:
        self.name = name
        self.model = model
        self._max_retry_wait_s = max_retry_wait_s
        self._extra_body = extra_body or {}
        headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}
        self._client = httpx.AsyncClient(base_url=base_url, headers=headers, timeout=timeout_s)

    async def complete(
        self,
        messages: list[Message],
        *,
        purpose: str,
        json_mode: bool = False,
        temperature: float = 0.3,
        max_tokens: int | None = None,
    ) -> str:
        body: dict = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            **self._extra_body,
        }
        if json_mode:
            body["response_format"] = {"type": "json_object"}
        # Groq beklenen çıktıyı max_tokens'a göre tahmin edip dakikalık kotadan düşer;
        # verilmezse küçük kotalı modellerde istek doğrudan reddedilir.
        body["max_tokens"] = max_tokens or DEFAULT_MAX_TOKENS

        start = time.perf_counter()
        try:
            resp = await self._post_with_retry(body)
            resp.raise_for_status()
            data = resp.json()
            content = data["choices"][0]["message"]["content"] or ""
        except (httpx.HTTPError, KeyError, IndexError, ValueError) as exc:
            detail = exc.response.text[:300] if isinstance(exc, httpx.HTTPStatusError) else ""
            log.warning(
                "llm_error", provider=self.name, purpose=purpose, error=repr(exc), detail=detail
            )
            raise LLMError(f"{self.name}: istek başarısız") from exc

        usage = data.get("usage") or {}
        # Loglara metin yazılmaz; sadece metrikler.
        log.info(
            "llm_call",
            provider=self.name,
            purpose=purpose,
            latency_ms=round((time.perf_counter() - start) * 1000),
            prompt_tokens=usage.get("prompt_tokens"),
            completion_tokens=usage.get("completion_tokens"),
        )
        return clean_text(content)

    async def _post_with_retry(self, body: dict, attempts: int = 3) -> httpx.Response:
        """Kota (429) hatasında sağlayıcının önerdiği süre kadar bekleyip tekrar dener."""
        for attempt in range(attempts):
            resp = await self._client.post("/chat/completions", json=body)
            if resp.status_code != 429 or attempt == attempts - 1:
                return resp
            wait = _retry_after_s(resp)
            if wait is None or wait > self._max_retry_wait_s:
                return resp
            log.info("llm_rate_limited", provider=self.name, wait_s=wait)
            await asyncio.sleep(wait)
        return resp

    async def aclose(self) -> None:
        await self._client.aclose()


def _retry_after_s(resp: httpx.Response) -> float | None:
    try:
        return float(resp.headers.get("retry-after", ""))
    except ValueError:
        return None
