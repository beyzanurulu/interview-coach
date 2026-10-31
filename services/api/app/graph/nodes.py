"""Mülakat graph'ının düğümleri.

Akış: planner → ask → await_answer → interviewer → (follow_up | ask | redirect |
candidate_questions | answer_candidate | wrap_up). Soru sorup cevap bekleyen düğümler
await_answer'a döner.

İlke: akışı kod yönetir. Model mesajı sınıflandırır ve kısa metinler üretir; bu metinler kod ile
denetlenir, geçemezse sabit şablonlara düşülür (ADR-003, ADR-004).
"""

import re
from collections.abc import Callable
from typing import Literal

import structlog
from langchain_core.messages import AIMessage, AnyMessage, HumanMessage
from langgraph.types import interrupt
from pydantic import BaseModel, Field

from app.core.config import Settings
from app.graph import prompts
from app.graph.messages import (
    CANDIDATE_ANOTHER,
    CANDIDATE_ERROR_REPLY,
    CANDIDATE_FALLBACK_ANSWER,
    CANDIDATE_INVITE,
    CLOSING,
    FALLBACK_WARMUP,
    GREETING,
    REDIRECTS,
    REPEAT_QUESTION,
)
from app.graph.state import AnswerType, InterviewState, Language, PlanItem, Stage
from app.guardrails.intent import quick_intent
from app.guardrails.output import (
    candidate_answer_issues,
    mentions_cv,
    question_issues,
    transition_issues,
)
from app.guardrails.sanitize import detect_injection, sanitize_untrusted
from app.providers.llm.base import LLMError, LLMProvider, Message, complete_json

log = structlog.get_logger()

MAX_UTTERANCE_CHARS = 500
# Bu kadar süre kalmışsa yeni soru sorulmaz, kapanış yapılır.
MIN_REMAINING_S = 30
# Adayın sorularına ayrılan süre; bu kadar kalınca plan soruları bırakılır.
CANDIDATE_STAGE_RESERVE_S = 90
MAX_CANDIDATE_QUESTIONS = 2
# Denetimi geçemeyen çıktı için modelin toplam deneme sayısı.
LLM_ATTEMPTS = 2

STAGE_ORDER: dict[Stage, int] = {"warmup": 0, "experience": 1, "technical": 2, "behavioral": 2}


class PlannedQuestion(BaseModel):
    topic: str = Field(min_length=1, max_length=80)
    question: str = Field(min_length=5, max_length=400)
    stage: Stage = "technical"


class PlanOut(BaseModel):
    questions: list[PlannedQuestion] = Field(min_length=1, max_length=12)


class DecisionOut(BaseModel):
    answer_type: AnswerType = "answer"
    decision: Literal["follow_up", "next"] | None = None
    reason: str = ""
    transition: str = ""
    follow_up_question: str = ""
    clarified_question: str = ""
    covered: list[int] = Field(default_factory=list)


class CandidateQAOut(BaseModel):
    type: Literal["has_question", "no_question", "other"]
    answer: str = ""


