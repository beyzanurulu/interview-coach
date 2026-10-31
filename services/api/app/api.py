from fastapi import APIRouter, HTTPException, Request, UploadFile

from app.parsing.cv_parser import CVParseError, CVSummary, extract_pdf_text, parse_cv
from app.providers.llm.base import LLMError

router = APIRouter(prefix="/api")


@router.post("/cv")
async def upload_cv(request: Request, file: UploadFile) -> CVSummary:
    """CV PDF'ini okuyup özet döner. Dosya saklanmaz."""
    settings = request.app.state.settings
    if file.content_type not in ("application/pdf", "application/octet-stream"):
        raise HTTPException(415, "Sadece PDF yükleyebilirsiniz.")
    data = await file.read(settings.max_cv_bytes + 1)
    if len(data) > settings.max_cv_bytes:
        raise HTTPException(413, "Dosya çok büyük (en fazla 2 MB).")
    try:
        text = extract_pdf_text(data)
        return await parse_cv(request.app.state.llm, text, max_chars=settings.max_cv_chars)
    except CVParseError as exc:
        raise HTTPException(422, str(exc)) from exc
    except LLMError as exc:
        raise HTTPException(503, "Yapay zeka servisine ulaşılamadı, tekrar deneyin.") from exc
