"""Collaborative HITL confirmation for filing steps."""

from __future__ import annotations

import streamlit as st

from utils.guardrails import validate_user_message


def render_chat_hitl() -> None:
    st.subheader("Chat & HITL")
    if "messages" not in st.session_state:
        st.session_state.messages = []

    for m in st.session_state.messages:
        with st.chat_message(m["role"]):
            st.markdown(m["content"])

    prompt = st.chat_input("Ask about Nigerian tax posture or confirm filing steps…")
    if not prompt:
        return
    try:
        text = validate_user_message(prompt)
    except ValueError as e:
        st.error(str(e))
        return

    st.session_state.messages.append({"role": "user", "content": text})
    with st.chat_message("user"):
        st.markdown(text)

    assistant_reply = (
        "Assistant (stub): connect OpenAI + LangGraph thread here. "
        "Use Sidekick node output for formal HITL approval UI."
    )
    st.session_state.messages.append({"role": "assistant", "content": assistant_reply})
    with st.chat_message("assistant"):
        st.markdown(assistant_reply)

    st.checkbox("I confirm filing details are accurate (HITL)", key="hitl_confirm")
