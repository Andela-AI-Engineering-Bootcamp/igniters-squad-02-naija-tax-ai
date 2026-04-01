"""Center panel: scrollable chat history + anchored input."""

from __future__ import annotations

from pathlib import Path

import streamlit as st

from ui import api_client
from utils.guardrails import sanitize_for_display, validate_user_message

_UPLOAD_DIR = Path("/tmp/naija_tax_uploads")

# Reserve space (px) below the history container for the attach expander
# and the chat_input bar so the panel total matches PANEL_HEIGHT.
_INPUT_RESERVE_PX = 110


def render_chat_panel(height: int = 640) -> None:
    """Render the center chat panel.

    The chat history sits in a fixed-height scrollable container.
    The attach expander and chat input sit below it, pinned to the
    bottom of the column — matching NotebookLM's layout.

    Args:
        height: Total panel height in pixels — must match PANEL_HEIGHT
                from app.py so all three columns are the same height.
    """
    # ── Chat history (scrollable) ──────────────────────────────────────────
    with st.container(height=height - _INPUT_RESERVE_PX, border=True):
        _render_chat_history()

    # ── Input area (below the scrollable container, fixed at bottom) ───────
    _render_chat_input()


# ─────────────────────────────────────────────────────────────────────────────
# Chat history
# ─────────────────────────────────────────────────────────────────────────────

def _render_chat_history() -> None:
    messages: list[dict] = st.session_state.get("messages", [])
    if not messages:
        with st.chat_message("assistant"):
            st.markdown(
                "Welcome! I'm your NaijaTax filing assistant.\n\n"
                "Upload a bank statement on the left, then ask me about your tax situation."
            )
        return

    for msg in messages:
        role = msg.get("role", "assistant")
        content = sanitize_for_display(msg.get("content", ""))
        with st.chat_message(role):
            st.markdown(str(content))


# ─────────────────────────────────────────────────────────────────────────────
# Chat input (with optional document shortcut)
# ─────────────────────────────────────────────────────────────────────────────

def _render_chat_input() -> None:
    # Compact attach shortcut — same upload path as the left panel.
    # Supported types must stay in sync with _SUPPORTED_TYPES in left_panel.py.
    with st.expander("📎 Attach document", expanded=False):
        shortcut_file = st.file_uploader(
            "Upload document",
            type=["pdf", "jpg", "jpeg", "png", "csv", "xlsx", "docx"],
            key="chat_panel_uploader",
            label_visibility="collapsed",
            help="PDF gives best results. Images, CSV, XLSX and DOCX also accepted.",
        )
        if shortcut_file and shortcut_file.name not in st.session_state.doc_list:
            try:
                validate_user_message(shortcut_file.name)
            except ValueError as exc:
                st.error(str(exc))
            else:
                _UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
                dest = _UPLOAD_DIR / shortcut_file.name
                dest.write_bytes(shortcut_file.getvalue())
                with st.spinner("Parsing document…"):
                    # ═════════════════════════════════════════════════════════
                    # 🔌 INTEGRATION POINT — Same as left_panel.py
                    # See the comment block in left_panel._render_documents_section
                    # for full wiring instructions.
                    # ═════════════════════════════════════════════════════════
                    result = api_client.call_parse_bank_pdf(str(dest))
                st.session_state.parsed_doc = result
                st.session_state.doc_list.append(shortcut_file.name)
                st.rerun()

    prompt = st.chat_input("Ask about Nigerian tax or your filing status…")
    if not prompt:
        return

    try:
        text = validate_user_message(prompt)
    except ValueError as exc:
        st.error(str(exc))
        return

    st.session_state.messages.append({"role": "user", "content": text})

    with st.spinner("Thinking…"):
        # ═════════════════════════════════════════════════════════════════════
        # 🔌 INTEGRATION POINT — LangGraph agent invocation
        #
        # Currently:  returns a keyword-matched mock from api_client.py
        # To wire up: implement api_client.call_langgraph_invoke() to POST:
        #   URL:    {LANGGRAPH_API_URL}/invoke
        #   Body:   {"message": text}
        #   Return: NaijaTaxState dict — see agentic_core/state.py for shape:
        #             {
        #               "messages":     list of LangChain message dicts,
        #               "tax_draft":    dict | None  (TaxComputationDraft),
        #               "hitl_pending": bool,
        #               "filing_payload": dict,
        #             }
        #
        # The LangGraph HTTP service must be running (port 8001).
        # See: agentic_core/graph.py — the /invoke FastAPI endpoint.
        #
        # Note: real LangGraph messages use {"type": "ai", "content": "..."}
        #       not {"role": "assistant", "content": "..."}.
        #       api_client.extract_assistant_text() handles both shapes.
        # ═════════════════════════════════════════════════════════════════════
        response = api_client.call_langgraph_invoke(text)

    assistant_text = api_client.extract_assistant_text(response)
    st.session_state.messages.append({"role": "assistant", "content": assistant_text})

    # ── Side-effects: tax draft triggers HITL queue + summary report ────────
    tax_draft = response.get("tax_draft")
    if tax_draft:
        st.session_state.tax_draft = tax_draft
        st.session_state.hitl_items = list(tax_draft.get("line_items", []))
        st.session_state.hitl_pending = bool(response.get("hitl_pending", False))

        # ═════════════════════════════════════════════════════════════════════
        # 🔌 INTEGRATION POINT — Tax summary report generation
        #
        # Currently:  generates a plain-text .txt report from mock data.
        # To wire up: replace generate_tax_summary_report() with a proper
        #             PDF renderer (e.g. reportlab or weasyprint) once the
        #             tax_draft schema is finalised by the Strategist node.
        #             The tax_draft shape is defined in agentic_core/schemas.py
        #             (TaxComputationDraft Pydantic model).
        # ═════════════════════════════════════════════════════════════════════
        report_bytes = api_client.generate_tax_summary_report(tax_draft)
        year = tax_draft.get("year", "")
        st.session_state.output_reports.append({
            "label": f"Tax Summary {year}",
            "filename": f"tax_summary_{year}.txt",
            "bytes": report_bytes,
        })

    st.rerun()
