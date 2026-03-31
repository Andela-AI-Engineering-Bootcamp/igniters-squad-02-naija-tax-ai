"""Regex-based masking for BVN and NUBAN in free text."""

from __future__ import annotations

import re

# Bank Verification Number: 11 digits
_BVN = re.compile(r"\b(\d{11})\b")
# NUBAN: 10 digits (context-agnostic; may match other 10-digit IDs)
_NUBAN = re.compile(r"\b(\d{10})\b")


def scrub_text(text: str, mask: str = "***") -> str:
    """
    Mask likely BVN (11 digits) and NUBAN (10 digits) sequences.
    Order: longer patterns first to avoid partial overlaps in edge cases.
    """
    if not text:
        return text
    out = _BVN.sub(mask, text)
    out = _NUBAN.sub(mask, out)
    return out
