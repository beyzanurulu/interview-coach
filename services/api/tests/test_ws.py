import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from app.core.config import Settings
from app.main import create_app
from app.ws import RateLimiter
from tests.fakes import JOB_SUMMARY, JOB_TEXT, FakeLLM, decision, make_plan, minimal_pdf


def make_client(llm: FakeLLM, clock=None) -> TestClient:
    settings = Settings(_env_file=None, cors_origins=["http://localhost:3000"])
    kwargs = {"clock": clock} if clock else {}
    return TestClient(create_app(settings=settings, llm=llm, **kwargs))


def start_msg(**kw) -> dict:
    return {
        "type": "start",
        "job_text": JOB_TEXT,
        "interview_type": "mixed",
        "language": "tr",
        "duration_min": 5,
        **kw,
    }


def test_full_text_interview_over_websocket() -> None:
    llm = FakeLLM(
        {
            "job_parse": JOB_SUMMARY,
            "plan": make_plan(3),
            "interviewer": [
                decision("follow_up"),
                decision("next"),
                decision("next"),
                decision("next"),
            ],
        }
    )
    with make_client(llm) as client, client.websocket_connect("/ws/interview") as ws:
        ws.send_json(start_msg())
        assert ws.receive_json() == {"type": "status", "status": "preparing"}
        ready = ws.receive_json()
        assert ready["type"] == "ready" and ready["total_questions"] == 3
        first = ws.receive_json()
        assert first["type"] == "interviewer" and first["question_index"] == 0

        ws.send_json({"type": "answer", "text": "kısa cevap"})
        follow = ws.receive_json()
        assert follow["kind"] == "follow_up" and follow["question_index"] is None
        for expected_index in (1, 2):
            ws.send_json({"type": "answer", "text": "detaylı cevap"})
            assert ws.receive_json()["question_index"] == expected_index
        ws.send_json({"type": "answer", "text": "son cevap"})
        closing = ws.receive_json()
        assert closing["kind"] == "closing" and closing["text"].startswith("Sorularım bu kadardı")
        assert ws.receive_json() == {"type": "ended", "reason": "completed"}


def test_user_can_end_over_websocket() -> None:
    llm = FakeLLM({"job_parse": JOB_SUMMARY, "plan": make_plan(3)})
    with make_client(llm) as client, client.websocket_connect("/ws/interview") as ws:
        ws.send_json(start_msg())
        for _ in range(3):
            ws.receive_json()
        ws.send_json({"type": "end"})
        assert ws.receive_json()["text"].startswith("Peki")
        assert ws.receive_json() == {"type": "ended", "reason": "user_ended"}


def test_server_enforces_time_limit_without_answer() -> None:
    class JumpingClock:
        """Mülakat başladıktan sonraki ilk okumada süreyi bitmiş gösterir."""

        def __init__(self) -> None:
            self.reads = 0

        def __call__(self) -> float:
            self.reads += 1
            return 0.0 if self.reads <= 2 else 10_000.0

    llm = FakeLLM({"job_parse": JOB_SUMMARY, "plan": make_plan(3)})
    with (
        make_client(llm, clock=JumpingClock()) as client,
        client.websocket_connect("/ws/interview") as ws,
    ):
        ws.send_json(start_msg())
        messages = [ws.receive_json() for _ in range(5)]
        assert messages[3]["text"].startswith("Süremiz doldu")
        assert messages[4] == {"type": "ended", "reason": "timeout"}


def test_rejects_invalid_duration() -> None:
    with make_client(FakeLLM({})) as client, client.websocket_connect("/ws/interview") as ws:
        ws.send_json(start_msg(duration_min=60))
        assert ws.receive_json()["code"] == "invalid_duration"


def test_rejects_answer_before_start() -> None:
    with make_client(FakeLLM({})) as client, client.websocket_connect("/ws/interview") as ws:
        ws.send_json({"type": "answer", "text": "merhaba"})
        assert ws.receive_json()["code"] == "not_started"


def test_reports_llm_unavailable() -> None:
    with make_client(FakeLLM({})) as client, client.websocket_connect("/ws/interview") as ws:
        ws.send_json(start_msg())
        ws.receive_json()  # preparing
        assert ws.receive_json()["code"] == "llm_unavailable"


def test_rejects_foreign_origin() -> None:
    headers = {"origin": "https://evil.example"}
    with (
        make_client(FakeLLM({})) as client,
        pytest.raises(WebSocketDisconnect),
        client.websocket_connect("/ws/interview", headers=headers) as ws,
    ):
        ws.receive_json()


def test_cv_upload_returns_summary() -> None:
    llm = FakeLLM({"cv_parse": {"skills": ["Python"]}})
    with make_client(llm) as client:
        resp = client.post(
            "/api/cv", files={"file": ("cv.pdf", minimal_pdf("Python"), "application/pdf")}
        )
    assert resp.status_code == 200 and resp.json()["skills"] == ["Python"]


def test_cv_upload_rejects_non_pdf() -> None:
    with make_client(FakeLLM({})) as client:
        resp = client.post("/api/cv", files={"file": ("cv.txt", b"metin", "text/plain")})
    assert resp.status_code == 415


def test_rate_limiter_sliding_window() -> None:
    limiter = RateLimiter(limit=2, window_s=10)
    assert limiter.allow(0) and limiter.allow(1)
    assert not limiter.allow(2)
    assert limiter.allow(11.5)
