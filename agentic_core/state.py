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

    pdf_path: NotRequired[str | None]
    """Path to uploaded bank-statement PDF for Guardian."""

    raw_document: NotRequired[str | None]
    """Optional raw scrubbed text from the PDF."""

    clean_income_profile: NotRequired[dict[str, Any] | None]
    """Serialized :class:`NigerianPITProfile`."""

    tax_parameters: NotRequired[dict[str, Any] | None]
    """Extracted Finance Act parameters (bands, CRA, rent relief)."""

    final_tax_report: NotRequired[dict[str, Any] | None]
    """Canonical :class:`TaxLiabilityReport` as dict."""

    tax_draft: NotRequired[dict[str, Any]]
    """Structured tax computation / citation payload for Streamlit (TaxComputationDraft-shaped)."""

    clarification_needed: NotRequired[bool]
    """True when intake needs human disambiguation (e.g. gift vs income)."""

    clarification_prompts: NotRequired[list[str]]

    pit_interview_pending: NotRequired[bool]
    """True when optional reliefs are unknown and B7 interview should run."""

    strategist_error: NotRequired[str | None]

    hitl_pending: NotRequired[bool]
    """True when human confirmation is required before filing."""

    filing_payload: NotRequired[dict[str, Any]]
    """Final payload for submission after HITL approval."""