def question_count(max_duration_s: int) -> int:
    return max(3, max_duration_s // 60 // 2)


def clean_utterance(text: str) -> str:
    return sanitize_untrusted(text, MAX_UTTERANCE_CHARS)


def _dedupe_key(text: str) -> str:
    return re.sub(r"\W+", "", text.lower())


def build_plan(
    questions: list[PlannedQuestion], language: Language, count: int, *, has_cv: bool = False
) -> list[PlanItem]:
    """Model çıktısından plan: denetimi geçemeyen ve tekrar eden sorular atılır, aşama sırası
    (ısınma → deneyim → diğerleri) kodla uygulanır, ısınma sorusu yoksa şablon eklenir.
    CV yüklenmediyse CV'den bahseden sorular atılır."""
    seen: set[str] = set()
    items: list[PlanItem] = []
    for q in questions:
        text = clean_utterance(q.question)
        key = _dedupe_key(text)
        if key in seen or question_issues(text, language):
            continue
        if not has_cv and mentions_cv(text):
            continue
        if q.stage == "warmup" and any(i["stage"] == "warmup" for i in items):
            continue
        seen.add(key)
        items.append(
            {"topic": q.topic, "question": text, "stage": q.stage, "asked": False, "depth": 0}
        )
    items.sort(key=lambda item: STAGE_ORDER[item["stage"]])
    if not items or items[0]["stage"] != "warmup":
        items.insert(
            0,
            {
                "topic": "tanışma",
                "question": FALLBACK_WARMUP[language],
                "stage": "warmup",
                "asked": False,
                "depth": 0,
            },
        )
    return items[:count]


def next_unasked(plan: list[PlanItem], after: int) -> int | None:
    for i in range(after + 1, len(plan)):
        if not plan[i]["asked"]:
            return i
    return None


def current_thread(turns: list[AnyMessage]) -> list[tuple[str, str]]:
    """Son ana sorudan (veya aday soruları davetinden) bu yana konuşma."""
    start = 0
    for i in range(len(turns) - 1, -1, -1):
        if turns[i].additional_kwargs.get("question_start"):
            start = i
            break
    return [
        ("aday" if isinstance(m, HumanMessage) else "mülakatçı", str(m.content))
        for m in turns[start:]
    ]


def decision_issues(out: DecisionOut, language: Language) -> list[str]:
    if out.answer_type == "clarification":
        return [
            f"clarified_question {i}" for i in question_issues(out.clarified_question, language)
        ]
    if out.answer_type == "answer" and out.decision == "follow_up":
        return [
            f"follow_up_question {i}" for i in question_issues(out.follow_up_question, language)
        ]
    if out.answer_type in ("answer", "dont_know"):
        return [f"transition {i}" for i in transition_issues(out.transition, language)]
    return []


async def complete_validated[T: BaseModel](
    llm: LLMProvider,
    messages: list[Message],
    schema: type[T],
    validate: Callable[[T], list[str]],
    *,
    purpose: str,
    max_tokens: int,
) -> tuple[T | None, list[str]]:
    """Şemaya uyan ve denetimi geçen çıktıyı ister; geçemezse sorunları gösterip tekrar dener.
    Dönüş: (son çıktı, kalan sorunlar). Model hiç yanıt veremezse (None, ["llm_error"])."""
    attempt_messages = list(messages)
    out: T | None = None
    issues = ["llm_error"]
    for attempt in range(LLM_ATTEMPTS):
        try:
            out = await complete_json(
                llm, attempt_messages, schema, purpose=purpose, max_tokens=max_tokens
            )
        except LLMError:
            break
        issues = validate(out)
        if not issues:
            break
        log.info("llm_output_rejected", purpose=purpose, attempt=attempt, issues=issues)
        attempt_messages = [
            *messages,
            {"role": "assistant", "content": out.model_dump_json()},
            {
                "role": "user",
                "content": f"Çıktın kurallara uymuyor: {'; '.join(issues)}. "
                "Düzeltip sadece JSON döndür.",
            },
        ]
    return out, issues


def make_nodes(llm: LLMProvider, settings: Settings, clock: Callable[[], float]) -> dict:
    def remaining_s(state: InterviewState) -> float:
        return state["started_at"] + state["max_duration_s"] - clock()

    def repeat(state: InterviewState) -> str:
        return REPEAT_QUESTION[state["language"]].format(question=state["last_question"])

    async def planner(state: InterviewState) -> dict:
        count = question_count(state["max_duration_s"])
        messages: list[Message] = [
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
        ]
        plan: list[PlanItem] = []
        for _ in range(LLM_ATTEMPTS):
            out = await complete_json(
                llm, messages, PlanOut, purpose="plan", temperature=0.5, max_tokens=700
            )
            plan = build_plan(
                out.questions, state["language"], count, has_cv=bool(state.get("cv_summary"))
            )
            if len(plan) >= min(3, count):
                break
            log.info("plan_rejected", valid_questions=len(plan), requested=count)
        if len(plan) < 2:
            raise LLMError("plan: yeterli geçerli soru üretilemedi")
        return {
            "plan": plan,
            "current_index": -1,
            "follow_up_count": 0,
            "status": "running",
            "end_reason": None,
            "phase": "questions",
            "last_question": "",
            "redirect_counts": {},
            "candidate_q_count": 0,
            "decision": None,
            "transition": "",
            "follow_up_question": "",
            "reply": "",
        }

    def ask(state: InterviewState) -> dict:
        index = next_unasked(state["plan"], state["current_index"])
        assert index is not None, "ask düğümüne soru kalmadan gelindi"
        plan = [dict(item) for item in state["plan"]]
        plan[index]["asked"] = True
        question = plan[index]["question"]
        if state["current_index"] == -1:
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
            "last_question": question,
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

    def to_next_question(state: InterviewState, out: DecisionOut) -> dict:
        plan, index = state["plan"], state["current_index"]
        upcoming = {i for i, p in enumerate(plan) if i > index and not p["asked"]}
        covered = {i for i in out.covered if i in upcoming}
        new_plan = [{**p, "asked": True} if i in covered else dict(p) for i, p in enumerate(plan)]
        transition = clean_utterance(out.transition)
        if transition_issues(transition, state["language"]):
            transition = ""
        no_more = next_unasked(new_plan, index) is None
        if no_more or remaining_s(state) <= CANDIDATE_STAGE_RESERVE_S:
            return {"plan": new_plan, "decision": "candidate_questions", "transition": transition}
        return {"plan": new_plan, "decision": "next", "transition": transition}

    def redirect_reply(state: InterviewState, answer_type: AnswerType) -> dict:
        counts = dict(state.get("redirect_counts") or {})
        counts[answer_type] = counts.get(answer_type, 0) + 1
        first, repeated = REDIRECTS[answer_type][state["language"]]
        text = first if counts[answer_type] == 1 else repeated
        return {
            "decision": "redirect",
            "redirect_counts": counts,
            "reply": f"{text} {repeat(state)}",
        }

    async def interviewer(state: InterviewState) -> dict:
        if state["status"] == "wrapping_up":
            return {"decision": "wrap_up"}
        if remaining_s(state) <= MIN_REMAINING_S:
            return {"decision": "wrap_up", "status": "wrapping_up", "end_reason": "timeout"}
        if state["phase"] == "candidate_questions":
            return await candidate_turn(state)

        language = state["language"]
        plan, index = state["plan"], state["current_index"]
        can_follow_up = state["follow_up_count"] < settings.max_follow_ups
        upcoming = [(i, p["question"]) for i, p in enumerate(plan) if i > index and not p["asked"]]
        if intent := quick_intent(str(state["turns"][-1].content)):
            log.info("turn_classified", answer_type=intent, decision=None, source="rule")
            if intent == "dont_know":
                return to_next_question(state, DecisionOut(answer_type=intent))
            return redirect_reply(state, intent)
        out, issues = await complete_validated(
            llm,
            [
                {"role": "system", "content": prompts.interviewer_system(language)},
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
            lambda o: decision_issues(o, language),
            purpose="interviewer",
            max_tokens=300,
        )
        # Model yanıt veremezse mülakat durmasın: cevap kabul edilip sıradaki soruya geçilir.
        out = out or DecisionOut(answer_type="answer", decision="next")
        log.info("turn_classified", answer_type=out.answer_type, decision=out.decision)

        match out.answer_type:
            case "answer":
                follow_up_question = clean_utterance(out.follow_up_question)
                if (
                    out.decision == "follow_up"
                    and can_follow_up
                    and not question_issues(follow_up_question, language)
                ):
                    return {"decision": "follow_up", "follow_up_question": follow_up_question}
                return to_next_question(state, out)
            case "dont_know":
                return to_next_question(state, out)
            case "clarification":
                clarified = clean_utterance(out.clarified_question)
                if question_issues(clarified, language):
                    return {"decision": "redirect", "reply": repeat(state)}
                return {"decision": "redirect", "reply": clarified, "last_question": clarified}
            case _:
                return redirect_reply(state, out.answer_type)

    async def candidate_turn(state: InterviewState) -> dict:
        language = state["language"]
        out, issues = await complete_validated(
            llm,
            [
                {"role": "system", "content": prompts.candidate_qa_system(language)},
                {
                    "role": "user",
                    "content": prompts.candidate_qa_user(
                        state["job_summary"], current_thread(state["turns"])
                    ),
                },
            ],
            CandidateQAOut,
            lambda o: (
                candidate_answer_issues(clean_utterance(o.answer), language)
                if o.type == "has_question"
                else []
            ),
            purpose="candidate_qa",
            max_tokens=250,
        )
        log.info("candidate_turn_classified", type=out.type if out else None)
        if out is None:
            # Kapanıştan önce nötr bir cevap; aday sorusu cevapsız kalmış gibi görünmesin.
            return {
                "decision": "answer_candidate",
                "reply": CANDIDATE_ERROR_REPLY[language],
                "candidate_q_count": MAX_CANDIDATE_QUESTIONS - 1,
            }
        if out.type != "has_question":
            return {"decision": "wrap_up", "status": "wrapping_up", "end_reason": "completed"}
        answer = CANDIDATE_FALLBACK_ANSWER[language] if issues else clean_utterance(out.answer)
        return {"decision": "answer_candidate", "reply": answer}

    def follow_up(state: InterviewState) -> dict:
        plan = [dict(item) for item in state["plan"]]
        plan[state["current_index"]]["depth"] += 1
        question = state["follow_up_question"]
        return {
            "plan": plan,
            "follow_up_count": state["follow_up_count"] + 1,
            "follow_up_question": "",
            "last_question": question,
            "turns": [AIMessage(content=question, additional_kwargs={"kind": "follow_up"})],
        }

    def redirect(state: InterviewState) -> dict:
        return {
            "reply": "",
            "turns": [AIMessage(content=state["reply"], additional_kwargs={"kind": "redirect"})],
        }

    def candidate_questions(state: InterviewState) -> dict:
        invite = CANDIDATE_INVITE[state["language"]]
        text = f"{state.get('transition', '')} {invite}".strip()
        return {
            "phase": "candidate_questions",
            "transition": "",
            "last_question": invite,
            "turns": [
                AIMessage(
                    content=text,
                    additional_kwargs={"kind": "candidate_invite", "question_start": True},
                )
            ],
        }

    def answer_candidate(state: InterviewState) -> dict:
        count = state["candidate_q_count"] + 1
        last = count >= MAX_CANDIDATE_QUESTIONS
        text = (
            state["reply"] if last else f"{state['reply']} {CANDIDATE_ANOTHER[state['language']]}"
        )
        update: dict = {
            "candidate_q_count": count,
            "reply": "",
            "turns": [AIMessage(content=text, additional_kwargs={"kind": "candidate_answer"})],
        }
        if last:
            update |= {"decision": "wrap_up", "status": "wrapping_up", "end_reason": "completed"}
        return update

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
        "redirect": redirect,
        "candidate_questions": candidate_questions,
        "answer_candidate": answer_candidate,
        "wrap_up": wrap_up,
    }
