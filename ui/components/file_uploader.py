"""Document handling: upload PDFs for downstream parsing (MCP tools)."""

from __future__ import annotations
import asyncio
from pathlib import Path

import streamlit as st
from utils.config import PDF_STORAGE_PATH
from utils.guardrails import validate_user_message
from mcp_server.tools.bank_parser import bank_statement_parser_agent


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
    dest = PDF_STORAGE_PATH
    dest.mkdir(parents=True, exist_ok=True)
    path = dest / uploaded.name
    path.write_bytes(uploaded.getvalue())
    with st.spinner("Running PDF agent"):
        try:
            output = asyncio.run(bank_statement_parser_agent(pdf_path=path))
        except Exception as e:
            st.warning(f"Could not run PDF agent: {e}")
        else:
            st.markdown(output)
