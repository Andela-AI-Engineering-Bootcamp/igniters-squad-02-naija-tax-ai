"""Surface strategist extraction/calculation failure."""

from __future__ import annotations

from typing import Any

from langchain_core.messages import AIMessage

from agentic_core.state import NaijaTaxState


def strategist_failed_node(state: NaijaTaxState) -> dict[str, Any]:
    err = state.get("strategist_error") or "Strategist failed."
    return {
        "hitl_pending": True,
        "messages": [AIMessage(content=f"Strategist error: {err}")],
    }
