"""Input/output validation and domain-specific safety checks."""

from __future__ import annotations

import re
from typing import Any

from pydantic import BaseModel, Field, field_validator

from agentic_core.schemas import NigerianPITProfile, TaxParameters

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


def progressive_tax_on_taxable(
    taxable_income: float, tax_bands: list[dict[str, Any]]
) -> float:
    """
    Apply progressive bands where each band has a slice ``limit`` (width in NGN)
    at ``rate``. Unbounded tail: last band may use a very large limit from the Act.
    """
    remaining = max(0.0, float(taxable_income))
    tax = 0.0
    for band in tax_bands:
        if remaining <= 0:
            break
        limit = float(band.get("limit", 0.0))
        rate = float(band.get("rate", 0.0))
        if limit <= 0:
            continue
        take = min(remaining, limit)
        tax += take * rate
        remaining -= take
    return tax


def consolidated_relief_allowance(gross_income: float, tp: TaxParameters) -> float:
    """CRA = max(minimum NGN, sum of gross-based components)."""
    combined = tp.cra_percent_gross_1 * gross_income + tp.cra_percent_gross_2 * gross_income
    return max(tp.cra_minimum_ngn, combined)


def rent_relief_amount(rental_income: float, tp: TaxParameters) -> float:
    if rental_income <= 0 or tp.rent_relief_percent_of_rent <= 0:
        return 0.0
    raw = tp.rent_relief_percent_of_rent * rental_income
    if tp.rent_relief_cap_ngn is not None:
        return min(raw, tp.rent_relief_cap_ngn)
    return raw


def compute_nigerian_pit(
    profile: NigerianPITProfile,
    document_parameters: dict[str, Any] | TaxParameters,
) -> tuple[float, float, float, float]:
    """
    Document-grounded PIT using parameters extracted from the Finance Act.

    Returns (pit_payable_ngn, taxable_income_ngn, cra_ngn, rent_relief_ngn).
    """
    tp = (
        TaxParameters.model_validate(document_parameters)
        if isinstance(document_parameters, dict)
        else document_parameters
    )
    gross = profile.total_gross_income()
    statutory = profile.total_statutory_deductions()
    cra = consolidated_relief_allowance(gross, tp)
    rent_rel = rent_relief_amount(profile.rental_income, tp)
    taxable = gross - statutory - cra - rent_rel
    taxable = max(0.0, taxable)
    bands = [b.model_dump() if hasattr(b, "model_dump") else dict(b) for b in tp.tax_bands]
    tax_before_credits = progressive_tax_on_taxable(taxable, bands)
    payable = max(
        0.0,
        tax_before_credits - profile.paye_deducted - profile.wht_credits,
    )
    return payable, taxable, cra, rent_rel


def verify_tax_math(
    profile: NigerianPITProfile,
    document_parameters: dict[str, Any],
    reported_pit_payable: float,
    *,
    tolerance_ngn: float = 1.0,
) -> bool:
    """Return True if reported liability matches deterministic math from the Act parameters."""
    expected, _, _, _ = compute_nigerian_pit(profile, document_parameters)
    return abs(expected - float(reported_pit_payable)) <= tolerance_ngn


def sanitize_for_display(data: Any) -> Any:
    """Recursively ensure nested structures are JSON-serialization friendly."""
    if isinstance(data, dict):
        return {k: sanitize_for_display(v) for k, v in data.items()}
    if isinstance(data, list):
        return [sanitize_for_display(x) for x in data]
    if isinstance(data, (str, int, float, bool)) or data is None:
        return data
    return str(data)
