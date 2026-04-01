"""Main Streamlit entry: 3-column layout matching the NaijaTax UI mockup."""

from __future__ import annotations

import datetime
import sys
from pathlib import Path

# Ensure the project root is on sys.path so absolute imports like
# `from ui.components...` and `from utils...` resolve correctly
# regardless of how/where streamlit is invoked.
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

import streamlit as st

from ui.components.chat_panel import render_chat_panel
from ui.components.hitl_panel import render_hitl_panel
from ui.components.left_panel import render_docs_panel, render_reports_panel

# ─────────────────────────────────────────────────────────────────────────────
# Height constants — single source of truth for the entire layout.
#
# The left column is split into two stacked panels. Their combined height
# plus the gap between them must equal PANEL_HEIGHT so all three columns
# appear the same height.
#
#   DOC_PANEL_HEIGHT + PANEL_GAP + REPORTS_PANEL_HEIGHT == PANEL_HEIGHT
#   390              + 14        + 276                  == 680  ✓
#
# To resize: only change PANEL_HEIGHT + DOC_PANEL_HEIGHT — REPORTS_PANEL_HEIGHT
# recalculates automatically.
# ─────────────────────────────────────────────────────────────────────────────
PANEL_HEIGHT        = 680   # pixels — height of center & right panels
PANEL_GAP           = 14    # pixels — approximate vertical gap between stacked containers
DOC_PANEL_HEIGHT    = 390   # pixels — top-left panel (document upload)
REPORTS_PANEL_HEIGHT = PANEL_HEIGHT - DOC_PANEL_HEIGHT - PANEL_GAP  # = 276

# ─────────────────────────────────────────────────────────────────────────────
# Page config
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="NaijaTax AI — Tax Filing Assistant",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ─────────────────────────────────────────────────────────────────────────────
# Global CSS — NotebookLM-inspired: panel shadows, title bar, typography
# ─────────────────────────────────────────────────────────────────────────────
st.markdown(
    """
    <style>
    /* ── Global ─────────────────────────────────────────────────────────── */
    .block-container { padding-top: 0.75rem; padding-bottom: 0.5rem; }
    [data-testid="column"] { padding-top: 0 !important; }

    /* ── Panel cards ─────────────────────────────────────────────────────── */
    [data-testid="stVerticalBlockBorderWrapper"] {
        border-radius: 12px !important;
        border: 1px solid rgba(128,128,128,0.18) !important;
        box-shadow: 0 2px 10px rgba(0,0,0,0.07) !important;
    }

    /* ── Title panel ─────────────────────────────────────────────────────── */
    .title-panel {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 14px 24px;
        border-radius: 12px;
        border: 1px solid rgba(128,128,128,0.18);
        box-shadow: 0 2px 10px rgba(0,0,0,0.07);
        margin-bottom: 14px;
    }
    .title-panel-left  { display: flex; align-items: center; gap: 10px; }
    .title-panel-logo  { font-size: 1.7rem; line-height: 1; }
    .title-panel-name  { font-size: 1.15rem; font-weight: 700; letter-spacing: -0.01em; margin: 0; }
    .title-panel-tag   { font-size: 0.75rem; color: #888; margin: 0; }
    .title-panel-center { text-align: center; }
    .title-panel-step  { font-size: 0.78rem; color: #888; }
    .title-panel-right { text-align: right; }
    .title-panel-user  { font-size: 0.9rem; font-weight: 600; margin: 0; }
    .title-panel-date  { font-size: 0.75rem; color: #888; margin: 0; }
    .privacy-badge     { font-size: 0.72rem; color: #4caf50; margin-top: 2px; }

    /* ── Section labels inside panels ───────────────────────────────────── */
    .panel-section-label {
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.07em;
        color: #888;
        margin: 0 0 6px 0;
    }

    /* ── Metric labels ───────────────────────────────────────────────────── */
    [data-testid="stMetricLabel"] { font-size: 0.72rem !important; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ─────────────────────────────────────────────────────────────────────────────
# Session state — single initialisation block; all keys live here.
# Components read/write these keys but never re-initialise them.
# ─────────────────────────────────────────────────────────────────────────────
_INITIAL_STATE: dict = {
    "messages":       [],     # list[dict] — chat history {role, content}
    "doc_list":       [],     # list[str]  — uploaded filenames
    "parsed_doc":     None,   # dict | None — last MCP parse result
    "tax_draft":      None,   # dict | None — TaxComputationDraft from LangGraph
    "hitl_pending":   False,  # bool — True while verification items remain
    "hitl_items":     [],     # list[dict] — queue of line_items to verify
    "hitl_payload":   {},     # dict — confirmed {label: {amount, ...}} map
    "output_reports": [],     # list[dict] — [{label, filename, bytes}]
}

for _key, _default in _INITIAL_STATE.items():
    if _key not in st.session_state:
        st.session_state[_key] = _default

# ─────────────────────────────────────────────────────────────────────────────
# Title panel — full-width bar above the three columns
# ─────────────────────────────────────────────────────────────────────────────

# Derive a simple filing status label for the centre of the title bar
_steps = ["Upload Docs", "Review Figures", "Verify", "Approve", "Filed ✓"]
if st.session_state.output_reports and any("receipt" in r["filename"] for r in st.session_state.output_reports):
    _current_step = "Filed ✓"
elif not st.session_state.hitl_pending and st.session_state.tax_draft:
    _current_step = "Approve"
elif st.session_state.hitl_pending:
    _current_step = "Verify"
elif st.session_state.tax_draft:
    _current_step = "Review Figures"
elif st.session_state.doc_list:
    _current_step = "Review Figures"
else:
    _current_step = "Upload Docs"

_step_html = " &nbsp;›&nbsp; ".join(
    f"<b>{s}</b>" if s == _current_step else f"<span style='color:#bbb'>{s}</span>"
    for s in _steps
)

st.markdown(
    f"""
    <div class="title-panel">
        <div class="title-panel-left">
            <span class="title-panel-logo">🇳🇬</span>
            <div>
                <p class="title-panel-name">NaijaTax AI</p>
                <p class="title-panel-tag">Privacy-first · FIRS/LIRS Compliant · 2025 Tax Year</p>
            </div>
        </div>
        <div class="title-panel-center">
            <p class="title-panel-step">{_step_html}</p>
        </div>
        <div class="title-panel-right">
            <p class="title-panel-user">
                <!-- ═══════════════════════════════════════════════════════
                     🔌 INTEGRATION POINT — Username
                     Replace "User" with authenticated user's name/email.
                     e.g. st.session_state.get("user_name", "User")
                     ═══════════════════════════════════════════════════════ -->
                👋 Hi, User
            </p>
            <p class="title-panel-date">{datetime.date.today().strftime('%d %B %Y')}</p>
            <p class="privacy-badge">🔒 Data stays on this device</p>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ─────────────────────────────────────────────────────────────────────────────
# Main 3-column layout
#
# Left column:  two stacked panels (docs + reports) — heights sum to PANEL_HEIGHT
# Center column: single chat panel — height = PANEL_HEIGHT
# Right column:  single HITL panel — height = PANEL_HEIGHT
# ─────────────────────────────────────────────────────────────────────────────
col_left, col_center, col_right = st.columns([1, 2, 1])

with col_left:
    render_docs_panel(height=DOC_PANEL_HEIGHT)
    render_reports_panel(height=REPORTS_PANEL_HEIGHT)

with col_center:
    render_chat_panel(height=PANEL_HEIGHT)

with col_right:
    render_hitl_panel(height=PANEL_HEIGHT)
