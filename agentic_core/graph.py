"""Compile guardian → (pit interview?) → strategist → sidekick with HITL interrupts."""

from __future__ import annotations

import os
from typing import Any

from langchain_core.messages import HumanMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph
from langgraph.types import Command

from agentic_core.nodes.clarification_node import clarification_end_node
from agentic_core.nodes.guardian_node import guardian_node
from agentic_core.nodes.pit_interview_node import pit_interview_node
from agentic_core.nodes.sidekick_node import sidekick_fill_node, sidekick_launch_node
from agentic_core.nodes.strategist_failed_node import strategist_failed_node
from agentic_core.nodes.strategist_node import strategist_node
from agentic_core.state import NaijaTaxState


def route_after_guardian(state: NaijaTaxState) -> str:
    if state.get("clarification_needed"):
        return "clarification_end"
    if state.get("pit_interview_pending"):
        return "pit_interview"
    return "strategist"


def route_after_strategist(state: NaijaTaxState) -> str:
    if state.get("strategist_error"):
        return "strategist_failed"
    return "sidekick_launch"


def _build_graph():
    g = StateGraph(NaijaTaxState)
    g.add_node("guardian", guardian_node)
    g.add_node("clarification_end", clarification_end_node)
    g.add_node("pit_interview", pit_interview_node)
    g.add_node("strategist", strategist_node)
    g.add_node("strategist_failed", strategist_failed_node)
    g.add_node("sidekick_launch", sidekick_launch_node)
    g.add_node("sidekick_fill", sidekick_fill_node)

    g.set_entry_point("guardian")
    g.add_conditional_edges(
        "guardian",
        route_after_guardian,
        {
            "clarification_end": "clarification_end",
            "pit_interview": "pit_interview",
            "strategist": "strategist",
        },
    )
    g.add_edge("clarification_end", END)
    g.add_edge("pit_interview", "strategist")
    g.add_conditional_edges(
        "strategist",
        route_after_strategist,
        {
            "strategist_failed": "strategist_failed",
            "sidekick_launch": "sidekick_launch",
        },
    )
    g.add_edge("strategist_failed", END)
    g.add_edge("sidekick_launch", "sidekick_fill")
    g.add_edge("sidekick_fill", END)

    return g.compile(
        checkpointer=MemorySaver(),
        interrupt_before=["sidekick_launch", "sidekick_fill"],
    )


graph = _build_graph()


def _initial_state(
    user_text: str,
    pdf_path: str | None,
) -> dict[str, Any]:
    return {
        "messages": [HumanMessage(content=user_text)],
        "pdf_path": pdf_path,
    }


def _thread_config(thread_id: str) -> dict[str, Any]:
    return {"configurable": {"thread_id": thread_id}}


async def invoke_async(
    user_text: str,
    *,
    pdf_path: str | None = None,
    thread_id: str = "default",
    resume: Any | None = None,
) -> dict[str, Any]:
    """Invoke or resume the graph (use ``resume`` after LangGraph interrupts)."""
    cfg = _thread_config(thread_id)
    if resume is not None:
        return await graph.ainvoke(Command(resume=resume), cfg)
    return await graph.ainvoke(_initial_state(user_text, pdf_path), cfg)


def invoke_demo(
    user_text: str,
    pdf_path: str | None = None,
    thread_id: str = "default",
    resume: Any | None = None,
) -> dict[str, Any]:
    """Sync helper for scripts and tests."""
    import asyncio

    return asyncio.run(
        invoke_async(user_text, pdf_path=pdf_path, thread_id=thread_id, resume=resume)
    )


def _make_app():
    from fastapi import FastAPI

    fastapi_app = FastAPI(title="Naija Tax LangGraph", version="0.2.0")

    @fastapi_app.get("/health")
    def health() -> dict:
        return {"status": "ok", "service": "langgraph"}

    @fastapi_app.post("/invoke")
    async def invoke(body: dict) -> dict:
        text = (body.get("message") or "").strip() or "ping"
        pdf = body.get("pdf_path")
        tid = (body.get("thread_id") or "default").strip() or "default"
        resume = body.get("resume")
        return await invoke_async(text, pdf_path=pdf, thread_id=tid, resume=resume)

    return fastapi_app


app = _make_app()

if __name__ == "__main__":
    import uvicorn

    host = os.environ.get("LANGGRAPH_HOST", "0.0.0.0")
    port = int(os.environ.get("LANGGRAPH_PORT", "8001"))
    uvicorn.run(app, host=host, port=port)
