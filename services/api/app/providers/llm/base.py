import json
import re
from typing import Literal, Protocol, TypedDict

from pydantic import BaseModel, ValidationError


class Message(TypedDict):
    role: Literal["system", "user", "assistant"]
    content: str


class LLMError(Exception):
    """Sağlayıcı hatası veya kullanılamaz çıktı."""


class LLMProvider(Protocol):
    name: str

    async def complete(
        self,
        messages: list[Message],
        *,
        purpose: str,
        json_mode: bool = False,
        temperature: float = 0.3,
        max_tokens: int | None = None,
    ) -> str:
        """`purpose` loglama ve kota takibi içindir (ör. "plan", "interviewer")."""
        ...


_THINK_RE = re.compile(r"<think>.*?</think>", re.DOTALL)
_FENCE_RE = re.compile(r"^```(?:json)?\s*|\s*```$")


def clean_text(text: str) -> str:
    """Akıl yürütme bloklarını ve baştaki/sondaki boşlukları temizler."""
    return _THINK_RE.sub("", text).strip()


def extract_json(text: str) -> object:
    cleaned = _FENCE_RE.sub("", clean_text(text))
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        start, end = cleaned.find("{"), cleaned.rfind("}")
        if start == -1 or end <= start:
            raise
        return json.loads(cleaned[start : end + 1])


async def complete_json[T: BaseModel](
    llm: LLMProvider,
    messages: list[Message],
    schema: type[T],
    *,
    purpose: str,
    temperature: float = 0.2,
    max_tokens: int = 512,
    retries: int = 1,
) -> T:
    """JSON ister ve şemaya göre doğrular; hata olursa hatayı modele gösterip tekrar dener."""
    attempt_messages = list(messages)
    last_error: Exception | None = None
    for _ in range(retries + 1):
        raw = await llm.complete(
            attempt_messages,
            purpose=purpose,
            json_mode=True,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        try:
            return schema.model_validate(extract_json(raw))
        except (json.JSONDecodeError, ValidationError) as exc:
            last_error = exc
            attempt_messages = [
                *messages,
                {"role": "assistant", "content": raw},
                {
                    "role": "user",
                    "content": f"Çıktın geçerli değil: {exc}. Sadece şemaya uyan JSON döndür.",
                },
            ]
    raise LLMError(f"{purpose}: geçerli JSON alınamadı") from last_error
