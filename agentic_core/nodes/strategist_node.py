"""Agent B: tax calculation & legal RAG (stub for squad integration)."""

from __future__ import annotations

from typing import Any

from langchain_core.messages import AIMessage

from agentic_core.schemas import TaxComputationDraft, TaxLineItem
from agentic_core.state import NaijaTaxState


def strategist_node(state: NaijaTaxState) -> dict[str, Any]:
    """
    Produce a structured tax draft placeholder.
    Replace with LLM + retrieval over FIRS/NTA sources in production.
    """
    draft = TaxComputationDraft(
        year=2026,
        summary="Placeholder computation — connect RAG and rules engine here.",
        line_items=[
            TaxLineItem(
                label="Withholding tax (illustrative)",
                amount_ngn=0.0,
                basis="Placeholder",
            )
        ],
        citations=["Connect legal corpus and official guidance."],
        confidence=0.2,
    )
    payload = draft.model_dump()
    return {
        "tax_draft": payload,
        "messages": [
            AIMessage(
                content=(
                    "Strategist: draft tax computation prepared for review "
                    f"(confidence={draft.confidence})."
                )
            )
        ],
    }
