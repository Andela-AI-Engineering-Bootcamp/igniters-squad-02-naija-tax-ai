"""API client: mock data for MCP + LangGraph responses.

╔══════════════════════════════════════════════════════════════════════════════╗
║  HOW TO WIRE UP THE REAL BACKEND                                            ║
║                                                                             ║
║  This file is the ONLY place that needs to change when the backend is       ║
║  ready. Components (left_panel, chat_panel, hitl_panel) call the functions  ║
║  below and never talk to any external service directly.                     ║
║                                                                             ║
║  Step-by-step:                                                              ║
║  1. Add `requests` (or `httpx`) to requirements.txt                         ║
║  2. In call_parse_bank_pdf(): replace `return MOCK_PARSED_DOC` with a       ║
║     POST to {MCP_SERVER_URL}/tools/parse_bank_pdf                           ║
║  3. In call_langgraph_invoke(): replace the mock router with a POST to      ║
║     {LANGGRAPH_API_URL}/invoke                                              ║
║  4. Each function already has a detailed comment showing the exact          ║
║     URL, request body, and expected response shape.                         ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

from __future__ import annotations

import datetime
import random
from typing import Any

# ---------------------------------------------------------------------------
# Mock data constants
# ---------------------------------------------------------------------------

MOCK_PARSED_DOC: dict[str, Any] = {
    "source": "camelot",
    "pii_masked": True,
    "summary": {
        "total_credits_ngn": 2_400_000.0,
        "total_debits_ngn": 216_000.0,
        "months_detected": 12,
    },
    "tables": [
        {
            "flavor": "stream",
            "page": 1,
            "data": [
                {"Date": "2025-01-31", "Narration": "SALARY CREDIT",   "Debit": "",          "Credit": "200,000.00", "Balance": "200,000.00"},
                {"Date": "2025-01-31", "Narration": "PAYE WHT - LIRS", "Debit": "18,000.00", "Credit": "",           "Balance": "182,000.00"},
                {"Date": "2025-02-28", "Narration": "SALARY CREDIT",   "Debit": "",          "Credit": "200,000.00", "Balance": "382,000.00"},
                {"Date": "2025-02-28", "Narration": "PAYE WHT - LIRS", "Debit": "18,000.00", "Credit": "",           "Balance": "364,000.00"},
                {"Date": "2025-03-31", "Narration": "SALARY CREDIT",   "Debit": "",          "Credit": "200,000.00", "Balance": "564,000.00"},
                {"Date": "2025-03-31", "Narration": "PAYE WHT - LIRS", "Debit": "18,000.00", "Credit": "",           "Balance": "546,000.00"},
                {"Date": "2025-06-30", "Narration": "SALARY CREDIT",   "Debit": "",          "Credit": "200,000.00", "Balance": "746,000.00"},
                {"Date": "2025-06-30", "Narration": "PAYE WHT - LIRS", "Debit": "18,000.00", "Credit": "",           "Balance": "728,000.00"},
                {"Date": "2025-09-30", "Narration": "SALARY CREDIT",   "Debit": "",          "Credit": "200,000.00", "Balance": "928,000.00"},
                {"Date": "2025-09-30", "Narration": "PAYE WHT - LIRS", "Debit": "18,000.00", "Credit": "",           "Balance": "910,000.00"},
                {"Date": "2025-12-31", "Narration": "SALARY CREDIT",   "Debit": "",          "Credit": "200,000.00", "Balance": "1,110,000.00"},
                {"Date": "2025-12-31", "Narration": "PAYE WHT - LIRS", "Debit": "18,000.00", "Credit": "",           "Balance": "1,092,000.00"},
            ],
        }
    ],
}

MOCK_TAX_DRAFT: dict[str, Any] = {
    "year": 2025,
    "jurisdiction": "Nigeria (Lagos State)",
    "confidence": 0.82,
    "summary": (
        "Annual PIT under PITA (Finance Act 2020). "
        "Gross ₦2,400,000. Tax payable ₦216,000 — fully settled via PAYE."
    ),
    "line_items": [
        {"label": "Gross Annual Income",       "amount_ngn": 2_400_000.0, "basis": "12 × ₦200,000 salary credits per bank statement"},
        {"label": "Consolidated Relief (CRA)", "amount_ngn":   400_000.0, "basis": "PITA S.33 — higher of ₦200k or 1% GI + 20% GI"},
        {"label": "NHF Contribution",          "amount_ngn":    30_000.0, "basis": "2.5% of basic salary — NHF Act"},
        {"label": "NHIS Contribution",         "amount_ngn":    18_000.0, "basis": "1.5% of GI — NHIS Act"},
        {"label": "Taxable Income",            "amount_ngn": 1_952_000.0, "basis": "GI minus all statutory deductions"},
        {"label": "Personal Income Tax (PIT)", "amount_ngn":   216_000.0, "basis": "Finance Act 2020 bands: 7% / 11% / 15% / 19%"},
        {"label": "PAYE Already Withheld",     "amount_ngn":   216_000.0, "basis": "Sum of WHT debits from bank statement"},
        {"label": "Net Tax Balance",           "amount_ngn":         0.0, "basis": "Fully settled via PAYE withholding"},
    ],
    "citations": [
        "Personal Income Tax Act (PITA) Cap P8 LFN 2004 as amended",
        "Finance Act 2020, Section 8 (CRA amendment)",
        "Lagos State Internal Revenue Service (LIRS) PAYE Guidelines 2025",
    ],
}


# ---------------------------------------------------------------------------
# Public API functions
# ---------------------------------------------------------------------------

def call_parse_bank_pdf(pdf_path: str) -> dict[str, Any]:  # noqa: ARG001
    """Return mock parsed bank statement data.

    ═══════════════════════════════════════════════════════════════════════════
    🔌 INTEGRATION POINT — MCP parse_bank_pdf tool
    ───────────────────────────────────────────────────────────────────────────
    Replace the mock below with a real HTTP call:

        import os, requests
        resp = requests.post(
            f"{os.environ['MCP_SERVER_URL']}/tools/parse_bank_pdf",
            json={"pdf_path": pdf_path},
            timeout=15,
        )
        resp.raise_for_status()
        return resp.json()

    Prerequisites:
    • MCP server running on port 8000 (`docker-compose up mcp`)
    • MCP_SERVER_URL set in .env (default: http://localhost:8000)
    • MCP server must use HTTP transport — change FastMCP transport in
      mcp_server/server.py from "sse" to "http" for plain REST calls.

    Expected response shape (mirrors MOCK_PARSED_DOC below):
    {
        "source":     "camelot" | "pymupdf",
        "pii_masked": True,
        "tables":     [{"flavor", "page", "data": [row dicts]}],
        "summary":    {"total_credits_ngn", "total_debits_ngn", "months_detected"},
    }
    ═══════════════════════════════════════════════════════════════════════════
    """
    return MOCK_PARSED_DOC


def call_langgraph_invoke(user_message: str) -> dict[str, Any]:
    """Return a mock LangGraph agent response based on message keywords.

    ═══════════════════════════════════════════════════════════════════════════
    🔌 INTEGRATION POINT — LangGraph /invoke endpoint
    ───────────────────────────────────────────────────────────────────────────
    Replace the keyword router below with a real HTTP call:

        import os, requests
        resp = requests.post(
            f"{os.environ['LANGGRAPH_API_URL']}/invoke",
            json={"message": user_message},
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()   # returns NaijaTaxState as a dict

    Prerequisites:
    • LangGraph service running on port 8001 (`docker-compose up langgraph`)
    • LANGGRAPH_API_URL set in .env (default: http://localhost:8001)
    • See agentic_core/graph.py for the /invoke FastAPI handler.

    Expected response shape (NaijaTaxState — see agentic_core/state.py):
    {
        "messages":       [{"type": "ai", "content": str}, ...],
        "tax_draft":      {TaxComputationDraft} | None,
        "hitl_pending":   bool,
        "filing_payload": dict,
        "scrubbed_documents": [...],
    }

    Note: real LangGraph message dicts use {"type": "ai"}, not
    {"role": "assistant"}. extract_assistant_text() handles both shapes.
    ═══════════════════════════════════════════════════════════════════════════
    """
    msg = user_message.lower()

    if any(kw in msg for kw in ("salary", "income", "statement", "tax", "filing", "situation", "compute", "calculate")):
        return {
            "messages": [{"role": "assistant", "content": (
                "I've reviewed your bank statement. Here's what I found:\n\n"
                "- **Gross Annual Income:** ₦2,400,000 (12 × ₦200,000 monthly salary)\n"
                "- **PAYE Withheld:** ₦216,000 (₦18,000/month)\n"
                "- **Net Tax Balance:** ₦0.00 — your employer has fully settled your PIT via PAYE.\n\n"
                "I've prepared a detailed breakdown. Please confirm each item "
                "in the **Verification Panel** on the right before we proceed to filing."
            )}],
            "tax_draft": MOCK_TAX_DRAFT,
            "hitl_pending": True,
        }

    if any(kw in msg for kw in ("confirm", "yes", "approve", "submit", "file", "proceed")):
        ref = f"LIRS-{datetime.date.today().year}-LAG-{random.randint(100000, 999999)}"
        return {
            "messages": [{"role": "assistant", "content": f"Filing confirmed. LIRS Reference: **{ref}**. Your tax return has been submitted successfully."}],
            "tax_draft": None,
            "hitl_pending": False,
        }

    if "vat" in msg:
        return {
            "messages": [{"role": "assistant", "content": (
                "VAT in Nigeria is currently **7.5%** (Finance Act 2020). "
                "For individuals, VAT is collected at point of sale and does not "
                "appear directly on your personal income tax return unless you are a registered business."
            )}],
            "tax_draft": None,
            "hitl_pending": False,
        }

    if any(kw in msg for kw in ("cit", "company", "corporate")):
        return {
            "messages": [{"role": "assistant", "content": (
                "Companies Income Tax (CIT) is levied at **30%** of taxable profits for large companies "
                "and **20%** for medium companies (Finance Act 2021). "
                "Small companies with turnover below ₦25M are exempt. "
                "Returns are due within **6 months** of the fiscal year end."
            )}],
            "tax_draft": None,
            "hitl_pending": False,
        }

    return {
        "messages": [{"role": "assistant", "content": (
            "I'm your NaijaTax filing assistant. I can help you:\n\n"
            "- Analyse your bank statement for income and deductions\n"
            "- Calculate your Personal Income Tax (PIT) under Nigerian law\n"
            "- Guide you through the FIRS/LIRS filing process step by step\n\n"
            "To get started, upload a bank statement using the **+ Add Document** button on the left, "
            "then ask me about your tax situation."
        )}],
        "tax_draft": None,
        "hitl_pending": False,
    }


def extract_assistant_text(response: dict[str, Any]) -> str:
    """Extract assistant reply text from a LangGraph response dict."""
    for m in reversed(response.get("messages", [])):
        if not isinstance(m, dict):
            continue
        if m.get("type") == "ai" or m.get("role") == "assistant":
            return m.get("content", "")
    return "No response received."


# ---------------------------------------------------------------------------
# Report generation (downloadable text reports)
# ---------------------------------------------------------------------------

def generate_tax_summary_report(tax_draft: dict[str, Any]) -> bytes:
    """Generate a tax computation summary as downloadable UTF-8 text."""
    lines = [
        "=" * 62,
        "  NAIJATAX AI — TAX COMPUTATION SUMMARY",
        "=" * 62,
        f"  Tax Year:     {tax_draft.get('year', 'N/A')}",
        f"  Jurisdiction: {tax_draft.get('jurisdiction', 'N/A')}",
        f"  Confidence:   {int(tax_draft.get('confidence', 0) * 100)}%",
        f"  Generated:    {datetime.date.today().strftime('%d %B %Y')}",
        "",
        "  SUMMARY",
        "  " + "-" * 58,
        f"  {tax_draft.get('summary', '')}",
        "",
        "  LINE ITEMS",
        "  " + "-" * 58,
    ]
    for item in tax_draft.get("line_items", []):
        label = item.get("label", "")
        amount = item.get("amount_ngn", 0)
        basis = item.get("basis", "")
        lines.append(f"  {label:<38} ₦{amount:>14,.2f}")
        if basis:
            lines.append(f"    ({basis})")
    lines += [
        "",
        "  LEGAL CITATIONS",
        "  " + "-" * 58,
    ]
    for cite in tax_draft.get("citations", []):
        lines.append(f"  • {cite}")
    lines += [
        "",
        "=" * 62,
        "  NaijaTax AI  |  Privacy-first  |  FIRS/LIRS Compliant",
        "=" * 62,
    ]
    return "\n".join(lines).encode("utf-8")


def generate_filing_receipt_report(hitl_payload: dict[str, Any]) -> bytes:
    """Generate a filing receipt as downloadable UTF-8 text."""
    ref = f"LIRS-{datetime.date.today().year}-LAG-{random.randint(100000, 999999)}"
    lines = [
        "=" * 62,
        "  NAIJATAX AI — FILING RECEIPT",
        "=" * 62,
        f"  Reference No:  {ref}",
        f"  Filed:         {datetime.date.today().strftime('%d %B %Y')}",
        "  Authority:     Lagos State Internal Revenue Service (LIRS)",
        "  Status:        SUBMITTED",
        "",
        "  CONFIRMED ITEMS",
        "  " + "-" * 58,
    ]
    for label, value in hitl_payload.items():
        if isinstance(value, (int, float)):
            lines.append(f"  {label:<38} ₦{value:>14,.2f}")
        else:
            lines.append(f"  {label:<38} {value}")
    lines += [
        "",
        "=" * 62,
        "  NaijaTax AI  |  Privacy-first  |  FIRS/LIRS Compliant",
        "=" * 62,
    ]
    return "\n".join(lines).encode("utf-8")
