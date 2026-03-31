"""Compile guardian → strategist → sidekick into a LangGraph workflow."""

from __future__ import annotations

import os

from langchain_core.messages import HumanMessage
from langgraph.graph import END, StateGraph

from agentic_core.nodes.guardian_node import guardian_node
from agentic_core.nodes.sidekick_node import sidekick_node
from agentic_core.nodes.strategist_node import strategist_node
from agentic_core.state import NaijaTaxState


def _build_graph():
    g = StateGraph(NaijaTaxState)
    g.add_node("guardian", guardian_node)
    g.add_node("strategist", strategist_node)
    g.add_node("sidekick", sidekick_node)
    g.set_entry_point("guardian")
    g.add_edge("guardian", "strategist")
    g.add_edge("strategist", "sidekick")
    g.add_edge("sidekick", END)
    return g.compile()


graph = _build_graph()


def invoke_demo(user_text: str) -> dict:
    """Helper for UI / health checks."""
    return graph.invoke({"messages": [HumanMessage(content=user_text)]})


# --- Optional HTTP service for docker-compose `langgraph` service ---
def _make_app():
    from fastapi import FastAPI

    fastapi_app = FastAPI(title="Naija Tax LangGraph", version="0.1.0")

    @fastapi_app.get("/health")
    def health() -> dict:
        return {"status": "ok", "service": "langgraph"}

    @fastapi_app.post("/invoke")
    def invoke(body: dict) -> dict:
        text = (body.get("message") or "").strip() or "ping"
        return invoke_demo(text)

    return fastapi_app


app = _make_app()

if __name__ == "__main__":
    import uvicorn

    host = os.environ.get("LANGGRAPH_HOST", "0.0.0.0")
    port = int(os.environ.get("LANGGRAPH_PORT", "8001"))
    uvicorn.run(app, host=host, port=port)
