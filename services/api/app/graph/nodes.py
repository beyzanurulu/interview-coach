"""Mülakat graph'ının düğümleri.

Akış: planner → ask → await_answer → interviewer → (follow_up | ask | wrap_up)
follow_up ve ask tekrar await_answer'a döner. Süre/sonlandırma her cevaptan sonra kontrol edilir.
"""

from collections.abc import Callable
from typing import Literal

import structlog
from langchain_core.messages import AIMessage, AnyMessage, HumanMessage
from langgraph.types import interrupt
from pydantic import BaseModel, Field

from app.core.config import Settings
from app.graph import prompts
from app.graph.messages import CLOSING, GREETING
from app.graph.state import InterviewState, PlanItem
from app.guardrails.sanitize import detect_injection, sanitize_untrusted
from app.providers.llm.base import LLMError, LLMProvider, complete_json

log = structlog.get_logger()

MAX_UTTERANCE_CHARS = 500
# Bu kadar süre kalmışsa yeni soruya/takibe geçilmez, kapanış yapılır.
MIN_REMAINING_S = 30


class PlannedQuestion(BaseModel):
    topic: str = Field(min_length=1, max_length=80)
    question: str = Field(min_length=5, max_length=400)
    kind: Literal["technical", "behavioral"] = "technical"


class PlanOut(BaseModel):
    questions: list[PlannedQuestion] = Field(min_length=2, max_length=12)


class DecisionOut(BaseModel):
    decision: Literal["follow_up", "next"]
    reason: str = ""
    transition: str = ""
    follow_up_question: str = ""
    covered: list[int] = Field(default_factory=list)


