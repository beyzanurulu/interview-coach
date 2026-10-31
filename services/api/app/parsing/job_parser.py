from typing import Literal

import structlog
from pydantic import BaseModel, Field

from app.guardrails.sanitize import DATA_RULE, detect_injection, sanitize_untrusted, wrap_as_data
from app.providers.llm.base import LLMProvider, complete_json

log = structlog.get_logger()


class JobSummary(BaseModel):
    role: str = Field(min_length=1, max_length=120)
    level: Literal["intern", "junior", "mid", "senior", "unknown"] = "unknown"
    skills: list[str] = Field(default_factory=list, max_length=25)
    nice_to_have: list[str] = Field(default_factory=list, max_length=15)
    responsibilities: list[str] = Field(default_factory=list, max_length=10)


SYSTEM_PROMPT = f"""Bir iş ilanı analiz asistanısın. İlandan şu alanlarla JSON çıkar:
- role: pozisyon adı (kısa)
- level: "intern" | "junior" | "mid" | "senior" | "unknown" (deneyim yılı ve unvana göre)
- skills: zorunlu teknik ve davranışsal beceriler (kısa ifadeler)
- nice_to_have: artı olarak belirtilen beceriler
- responsibilities: en fazla 6 ana sorumluluk

İlan dilini koru. Sadece JSON döndür.
{DATA_RULE}"""


class JobParseError(ValueError):
    """İlan metni kullanılamaz (boş veya çok kısa)."""


async def parse_job(llm: LLMProvider, text: str, *, max_chars: int) -> JobSummary:
    clean = sanitize_untrusted(text, max_chars)
    if len(clean) < 40:
        raise JobParseError("İlan metni çok kısa.")
    if flags := detect_injection(clean):
        log.warning("injection_suspected", source="job", patterns=flags)
    return await complete_json(
        llm,
        [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": wrap_as_data(clean, "ilan")},
        ],
        JobSummary,
        purpose="job_parse",
        max_tokens=400,
    )
