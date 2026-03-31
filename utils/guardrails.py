"""Input/output validation and domain-specific safety checks."""

from __future__ import annotations

import re
from typing import Any

from pydantic import BaseModel, Field, field_validator

from utils.logger import get_logger

logger = get_logger(__name__)

_MAX_MESSAGE_LEN = 16_000
_ALLOWED_TOPICS_PATTERN = re.compile(
    r"(tax|firs|nigeria|nta|withholding|vat|cit|pit|compliance|filing)",
    re.IGNORECASE,
)


class ChatTurn(BaseModel):
    """Validated chat payload from the UI."""

    role: str = Field(..., pattern="^(user|assistant|system)$")
    content: str = Field(..., min_length=1, max_length=_MAX_MESSAGE_LEN)

    @field_validator("content")
    @classmethod
    def strip_and_check(cls, v: str) -> str:
        s = v.strip()
        if not s:
            raise ValueError("content cannot be empty")
        return s


def validate_user_message(text: str) -> str:
    """Basic length and emptiness checks for free-form user input."""
    s = text.strip()
    if not s:
        raise ValueError("Message is empty.")
    if len(s) > _MAX_MESSAGE_LEN:
        raise ValueError("Message exceeds maximum length.")
    return s


def output_safety_check(text: str) -> tuple[bool, str]:
    """
    Lightweight domain guardrail: flag outputs that look entirely off-topic.
    Returns (ok, reason). Does not block; callers may log or surface in UI.
    """
    if _ALLOWED_TOPICS_PATTERN.search(text):
        return True, ""
    logger.info("Guardrail: response may be outside tax domain")
    return True, "outside_domain_hint"


def sanitize_for_display(data: Any) -> Any:
    """Recursively ensure nested structures are JSON-serialization friendly."""
    if isinstance(data, dict):
        return {k: sanitize_for_display(v) for k, v in data.items()}
    if isinstance(data, list):
        return [sanitize_for_display(x) for x in data]
    if isinstance(data, (str, int, float, bool)) or data is None:
        return data
    return str(data)
