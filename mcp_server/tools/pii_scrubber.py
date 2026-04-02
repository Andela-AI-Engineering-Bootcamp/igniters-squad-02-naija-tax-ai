"""Deterministic PII masking for MCP tools (regex only; no LLM)."""

from __future__ import annotations

from utils.scrubber import scrub_deterministic


def scrub_text(text: str, mask: str = "***") -> str:
    """Mask BVN-like, NUBAN-like, Nigerian phone, and email patterns in free text."""
    return scrub_deterministic(text, mask=mask)
