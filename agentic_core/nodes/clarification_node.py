"""End graph when Guardian needs disambiguation before calculation."""

from __future__ import annotations

from typing import Any

from langchain_core.messages import AIMessage

from agentic_core.state import NaijaTaxState


def clarification_end_node(state: NaijaTaxState) -> dict[str, Any]:
    prompts = state.get("clarification_prompts") or []
    text = "Clarification required before tax calculation:\n- " + "\n- ".join(
        str(p) for p in prompts
    )
    return {
        "hitl_pending": True,
        "messages": [AIMessage(content=text)],
    }
