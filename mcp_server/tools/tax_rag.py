"""Chroma-backed retrieval over Nigerian Finance Act text (to be wired)."""

from __future__ import annotations

from typing import Any


def query_tax_law(query: str, top_k: int = 5) -> dict[str, Any]:
    """
    Retrieve relevant tax-law snippets for a natural-language query.

    When Chroma is integrated, this should return ranked chunks with metadata.
    Until then, returns a stable placeholder response (no LLM calls here).
    """
    _ = top_k
    q = (query or "").strip()
    if not q:
        return {
            "status": "empty_query",
            "chunks": [],
            "detail": "Provide a non-empty query string.",
        }
    return {
        "status": "not_configured",
        "chunks": [],
        "detail": "Chroma collection for Nigerian tax law is not wired yet.",
        "query_preview": q[:200],
    }