def question_count(max_duration_s: int) -> int:
    return max(3, max_duration_s // 60 // 2)


def clean_utterance(text: str) -> str:
    return sanitize_untrusted(text, MAX_UTTERANCE_CHARS)


def next_unasked(plan: list[PlanItem], after: int) -> int | None:
    for i in range(after + 1, len(plan)):
        if not plan[i]["asked"]:
            return i
    return None


def current_thread(turns: list[AnyMessage]) -> list[tuple[str, str]]:
    """Son ana sorudan bu yana konuşma (ana soru mesajı `question_start` ile işaretli)."""
    start = 0
    for i in range(len(turns) - 1, -1, -1):
        if turns[i].additional_kwargs.get("question_start"):
            start = i
            break
    return [
        ("aday" if isinstance(m, HumanMessage) else "mülakatçı", str(m.content))
        for m in turns[start:]
    ]


def make_nodes(llm: LLMProvider, settings: Settings, clock: Callable[[], float]) -> dict:
    def remaining_s(state: InterviewState) -> float:
        return state["started_at"] + state["max_duration_s"] - clock()

    async def planner(state: InterviewState) -> dict:
        count = question_count(state["max_duration_s"])
        out = await complete_json(
            llm,
            [
                {
                    "role": "system",
                    "content": prompts.planner_system(
                        state["language"], state["interview_type"], count
                    ),
                },
                {
                    "role": "user",
                    "content": prompts.planner_user(state["job_summary"], state.get("cv_summary")),
                },
            ],
            PlanOut,
            purpose="plan",
            temperature=0.5,
            max_tokens=700,
        )
        plan: list[PlanItem] = [
            {
                "topic": q.topic,
                "question": clean_utterance(q.question),
                "kind": q.kind,
                "asked": False,
                "depth": 0,
            }
            for q in out.questions[:count]
        ]
        return {
            "plan": plan,
            "current_index": -1,
            "follow_up_count": 0,
            "status": "running",
            "end_reason": None,
            "decision": None,
            "transition": "",
            "follow_up_question": "",
        }

    def ask(state: InterviewState) -> dict:
        index = next_unasked(state["plan"], state["current_index"])
        assert index is not None, "ask düğümüne soru kalmadan gelindi"
        plan = [dict(item) for item in state["plan"]]
        plan[index]["asked"] = True
        question = plan[index]["question"]
        if index == 0 and state["current_index"] == -1:
            greeting = GREETING[state["language"]].format(
                role=state["job_summary"].get("role", ""),
                minutes=state["max_duration_s"] // 60,
            )
            text = f"{greeting} {question}"
        else:
            text = f"{state.get('transition', '')} {question}".strip()
        return {
            "plan": plan,
            "current_index": index,
            "follow_up_count": 0,
            "transition": "",
            "turns": [
                AIMessage(
                    content=text,
                    additional_kwargs={"kind": "question", "question_start": True, "index": index},
                )
            ],
        }

    def await_answer(state: InterviewState) -> dict:
        event = interrupt({"type": "await_answer", "index": state["current_index"]})
        if event.get("type") == "end":
            return {"status": "wrapping_up", "end_reason": "user_ended"}
        if event.get("type") == "timeout":
            return {"status": "wrapping_up", "end_reason": "timeout"}
        text = sanitize_untrusted(str(event.get("text", "")), settings.max_answer_chars)
        if flags := detect_injection(text):
            log.warning("injection_suspected", source="answer", patterns=flags)
        return {"turns": [HumanMessage(content=text)]}

    async def interviewer(state: InterviewState) -> dict:
        if state["status"] == "wrapping_up":
            return {"decision": "wrap_up"}
        if remaining_s(state) <= MIN_REMAINING_S:
            return {"decision": "wrap_up", "status": "wrapping_up", "end_reason": "timeout"}

        plan, index = state["plan"], state["current_index"]
        can_follow_up = state["follow_up_count"] < settings.max_follow_ups
        upcoming = [(i, p["question"]) for i, p in enumerate(plan) if i > index and not p["asked"]]
        try:
            out = await complete_json(
                llm,
                [
                    {"role": "system", "content": prompts.interviewer_system(state["language"])},
                    {
                        "role": "user",
                        "content": prompts.interviewer_user(
                            job_summary=state["job_summary"],
                            question=plan[index],
                            thread=current_thread(state["turns"]),
                            can_follow_up=can_follow_up,
                            upcoming=upcoming,
                        ),
                    },
                ],
                DecisionOut,
                purpose="interviewer",
                max_tokens=250,
            )
        except LLMError:
            # Model cevap veremezse mülakat durmasın: sıradaki plan sorusuna geç.
            out = DecisionOut(decision="next")

        follow_up_question = clean_utterance(out.follow_up_question)
        if out.decision == "follow_up" and can_follow_up and follow_up_question:
            return {"decision": "follow_up", "follow_up_question": follow_up_question}

        upcoming_ids = {i for i, _ in upcoming}
        covered = {i for i in out.covered if i in upcoming_ids}
        new_plan = [{**p, "asked": True} if i in covered else dict(p) for i, p in enumerate(plan)]
        if next_unasked(new_plan, index) is None:
            return {
                "plan": new_plan,
                "decision": "wrap_up",
                "status": "wrapping_up",
                "end_reason": "completed",
            }
        return {
            "plan": new_plan,
            "decision": "next",
            "transition": clean_utterance(out.transition),
        }

    def follow_up(state: InterviewState) -> dict:
        plan = [dict(item) for item in state["plan"]]
        plan[state["current_index"]]["depth"] += 1
        return {
            "plan": plan,
            "follow_up_count": state["follow_up_count"] + 1,
            "follow_up_question": "",
            "turns": [
                AIMessage(
                    content=state["follow_up_question"], additional_kwargs={"kind": "follow_up"}
                )
            ],
        }

    def wrap_up(state: InterviewState) -> dict:
        reason = state.get("end_reason") or "completed"
        return {
            "status": "done",
            "end_reason": reason,
            "turns": [
                AIMessage(
                    content=CLOSING[reason][state["language"]],
                    additional_kwargs={"kind": "closing"},
                )
            ],
        }

    return {
        "planner": planner,
        "ask": ask,
        "await_answer": await_answer,
        "interviewer": interviewer,
        "follow_up": follow_up,
        "wrap_up": wrap_up,
    }
