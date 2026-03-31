"""Main Streamlit entry: document upload, collaborative chat, graph runs."""

from __future__ import annotations

import streamlit as st

from agentic_core.graph import invoke_demo
from ui.components.chat_interface import render_chat_hitl
from ui.components.file_uploader import render_file_uploader
from utils.config import MCP_SERVER_URL, LANGGRAPH_API_URL

st.set_page_config(page_title="Naija Tax AI", layout="wide")

st.title("Naija Tax AI")
st.caption(
    "Privacy-first ingestion, tax reasoning (LangGraph), and MCP-backed tools. "
    f"MCP: `{MCP_SERVER_URL}` · "
    f"LangGraph API: `{LANGGRAPH_API_URL}`"
)

col_left, col_right = st.columns([1, 1])

with col_left:
    render_file_uploader()

with col_right:
    render_chat_hitl()

st.divider()
if st.button("Run demo graph on sample message"):
    with st.spinner("Invoking LangGraph…"):
        out = invoke_demo("Sample income and withholding for Lagos.")
    st.json(out)
