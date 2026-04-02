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


class NigerianPITProfile(BaseModel):
    """Form A–oriented PIT inputs (bank statements only prefill a subset)."""

    tin: str | None = Field(
        None,
        description="Tax Identification Number when known (often 10 digits).",
    )

    gross_salary: float = Field(0.0, description="Employment income / salary.")
    trade_income: float = Field(
        0.0,
        description="Business or self-employment income (e.g. inferred from deposits).",
    )
    dividend_income: float = Field(0.0, description="Dividend income.")
    rental_income: float = Field(0.0, description="Rental income.")

    pension_contribution: float = Field(
        0.0, description="Statutory or voluntary pension contributions claimed."
    )
    nhf_contribution: float = Field(0.0, description="National Housing Fund contributions.")
    nhis_premium: float = Field(0.0, description="NHIS or similar health premiums.")
    life_assurance_premium: float = Field(0.0, description="Life assurance premiums.")

    paye_deducted: float = Field(0.0, description="PAYE already withheld by employer.")
    wht_credits: float = Field(0.0, description="Withholding tax credits available.")

    def total_gross_income(self) -> float:
        return (
            self.gross_salary
            + self.trade_income
            + self.dividend_income
            + self.rental_income
        )

    def total_statutory_deductions(self) -> float:
        return (
            self.pension_contribution
            + self.nhf_contribution
            + self.nhis_premium
            + self.life_assurance_premium
        )


# Backward-compatible alias for sprint wording
CleanIncomeProfile = NigerianPITProfile


class TaxBand(BaseModel):
    """One progressive slice: amount width at `rate`."""

    limit: float = Field(
        ...,
        ge=0.0,
        description="NGN width of this bracket at this rate (see Finance Act tables).",
    )
    rate: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Rate applied to income in this slice (e.g. 0.07).",
    )


class TaxParameters(BaseModel):
    """Legal parameters extracted from the Finance Act via RAG (document-grounded)."""

    tax_bands: list[TaxBand] = Field(
        default_factory=list,
        description="Ordered progressive bands; each limit is slice width at rate.",
    )
    cra_minimum_ngn: float = Field(
        200_000.0,
        description="Minimum Consolidated Relief Allowance (NGN).",
    )
    cra_percent_gross_1: float = Field(
        0.01,
        description="First CRA component as fraction of gross (e.g. 1%).",
    )
    cra_percent_gross_2: float = Field(
        0.20,
        description="Second CRA component as fraction of gross (e.g. 20%).",
    )
    rent_relief_percent_of_rent: float = Field(
        0.0,
        ge=0.0,
        le=1.0,
        description="Fraction of rental income allowed as rent relief.",
    )
    rent_relief_cap_ngn: float | None = Field(
        None,
        description="Cap on rent relief (NGN), if applicable.",
    )
    source_citations: list[str] = Field(
        default_factory=list,
        description="Act section references or chunk anchors used for extraction.",
    )


class TaxLiabilityReport(BaseModel):
    """Strategist output: liability grounded in Act parameters and profile."""

    year: int
    jurisdiction: str = "Nigeria"
    summary: str
    line_items: list[TaxLineItem] = Field(default_factory=list)
    citations: list[str] = Field(default_factory=list)
    confidence: float = Field(0.85, ge=0.0, le=1.0)

    gross_income_ngn: float = 0.0
    taxable_income_ngn: float = 0.0
    pit_payable_ngn: float = 0.0
    consolidated_relief_ngn: float = 0.0
    rent_relief_ngn: float = 0.0
    tax_parameters_snapshot: dict[str, Any] = Field(default_factory=dict)
    math_verified: bool = False
    math_error: str | None = None

    def as_tax_computation_draft(self) -> TaxComputationDraft:
        """UI (`tax_draft`) expects TaxComputationDraft-shaped dict."""
        return TaxComputationDraft(
            year=self.year,
            jurisdiction=self.jurisdiction,
            summary=self.summary,
            line_items=list(self.line_items),
            citations=list(self.citations),
            confidence=self.confidence,
        )
