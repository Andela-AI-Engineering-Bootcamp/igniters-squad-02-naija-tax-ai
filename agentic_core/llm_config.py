"""Shared LangChain chat model for strategist / guardian (OpenRouter)."""

from __future__ import annotations

import os

from langchain_openai import ChatOpenAI


def strategist_llm() -> ChatOpenAI | None:
    """Return a low-temperature chat model, or None if API key is missing."""
    key = os.environ.get("OPENROUTER_API_KEY")
    if not key:
        return None
    base = os.environ.get("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1").rstrip("/")
    model = os.environ.get("OPENROUTER_STRATEGIST_MODEL", "openai/gpt-4o-mini")
    return ChatOpenAI(
        model=model,
        api_key=key,
        base_url=base,
        temperature=0,
    )
