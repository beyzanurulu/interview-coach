import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import Literal

from langchain_core.messages import AIMessage
from langgraph.types import Command

from app.graph.state import InterviewType, Language

UtteranceKind = Literal["question", "follow_up", "closing"]


@dataclass
class Utterance:
    text: str
    kind: UtteranceKind
    question_index: int | None  # ana soru ise plan sırası, takip/kapanış ise None


class InterviewSession:
    """Tek bir mülakatın graph thread'ini yönetir; her çağrı yeni mülakatçı mesajlarını döner."""

    def __init__(self, graph, *, interview_id: str, clock: Callable[[], float] = time.time):
        self._graph = graph
        self._config = {"configurable": {"thread_id": interview_id}}
        self._clock = clock
        self._seen = 0
        self.interview_id = interview_id

    async def start(
        self,
        *,
        job_summary: dict,
        cv_summary: dict | None,
        interview_type: InterviewType,
        language: Language,
        duration_min: int,
        user_id: str = "anonymous",
    ) -> list[Utterance]:
        await self._graph.ainvoke(
            {
                "user_id": user_id,
                "interview_id": self.interview_id,
                "language": language,
                "interview_type": interview_type,
                "job_summary": job_summary,
                "cv_summary": cv_summary,
                "turns": [],
                "started_at": self._clock(),
                "max_duration_s": duration_min * 60,
            },
            self._config,
        )
        return await self._new_utterances()

    async def answer(self, text: str) -> list[Utterance]:
        return await self._resume({"type": "answer", "text": text})

    async def end(self, reason: Literal["end", "timeout"]) -> list[Utterance]:
        return await self._resume({"type": reason})

    async def values(self) -> dict:
        return (await self._graph.aget_state(self._config)).values

    async def status(self) -> str:
        return (await self.values()).get("status", "running")

    async def remaining_s(self) -> float:
        values = await self.values()
        return values["started_at"] + values["max_duration_s"] - self._clock()

    async def close(self) -> None:
        await self._graph.checkpointer.adelete_thread(self.interview_id)

    async def _resume(self, event: dict) -> list[Utterance]:
        if await self.status() == "done":
            return []
        await self._graph.ainvoke(Command(resume=event), self._config)
        return await self._new_utterances()

    async def _new_utterances(self) -> list[Utterance]:
        turns = (await self.values()).get("turns", [])
        new = turns[self._seen :]
        self._seen = len(turns)
        return [
            Utterance(
                text=str(m.content),
                kind=m.additional_kwargs.get("kind", "follow_up"),
                question_index=m.additional_kwargs.get("index"),
            )
            for m in new
            if isinstance(m, AIMessage)
        ]
