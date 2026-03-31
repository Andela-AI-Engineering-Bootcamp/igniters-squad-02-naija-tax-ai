"""LangGraph state as TypedDict definitions."""

from __future__ import annotations

from typing import Annotated, Any, TypedDict

from langgraph.graph.message import add_messages
from typing_extensions import NotRequired


class NaijaTaxState(TypedDict):
    """Shared graph state passed between nodes."""

    messages: Annotated[list, add_messages]
    """Conversation + tool messages (LangGraph reducer)."""

    scrubbed_documents: NotRequired[list[dict[str, Any]]]
    """Metadata and text chunks after privacy scrubbing."""

    tax_draft: NotRequired[dict[str, Any]]
    """Structured tax computation / citation payload from the strategist."""

    hitl_pending: NotRequired[bool]
    """True when human confirmation is required before filing."""

    filing_payload: NotRequired[dict[str, Any]]
    """Final payload for submission after HITL approval."""
