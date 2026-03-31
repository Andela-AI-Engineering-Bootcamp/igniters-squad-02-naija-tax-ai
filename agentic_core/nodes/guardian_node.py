"""Agent A: ingestion & privacy — scrub PII before downstream use."""

from __future__ import annotations

from typing import Any

from langchain_core.messages import AIMessage

from agentic_core.state import NaijaTaxState
from mcp_server.tools.pii_scrubber import scrub_text


def guardian_node(state: NaijaTaxState) -> dict[str, Any]:
    """Apply PII scrubbing to recent user content and record scrubbed docs."""
    scrubbed: list[dict[str, Any]] = list(state.get("scrubbed_documents") or [])
    for msg in state.get("messages") or []:
        content = getattr(msg, "content", None)
        if isinstance(content, str) and content.strip():
            scrubbed.append({"text": scrub_text(content), "source": "user_turn"})
    note = (
        "Guardian: documents and messages scrubbed for BVN/NUBAN-like patterns."
        if scrubbed
        else "Guardian: no new text to scrub."
    )
    return {
        "scrubbed_documents": scrubbed,
        "messages": [AIMessage(content=note)],
    }
