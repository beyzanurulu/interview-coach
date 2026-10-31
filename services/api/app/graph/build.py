import time
from collections.abc import Callable

from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph

from app.core.config import Settings
from app.graph.nodes import make_nodes
from app.graph.state import InterviewState
from app.providers.llm.base import LLMProvider


def route_after_interviewer(state: InterviewState) -> str:
    return {"follow_up": "follow_up", "next": "ask"}.get(state.get("decision") or "", "wrap_up")


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
    graph.add_edge("ask", "await_answer")
    graph.add_edge("await_answer", "interviewer")
    graph.add_conditional_edges(
        "interviewer",
        route_after_interviewer,
        {"follow_up": "follow_up", "ask": "ask", "wrap_up": "wrap_up"},
    )
    graph.add_edge("follow_up", "await_answer")
    graph.add_edge("wrap_up", END)
    # Aşama 1: oturum durumu bellekte. Kalıcı saklama Aşama 4'te (Supabase).
    return graph.compile(checkpointer=checkpointer or InMemorySaver())
