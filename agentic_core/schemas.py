"""Pydantic models for structured LLM and tool outputs."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class TaxLineItem(BaseModel):
    label: str
    amount_ngn: float = Field(..., description="Amount in Nigerian Naira")
    basis: str | None = Field(None, description="Statutory or regulatory basis")


class TaxComputationDraft(BaseModel):
    """Structured strategist output for review in UI."""

    year: int
    jurisdiction: str = "Nigeria"
    summary: str
    line_items: list[TaxLineItem] = Field(default_factory=list)
    citations: list[str] = Field(default_factory=list)
    confidence: float = Field(0.5, ge=0.0, le=1.0)


class FilingConfirmation(BaseModel):
    """Human-in-the-loop confirmation record."""

    approved: bool
    reviewer_note: str | None = None
    payload: dict[str, Any] = Field(default_factory=dict)
