"""Agent C: human-in-the-loop filing logic."""

from __future__ import annotations

from typing import Any

from langchain_core.messages import AIMessage

from agentic_core.state import NaijaTaxState


def sidekick_node(state: NaijaTaxState) -> dict[str, Any]:
    """Mark HITL pending when a tax draft exists; prepare filing payload stub."""
    tax_draft = state.get("tax_draft") or {}
    pending = bool(tax_draft)
    filing = {"status": "awaiting_human_confirmation", "draft": tax_draft}
    msg = (
        "Sidekick: filing staged — confirm in the UI before submission."
        if pending
        else "Sidekick: nothing to file yet."
    )
    return {
        "hitl_pending": pending,
        "filing_payload": filing,
        "messages": [AIMessage(content=msg)],
    }
