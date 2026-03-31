"""Logging helpers that strip common Nigerian PII before emitting to console."""

from __future__ import annotations

import logging
import re
from typing import Any

# BVN (11 digits), NUBAN (10 digits) — coarse patterns for log redaction
_REDACT_PATTERNS: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"\b\d{11}\b"), "[BVN_REDACTED]"),
    (re.compile(r"\b\d{10}\b"), "[NUBAN_REDACTED]"),
)


class PIISafeFilter(logging.Filter):
    """Filter that redacts BVN/NUBAN-like sequences from log records."""

    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            record.msg = _redact_text(record.msg)
        if record.args:
            record.args = tuple(
                _redact_text(a) if isinstance(a, str) else a for a in record.args
            )
        return True


def _redact_text(text: str) -> str:
    out = text
    for pattern, repl in _REDACT_PATTERNS:
        out = pattern.sub(repl, out)
    return out


def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    if not any(isinstance(f, PIISafeFilter) for f in logger.filters):
        logger.addFilter(PIISafeFilter())
    return logger


def safe_log_extra(**kwargs: Any) -> dict[str, Any]:
    """Stringify and redact values intended for log `extra` payloads."""
    return {k: _redact_text(str(v)) for k, v in kwargs.items()}
