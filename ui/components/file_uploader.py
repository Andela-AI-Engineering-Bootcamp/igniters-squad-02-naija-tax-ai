"""Document handling: upload PDFs for downstream parsing (MCP tools)."""

from __future__ import annotations

from pathlib import Path

import streamlit as st

from utils.guardrails import validate_user_message


def render_file_uploader() -> None:
    st.subheader("Documents")
    uploaded = st.file_uploader("Bank statements (PDF)", type=["pdf"])
    if not uploaded:
        return
    try:
        validate_user_message(uploaded.name)
    except ValueError as e:
        st.error(str(e))
        return
    dest = Path("/tmp/naija_tax_uploads")
    dest.mkdir(parents=True, exist_ok=True)
    path = dest / uploaded.name
    path.write_bytes(uploaded.getvalue())
    st.success(f"Saved to `{path}` — call MCP `parse_bank_pdf` with this path from tooling.")
