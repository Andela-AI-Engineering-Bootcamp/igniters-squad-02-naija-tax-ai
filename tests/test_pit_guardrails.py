"""Unit tests for document-grounded PIT math."""

from agentic_core.schemas import NigerianPITProfile, TaxBand, TaxParameters
from utils.guardrails import compute_nigerian_pit, verify_tax_math


def test_compute_nigerian_pit_flat_band():
    profile = NigerianPITProfile(trade_income=1_000_000.0)
    tp = TaxParameters(
        tax_bands=[TaxBand(limit=1e15, rate=0.1)],
        cra_minimum_ngn=200_000.0,
        cra_percent_gross_1=0.01,
        cra_percent_gross_2=0.20,
    )
    payable, taxable, cra, _rent = compute_nigerian_pit(profile, tp.model_dump())
    assert cra == 210_000.0
    assert taxable == 790_000.0
    assert payable == 79_000.0


def test_verify_tax_math_matches():
    profile = NigerianPITProfile(trade_income=500_000.0)
    tp = TaxParameters(
        tax_bands=[TaxBand(limit=1e15, rate=0.05)],
        cra_minimum_ngn=200_000.0,
        cra_percent_gross_1=0.01,
        cra_percent_gross_2=0.20,
    )
    d = tp.model_dump()
    pay, _, _, _ = compute_nigerian_pit(profile, d)
    assert verify_tax_math(profile, d, pay)
