"""Left column: two separate panels — document upload and output reports.

Called from app.py as:
    render_docs_panel(height=DOC_PANEL_HEIGHT)
    render_reports_panel(height=REPORTS_PANEL_HEIGHT)

Their combined height + PANEL_GAP must equal PANEL_HEIGHT (set in app.py).
"""

from __future__ import annotations

import base64
from pathlib import Path

import streamlit as st

from ui import api_client
from utils.guardrails import validate_user_message

_UPLOAD_DIR = Path("/tmp/naija_tax_uploads")

# ─────────────────────────────────────────────────────────────────────────────
# Supported upload formats
#
# PDF is the primary format for Nigerian bank statements (fully parsed by MCP).
# Images and other doc formats are accepted for future parser support — they
# currently return mock data until the MCP bank_parser is extended.
#
# 🔌 INTEGRATION POINT — Extend MCP bank_parser for non-PDF formats:
#   mcp_server/tools/bank_parser.py → add handlers for:
#     .jpg/.jpeg/.png  → OCR via pytesseract or Google Vision API
#     .csv/.xlsx       → pandas read_csv / read_excel
#     .docx            → python-docx extraction
# ─────────────────────────────────────────────────────────────────────────────
_SUPPORTED_TYPES = ["pdf", "jpg", "jpeg", "png", "csv", "xlsx", "docx"]

# Map extension → display icon for doc cards
_EXT_ICONS: dict[str, str] = {
    "pdf":  "📄",
    "jpg":  "🖼️",
    "jpeg": "🖼️",
    "png":  "🖼️",
    "csv":  "📊",
    "xlsx": "📊",
    "docx": "📝",
}


def _file_icon(filename: str) -> str:
    ext = Path(filename).suffix.lstrip(".").lower()
    return _EXT_ICONS.get(ext, "📎")


# ─────────────────────────────────────────────────────────────────────────────
# Panel A — Document upload
# ─────────────────────────────────────────────────────────────────────────────

def render_docs_panel(height: int = 390) -> None:
    """Scrollable panel containing the document list and the upload widget.

    Args:
        height: Height in pixels. Set in app.py as DOC_PANEL_HEIGHT.
                Combined with PANEL_GAP + render_reports_panel height
                this must equal PANEL_HEIGHT.
    """
    with st.container(height=height, border=True):
        st.markdown("<p class='panel-section-label'>📄 Documents</p>", unsafe_allow_html=True)

        # Render a card for each already-uploaded file
        for filename in st.session_state.doc_list:
            _render_doc_card(filename)

        # Upload widget — accepts all supported formats
        uploaded = st.file_uploader(
            "Add document",
            type=_SUPPORTED_TYPES,
            label_visibility="collapsed",
            key="left_panel_uploader",
            help=(
                "Supported: PDF, JPG, PNG (images), CSV, XLSX (spreadsheets), DOCX.\n"
                "Bank statement PDFs give the best parsing results."
            ),
        )

        if uploaded and uploaded.name not in st.session_state.doc_list:
            try:
                validate_user_message(uploaded.name)
            except ValueError as exc:
                st.error(str(exc))
                return

            _UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
            dest = _UPLOAD_DIR / uploaded.name
            dest.write_bytes(uploaded.getvalue())

            ext = Path(uploaded.name).suffix.lstrip(".").lower()
            if ext != "pdf":
                st.info(
                    f"ℹ️ **{ext.upper()} format detected.** "
                    "Full parsing for this format is coming soon — mock data will be used for now."
                )

            with st.spinner("Parsing document…"):
                # ═════════════════════════════════════════════════════════════
                # 🔌 INTEGRATION POINT — MCP parse_bank_pdf tool
                #
                # Currently:  returns MOCK_PARSED_DOC from api_client.py
                # To wire up: implement api_client.call_parse_bank_pdf() to POST:
                #   URL:    {MCP_SERVER_URL}/tools/parse_bank_pdf
                #   Body:   {"pdf_path": str(dest)}
                #   Return: {"source", "pii_masked", "tables", "summary"}
                #
                # The MCP server must be running (port 8000) and using HTTP
                # transport (not SSE) for plain REST calls to work.
                # See: mcp_server/server.py and mcp_server/tools/bank_parser.py
                #
                # For non-PDF formats, the MCP tool must be extended —
                # see _SUPPORTED_TYPES comment block at the top of this file.
                # ═════════════════════════════════════════════════════════════
                result = api_client.call_parse_bank_pdf(str(dest))

            st.session_state.parsed_doc = result
            st.session_state.doc_list.append(uploaded.name)
            st.rerun()


