from typing import Annotated, Literal, TypedDict

from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages

Language = Literal["tr", "en"]
InterviewType = Literal["technical", "behavioral", "mixed"]
Status = Literal["running", "wrapping_up", "done", "aborted"]
EndReason = Literal["completed", "timeout", "user_ended"]
Stage = Literal["warmup", "experience", "technical", "behavioral"]
Phase = Literal["questions", "candidate_questions"]
AnswerType = Literal[
    "answer",
    "clarification",
    "dont_know",
    "asks_for_answer",
    "off_topic",
    "ai_question",
    "inappropriate",
    "unclear",
]
Decision = Literal[
    "follow_up", "next", "redirect", "candidate_questions", "answer_candidate", "wrap_up"
]


class PlanItem(TypedDict):
    topic: str
    question: str
    stage: Stage
    asked: bool
    depth: int


class InterviewState(TypedDict, total=False):
    user_id: str
    interview_id: str
    language: Language
    interview_type: InterviewType
    job_summary: dict
    cv_summary: dict | None
    plan: list[PlanItem]
    turns: Annotated[list[AnyMessage], add_messages]
    current_index: int
    follow_up_count: int
    started_at: float  # epoch saniye
    max_duration_s: int
    status: Status
    end_reason: EndReason | None
    phase: Phase
    last_question: str  # tekrar sorulabilmesi için son sorulan soru (ana, takip veya açıklama)
    redirect_counts: dict[str, int]  # konu dışı vb. davranışların sayısı (uyarı tonu için)
    candidate_q_count: int
    # interviewer düğümünün son kararı (yönlendirme için)
    decision: Decision | None
    transition: str
    follow_up_question: str
    reply: str
