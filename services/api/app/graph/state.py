from typing import Annotated, Literal, TypedDict

from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages

Language = Literal["tr", "en"]
InterviewType = Literal["technical", "behavioral", "mixed"]
Status = Literal["running", "wrapping_up", "done", "aborted"]
EndReason = Literal["completed", "timeout", "user_ended"]
Decision = Literal["follow_up", "next", "wrap_up"]


class PlanItem(TypedDict):
    topic: str
    question: str
    kind: Literal["technical", "behavioral"]
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
    # interviewer düğümünün son kararı (yönlendirme için)
    decision: Decision | None
    transition: str
    follow_up_question: str
