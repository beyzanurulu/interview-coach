import time
from collections.abc import Callable

from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph

from app.core.config import Settings
from app.graph.nodes import make_nodes
from app.graph.state import InterviewState
from app.providers.llm.base import LLMProvider

INTERVIEWER_ROUTES = {
    "follow_up": "follow_up",
    "next": "ask",
    "redirect": "redirect",
    "candidate_questions": "candidate_questions",
    "answer_candidate": "answer_candidate",
    "wrap_up": "wrap_up",
}


def route_after_interviewer(state: InterviewState) -> str:
    return INTERVIEWER_ROUTES.get(state.get("decision") or "", "wrap_up")


def route_after_answer_candidate(state: InterviewState) -> str:
    return "wrap_up" if state.get("decision") == "wrap_up" else "await_answer"


def build_interview_graph(
    llm: LLMProvider,
    settings: Settings,
    *,
    clock: Callable[[], float] = time.time,
    checkpointer: BaseCheckpointSaver | None = None,
):
    nodes = make_nodes(llm, settings, clock)
    graph = StateGraph(InterviewState)
    for name, fn in nodes.items():
        graph.add_node(name, fn)

    graph.add_edge(START, "planner")
    graph.add_edge("planner", "ask")
    for asking in ("ask", "follow_up", "redirect", "candidate_questions"):
        graph.add_edge(asking, "await_answer")
    graph.add_edge("await_answer", "interviewer")
    graph.add_conditional_edges(
        "interviewer", route_after_interviewer, list(set(INTERVIEWER_ROUTES.values()))
    )
    graph.add_conditional_edges(
        "answer_candidate", route_after_answer_candidate, ["wrap_up", "await_answer"]
    )
    graph.add_edge("wrap_up", END)
    # Oturum durumu bellekte. Kalıcı saklama Aşama 4'te (Supabase).
    return graph.compile(checkpointer=checkpointer or InMemorySaver())
