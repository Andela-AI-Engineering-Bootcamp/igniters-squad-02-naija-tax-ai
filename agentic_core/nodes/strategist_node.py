"""Agent B: extract Act parameters via RAG + LLM, deterministic PIT, citations."""

from __future__ import annotations

import os
from datetime import datetime
from typing import Any

from langchain_core.messages import AIMessage, HumanMessage

from agentic_core.llm_config import strategist_llm
from agentic_core.schemas import (
    NigerianPITProfile,
    TaxBand,
    TaxLineItem,
    TaxLiabilityReport,
    TaxParameters,
)
from agentic_core.state import NaijaTaxState
from mcp_server.tools.tax_rag import query_tax_law
from utils.guardrails import compute_nigerian_pit, verify_tax_math
from utils.paths import REPO_ROOT


def _rag_context() -> tuple[str, list[str]]:
    """
    Prefer plain-text Act files under data/finance_acts/ (fast, deterministic).
    Optionally enrich with Chroma ``query_tax_law`` when the stack is available.
    """
    blobs: list[str] = []
    cites: list[str] = []
    fin = REPO_ROOT / "data" / "finance_acts"
    if fin.is_dir():
        for path in sorted(fin.glob("*.txt")):
            if path.name.upper().startswith("README"):
                continue
            try:
                blobs.append(path.read_text(encoding="utf-8"))
                cites.append(f"file:{path.name}")
            except OSError:
                continue

    if os.environ.get("NAIJA_USE_CHROMA_RAG") == "1":
        try:
            q1 = query_tax_law(
                "Personal Income Tax progressive tax bands CRA Nigeria Finance Act",
                top_k=6,
            )
            if q1.get("status") == "ok":
                for c in q1.get("chunks") or []:
                    t = c.get("text") or ""
                    if t:
                        blobs.append(t)
                cites.append("chroma:pit_query")
        except Exception:
            pass

    return "\n\n---\n\n".join(blobs), cites


async def _extract_parameters(act_text: str) -> TaxParameters | None:
    if not act_text.strip():
        return None
    llm = strategist_llm()
    if llm is None:
        return None
    structured = llm.with_structured_output(TaxParameters)
    msg = (
        "Extract Nigerian Personal Income Tax parameters from the Act excerpts below. "
        "tax_bands: ordered list of {limit, rate} where limit is the NGN width of each "
        "progressive slice at that rate (decimal, e.g. 0.07). Include cra_minimum_ngn, "
        "cra_percent_gross_1 (e.g. 0.01), cra_percent_gross_2 (e.g. 0.20), "
        "rent_relief_percent_of_rent and rent_relief_cap_ngn if stated. "
        "Add source_citations with section references mentioned in the text.\n\n"
        f"{act_text[:24000]}"
    )
    out = await structured.ainvoke([HumanMessage(content=msg)])
    return out if isinstance(out, TaxParameters) else None


def _fallback_parameters() -> TaxParameters:
    """Conservative placeholder when RAG/LLM unavailable — still document-grounded path fails verify."""
    return TaxParameters(
        tax_bands=[],
        source_citations=["fallback_empty_bands"],
    )


def _illustrative_parameters_from_act_placeholder() -> TaxParameters:
    """
    Progressive slices only for local demos when LLM extraction is unavailable.
    Replace with Act-extracted values in production (set OPENROUTER_API_KEY).
    """
    return TaxParameters(
        tax_bands=[
            TaxBand(limit=300_000, rate=0.07),
            TaxBand(limit=300_000, rate=0.11),
            TaxBand(limit=500_000, rate=0.15),
            TaxBand(limit=500_000, rate=0.19),
            TaxBand(limit=1_600_000, rate=0.21),
            TaxBand(limit=1e15, rate=0.24),
        ],
        cra_minimum_ngn=200_000.0,
        cra_percent_gross_1=0.01,
        cra_percent_gross_2=0.20,
        source_citations=[
            "ILLUSTRATIVE_ONLY: replace with Finance Act extraction via query_tax_law + LLM"
        ],
    )


async def strategist_node(state: NaijaTaxState) -> dict[str, Any]:
    profile_dict = state.get("clean_income_profile") or {}
    try:
        profile = NigerianPITProfile.model_validate(profile_dict)
    except Exception as e:
        return {
            "strategist_error": f"Invalid NigerianPITProfile: {e}",
            "messages": [AIMessage(content=f"Strategist: invalid profile ({e}).")],
        }

    act_text, preview_cites = _rag_context()
    tp = await _extract_parameters(act_text)
    if tp is None:
        tp = _fallback_parameters()

    if not tp.tax_bands:
        tp = _illustrative_parameters_from_act_placeholder()
        extra = [f"rag_query:{c}" for c in preview_cites]
        if act_text.strip():
            extra.append(
                "note: prefer OPENROUTER_API_KEY + LLM to replace illustrative bands with Act extraction."
            )
        else:
            extra.append(
                "note: no RAG text (index Finance Act under data/finance_acts/) — illustrative bands."
            )
        tp.source_citations = list(tp.source_citations) + extra

    tp.source_citations = list(tp.source_citations or []) + [f"query:{c}" for c in preview_cites]

    payable, taxable, cra, rent_rel = compute_nigerian_pit(profile, tp.model_dump())
    year = datetime.now().year

    report = TaxLiabilityReport(
        year=year,
        summary=(
            f"Estimated PIT payable {payable:,.2f} NGN (taxable income {taxable:,.2f} NGN). "
            "Parameters from Finance Act text and/or illustrative fallback — see citations."
        ),
        line_items=[
            TaxLineItem(
                label="Consolidated Relief Allowance (CRA)",
                amount_ngn=cra,
                basis="Finance Act (extracted)",
            ),
            TaxLineItem(
                label="Rent relief",
                amount_ngn=rent_rel,
                basis="Finance Act (extracted)",
            ),
            TaxLineItem(
                label="Tax before PAYE/WHT credits",
                amount_ngn=max(0.0, payable + profile.paye_deducted + profile.wht_credits),
                basis="Progressive bands from Act",
            ),
            TaxLineItem(
                label="PAYE deducted (credit)",
                amount_ngn=-profile.paye_deducted,
                basis="Profile",
            ),
            TaxLineItem(
                label="WHT credits",
                amount_ngn=-profile.wht_credits,
                basis="Profile",
            ),
            TaxLineItem(
                label="Net PIT payable",
                amount_ngn=payable,
                basis="Deterministic recompute",
            ),
        ],
        citations=list(tp.source_citations),
        confidence=0.9 if strategist_llm() else 0.4,
        gross_income_ngn=profile.total_gross_income(),
        taxable_income_ngn=taxable,
        pit_payable_ngn=payable,
        consolidated_relief_ngn=cra,
        rent_relief_ngn=rent_rel,
        tax_parameters_snapshot=tp.model_dump(),
    )

    ok = verify_tax_math(profile, tp.model_dump(), payable)
    report.math_verified = ok
    if not ok:
        report.math_error = "Deterministic verify_tax_math mismatch — check bands extraction."
        report.confidence = min(report.confidence, 0.3)

    draft = report.as_tax_computation_draft()

    msg = (
        f"Strategist: PIT payable ≈ {payable:,.2f} NGN; math_verified={ok}. "
        f"Citations: {len(report.citations)}."
    )
    return {
        "tax_parameters": tp.model_dump(),
        "final_tax_report": report.model_dump(),
        "tax_draft": draft.model_dump(),
        "strategist_error": None,
        "messages": [AIMessage(content=msg)],
    }