def _render_doc_card(filename: str) -> None:
    """Horizontal card: icon · filename · PII badge · credit/debit metrics."""
    with st.container(border=True):
        col_icon, col_name, col_badge = st.columns([1, 5, 3])
        col_icon.markdown(_file_icon(filename))
        col_name.markdown(f"**{filename}**")
        col_badge.markdown(":green[✅ PII masked]")

        parsed = st.session_state.get("parsed_doc")
        if parsed and parsed.get("summary"):
            summary = parsed["summary"]
            m1, m2 = st.columns(2)
            m1.metric("Credits", f"₦{summary.get('total_credits_ngn', 0):,.0f}")
            m2.metric("Debits",  f"₦{summary.get('total_debits_ngn', 0):,.0f}")


# ─────────────────────────────────────────────────────────────────────────────
# Panel B — Output reports
# ─────────────────────────────────────────────────────────────────────────────

def render_reports_panel(height: int = 276) -> None:
    """Scrollable panel containing downloadable report cards.

    Reports are appended to session_state.output_reports by:
    - chat_panel.py  → when LangGraph returns a tax_draft
    - hitl_panel.py  → when the user approves the final filing

    Args:
        height: Height in pixels. Set in app.py as REPORTS_PANEL_HEIGHT.
                Must satisfy: DOC_PANEL_HEIGHT + PANEL_GAP + height == PANEL_HEIGHT.
    """
    with st.container(height=height, border=True):
        st.markdown("<p class='panel-section-label'>📑 Reports</p>", unsafe_allow_html=True)

        reports: list[dict] = st.session_state.get("output_reports", [])
        if not reports:
            st.caption("Reports appear here after your tax computation is complete.")
            return

        for report in reports:
            _render_report_card(
                label=report["label"],
                file_bytes=report["bytes"],
                filename=report["filename"],
            )


def _render_report_card(label: str, file_bytes: bytes, filename: str) -> None:
    """Horizontal card: label · view-in-browser link · download button.

    View-in-browser uses a base64 data URI so no server round-trip is needed.
    The link opens the report as plain text in a new browser tab.
    """
    # Build a base64 data URI for the view-in-browser link
    b64 = base64.b64encode(file_bytes).decode("utf-8")
    data_uri = f"data:text/plain;charset=utf-8;base64,{b64}"

    icon = "📊" if "summary" in filename.lower() else "🧾"

    with st.container(border=True):
        col_label, col_view, col_dl = st.columns([4, 2, 2])

        col_label.markdown(f"{icon} **{label}**")

        # View in browser — opens data URI in a new tab (no server needed)
        col_view.markdown(
            f"""
            <a href="{data_uri}" target="_blank"
               style="display:inline-block;width:100%;text-align:center;
                      padding:6px 0;border-radius:6px;font-size:0.82rem;
                      text-decoration:none;color:inherit;
                      border:1px solid rgba(128,128,128,0.35);">
                🔍 View
            </a>
            """,
            unsafe_allow_html=True,
        )

        # Download — saves the file to the user's machine
        col_dl.download_button(
            label="⬇ Save",
            data=file_bytes,
            file_name=filename,
            mime="text/plain",
            key=f"dl_{filename}",
            use_container_width=True,
        )


# ─────────────────────────────────────────────────────────────────────────────
# Backwards-compat shim — render_left_panel() still works if called directly
# ─────────────────────────────────────────────────────────────────────────────

def render_left_panel(height: int = 680) -> None:
    """Deprecated: use render_docs_panel() + render_reports_panel() instead."""
    render_docs_panel(height=390)
    render_reports_panel(height=height - 390 - 14)
