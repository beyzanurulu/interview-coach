import io

import structlog
from pydantic import BaseModel, Field
from pypdf import PdfReader
from pypdf.errors import PdfReadError

from app.guardrails.sanitize import DATA_RULE, detect_injection, sanitize_untrusted, wrap_as_data
from app.providers.llm.base import LLMProvider, complete_json

log = structlog.get_logger()

MAX_PAGES = 5


class CVProject(BaseModel):
    name: str = Field(max_length=120)
    description: str = Field(default="", max_length=400)
    technologies: list[str] = Field(default_factory=list, max_length=15)


class CVSummary(BaseModel):
    skills: list[str] = Field(default_factory=list, max_length=30)
    projects: list[CVProject] = Field(default_factory=list, max_length=8)
    experience: list[str] = Field(default_factory=list, max_length=8)
    education: list[str] = Field(default_factory=list, max_length=4)


class CVParseError(ValueError):
    """PDF okunamadı veya içinde metin yok."""


SYSTEM_PROMPT = f"""Bir CV analiz asistanısın. CV metninden şu alanlarla JSON çıkar:
- skills: teknik beceriler ve araçlar
- projects: [{{name, description (1-2 cümle), technologies}}]
- experience: "Rol, Şirket, süre" biçiminde kısa satırlar
- education: kısa satırlar

Kişisel iletişim bilgilerini (telefon, e-posta, adres) ALMA. CV dilini koru. Sadece JSON döndür.
{DATA_RULE}"""


def extract_pdf_text(data: bytes) -> str:
    try:
        reader = PdfReader(io.BytesIO(data))
        pages = reader.pages[:MAX_PAGES]
        text = "\n".join(page.extract_text() or "" for page in pages)
    except (PdfReadError, ValueError, OSError) as exc:
        raise CVParseError("PDF okunamadı.") from exc
    if not text.strip():
        raise CVParseError("PDF'te metin bulunamadı (taranmış görüntü olabilir).")
    return text


async def parse_cv(llm: LLMProvider, text: str, *, max_chars: int) -> CVSummary:
    clean = sanitize_untrusted(text, max_chars)
    if flags := detect_injection(clean):
        log.warning("injection_suspected", source="cv", patterns=flags)
    return await complete_json(
        llm,
        [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": wrap_as_data(clean, "cv")},
        ],
        CVSummary,
        purpose="cv_parse",
        max_tokens=700,
    )
