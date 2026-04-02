"""Agent A: ingestion — parse bank PDF, scrub PII, build NigerianPITProfile."""

from __future__ import annotations

import re
from typing import Any

from langchain_core.messages import AIMessage, HumanMessage

from agentic_core.llm_config import strategist_llm
from agentic_core.schemas import NigerianPITProfile
from agentic_core.state import NaijaTaxState
from mcp_server.tools.bank_parser import parse_and_scrub


def _amounts_from_text(text: str) -> list[float]:
    out: list[float] = []
    for m in re.finditer(r"\b\d[\d,]*(?:\.\d{1,2})?\b", text):
        s = m.group(0).replace(",", "")
        try:
            v = float(s)
        except ValueError:
            continue
        if v > 0:
            out.append(v)
    return out


def _heuristic_profile(scrubbed: str) -> NigerianPITProfile:
    """Infer a minimal profile when no LLM is available."""
    amounts = _amounts_from_text(scrubbed)
    if not amounts:
        return NigerianPITProfile()
    trade_guess = min(1_000_000_000.0, max(amounts))
    return NigerianPITProfile(trade_income=trade_guess)


async def _llm_profile(scrubbed: str) -> NigerianPITProfile | None:
    llm = strategist_llm()
    if llm is None:
        return None
    structured = llm.with_structured_output(NigerianPITProfile)
    msg = (
        "You map scrubbed Nigerian bank-statement text to a NigerianPITProfile. "
        "Numbers may be masked (***). Infer trade_income from typical credit patterns; "
        "leave statutory reliefs at 0 unless clearly stated. "
        "Scrubbed text follows:\n\n"
        f"{scrubbed[:12000]}"
    )
    out = await structured.ainvoke([HumanMessage(content=msg)])
    return out if isinstance(out, NigerianPITProfile) else None


def _needs_pit_interview(profile: NigerianPITProfile) -> bool:
    if profile.total_gross_income() <= 0:
        return False
    reliefs = (
        profile.pension_contribution
        + profile.nhf_contribution
        + profile.nhis_premium
        + profile.life_assurance_premium
    )
    return reliefs == 0.0


def _ambiguous_credits_hint(scrubbed: str) -> list[str]:
    hints: list[str] = []
    if re.search(r"\bgift\b|\bnon-taxable\b", scrubbed, re.I):
        hints.append(
            "Some inflows may be gifts or non-taxable transfers — confirm if unsure."
        )
    return hints


async def guardian_node(state: NaijaTaxState) -> dict[str, Any]:
    pdf_path = state.get("pdf_path")
    if not pdf_path or not str(pdf_path).strip():
        return {
            "messages": [
                AIMessage(
                    content="Guardian: no pdf_path in state — upload a bank statement PDF."
                )
            ],
            "clarification_needed": True,
            "clarification_prompts": ["Provide pdf_path in the invoke payload."],
        }

    parsed = await parse_and_scrub(str(pdf_path).strip())
    scrubbed_docs = list(state.get("scrubbed_documents") or [])
    scrubbed_docs.append(
        {"source": "parse_and_scrub", "status": parsed.get("status"), "path": pdf_path}
    )

    if parsed.get("status") != "ok":
        detail = parsed.get("detail") or parsed.get("error", "unknown")
        return {
            "scrubbed_documents": scrubbed_docs,
            "messages": [AIMessage(content=f"Guardian: could not read PDF ({detail}).")],
            "clarification_needed": True,
            "clarification_prompts": [str(detail)],
        }

    scrubbed_text = parsed.get("scrubbed_text") or ""
    profile = await _llm_profile(scrubbed_text)
    if profile is None:
        profile = _heuristic_profile(scrubbed_text)

    prompts = _ambiguous_credits_hint(scrubbed_text)
    clarification_needed = bool(prompts)

    pit_interview_pending = _needs_pit_interview(profile) and not clarification_needed

    note = (
        "Guardian: bank text parsed into NigerianPITProfile "
        f"(gross total ≈ {profile.total_gross_income():,.2f} NGN)."
    )
    return {
        "scrubbed_documents": scrubbed_docs,
        "raw_document": scrubbed_text[:50_000],
        "clean_income_profile": profile.model_dump(),
        "clarification_needed": clarification_needed,
        "clarification_prompts": prompts,
        "pit_interview_pending": pit_interview_pending,
        "messages": [AIMessage(content=note)],
    }
