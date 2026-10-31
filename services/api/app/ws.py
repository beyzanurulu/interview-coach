"""Metin tabanlı mülakat WebSocket'i.

İstemci → sunucu:
  {"type": "start", "job_text", "cv_summary"?, "interview_type", "language", "duration_min"}
  {"type": "answer", "text"}
  {"type": "end"}
Sunucu → istemci:
  {"type": "status", "status": "preparing"}
  {"type": "ready", "total_questions", "duration_s"}
  {"type": "interviewer", "text", "kind", "question_index", "remaining_s"}
    kind: question | follow_up | redirect | candidate_invite | candidate_answer | closing
  {"type": "ended", "reason"}
  {"type": "error", "code", "message"}
"""

import asyncio
import time
import uuid
from collections import deque
from typing import Annotated, Literal

import structlog
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field, TypeAdapter, ValidationError

from app.interview.session import InterviewSession, Utterance
from app.parsing.cv_parser import CVSummary
from app.parsing.job_parser import JobParseError, parse_job
from app.providers.llm.base import LLMError

log = structlog.get_logger()
router = APIRouter()

MAX_MESSAGE_BYTES = 32_000
RATE_LIMIT_MESSAGES = 20
RATE_LIMIT_WINDOW_S = 60.0


class StartMsg(BaseModel):
    type: Literal["start"]
    job_text: str = Field(max_length=20_000)
    cv_summary: CVSummary | None = None
    interview_type: Literal["technical", "behavioral", "mixed"] = "mixed"
    language: Literal["tr", "en"] = "tr"
    duration_min: int


class AnswerMsg(BaseModel):
    type: Literal["answer"]
    text: str = Field(min_length=1, max_length=10_000)


class EndMsg(BaseModel):
    type: Literal["end"]


ClientMsg = TypeAdapter(Annotated[StartMsg | AnswerMsg | EndMsg, Field(discriminator="type")])


class RateLimiter:
    """Kayan pencere: pencere içinde en fazla `limit` mesaj."""

    def __init__(self, limit: int, window_s: float) -> None:
        self.limit, self.window_s = limit, window_s
        self._times: deque[float] = deque()

    def allow(self, now: float) -> bool:
        while self._times and now - self._times[0] > self.window_s:
            self._times.popleft()
        if len(self._times) >= self.limit:
            return False
        self._times.append(now)
        return True


class ClientError(Exception):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code, self.message = code, message


async def send_error(ws: WebSocket, code: str, message: str) -> None:
    await ws.send_json({"type": "error", "code": code, "message": message})


async def receive_msg(ws: WebSocket, timeout: float | None = None):
    raw = await asyncio.wait_for(ws.receive_text(), timeout=timeout)
    if len(raw.encode()) > MAX_MESSAGE_BYTES:
        raise ClientError("too_large", "Mesaj çok uzun.")
    try:
        return ClientMsg.validate_json(raw)
    except ValidationError as exc:
        raise ClientError("invalid_message", "Geçersiz mesaj.") from exc


async def send_utterances(ws: WebSocket, session: InterviewSession, items: list[Utterance]):
    remaining = max(0, round(await session.remaining_s()))
    for u in items:
        await ws.send_json(
            {
                "type": "interviewer",
                "text": u.text,
                "kind": u.kind,
                "question_index": u.question_index,
                "remaining_s": remaining,
            }
        )


@router.websocket("/ws/interview")
async def interview_ws(ws: WebSocket) -> None:
    app = ws.app
    settings, llm = app.state.settings, app.state.llm
    # CORS middleware WebSocket'e uygulanmaz; tarayıcıdan gelen Origin elle kontrol edilir.
    origin = ws.headers.get("origin")
    if origin and origin.rstrip("/") not in settings.cors_origins:
        await ws.close(code=1008)
        return
    await ws.accept()
    session: InterviewSession | None = None
    try:
        start = await receive_msg(ws, timeout=60)
        if not isinstance(start, StartMsg):
            raise ClientError("not_started", "Önce mülakatı başlatın.")
        if start.duration_min not in settings.interview_durations_min:
            raise ClientError("invalid_duration", "Geçersiz süre.")

        await ws.send_json({"type": "status", "status": "preparing"})
        job_summary = await parse_job(llm, start.job_text, max_chars=settings.max_job_chars)
        session = InterviewSession(
            app.state.graph, interview_id=str(uuid.uuid4()), clock=app.state.clock
        )
        structlog.contextvars.bind_contextvars(interview_id=session.interview_id)
        first = await session.start(
            job_summary=job_summary.model_dump(),
            cv_summary=start.cv_summary.model_dump() if start.cv_summary else None,
            interview_type=start.interview_type,
            language=start.language,
            duration_min=start.duration_min,
        )
        values = await session.values()
        log.info(
            "interview_started", questions=len(values["plan"]), duration_min=start.duration_min
        )
        await ws.send_json(
            {
                "type": "ready",
                "total_questions": len(values["plan"]),
                "duration_s": values["max_duration_s"],
            }
        )
        await send_utterances(ws, session, first)

        limiter = RateLimiter(RATE_LIMIT_MESSAGES, RATE_LIMIT_WINDOW_S)
        while await session.status() != "done":
            # Süre sınırını sunucu uygular: süre dolunca cevap beklenmeden kapanışa geçilir.
            remaining = await session.remaining_s()
            try:
                msg = await receive_msg(ws, timeout=max(remaining, 0.01))
            except TimeoutError:
                await send_utterances(ws, session, await session.end("timeout"))
                break
            except ClientError as exc:
                await send_error(ws, exc.code, exc.message)
                continue

            if isinstance(msg, EndMsg):
                await send_utterances(ws, session, await session.end("end"))
                break
            if isinstance(msg, StartMsg):
                await send_error(ws, "already_started", "Mülakat zaten başladı.")
                continue
            if not limiter.allow(time.monotonic()):
                await send_error(ws, "rate_limited", "Çok hızlı mesaj gönderiliyor.")
                continue
            await send_utterances(ws, session, await session.answer(msg.text))

        values = await session.values()
        log.info("interview_ended", reason=values.get("end_reason"), turns=len(values["turns"]))
        await ws.send_json({"type": "ended", "reason": values.get("end_reason")})
        await ws.close()
    except WebSocketDisconnect:
        log.info("interview_disconnected")
    except TimeoutError:
        await send_error(ws, "start_timeout", "Mülakat başlatılmadı.")
        await ws.close()
    except ClientError as exc:
        await send_error(ws, exc.code, exc.message)
        await ws.close()
    except JobParseError as exc:
        await send_error(ws, "job_invalid", str(exc))
        await ws.close()
    except LLMError:
        await send_error(ws, "llm_unavailable", "Yapay zeka servisine ulaşılamadı, tekrar deneyin.")
        await ws.close()
    finally:
        if session:
            await session.close()
        structlog.contextvars.unbind_contextvars("interview_id")
