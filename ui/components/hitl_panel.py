"""Right panel: Human-in-the-Loop verification cards."""

from __future__ import annotations

import streamlit as st

from ui import api_client


def render_hitl_panel(height: int = 640) -> None:
    """Render the full HITL panel inside a fixed-height scrollable container.

    Args:
        height: Panel height in pixels — must match PANEL_HEIGHT from app.py
                so all three columns are the same height.
    """
    with st.container(height=height, border=True):
        _render_status_pane()

        if not st.session_state.hitl_pending:
            st.caption("No pending verifications.")
            return

        items: list[dict] = st.session_state.hitl_items
        if items:
            _render_hitl_card(items[0])
        else:
            _render_final_approval_card()


# ─────────────────────────────────────────────────────────────────────────────
# Status pane — card count traffic-light indicator
# ─────────────────────────────────────────────────────────────────────────────

def _render_status_pane() -> None:
    count = len(st.session_state.hitl_items)

    if not st.session_state.hitl_pending:
        st.markdown(
            "<p class='panel-section-label'>🔍 Verification Panel</p>",
            unsafe_allow_html=True,
        )
        return

    if count < 3:
        st.success(f"● FINE — {count} item(s) remaining")
    elif count <= 5:
        st.warning(f"● CONCERNING — {count} items remaining")
    else:
        st.error(f"● HIGH — {count} items remaining")


# ─────────────────────────────────────────────────────────────────────────────
# Single HITL card — one item at a time
# ─────────────────────────────────────────────────────────────────────────────

def _render_hitl_card(item: dict) -> None:
    """Show the current verification item with text-reply and doc-upload tabs."""
    total = len(st.session_state.hitl_items) + len(st.session_state.hitl_payload)
    current = total - len(st.session_state.hitl_items) + 1

    with st.container(border=True):
        st.markdown(f"**Item {current} of {total}**")
        st.markdown(f"### {item['label']}")
        st.markdown(
            f"I calculated **₦{item['amount_ngn']:,.2f}** based on your statement. "
            "Confirm or correct the value below."
        )
        if item.get("basis"):
            st.caption(f"📖 Basis: {item['basis']}")

        st.divider()

        tab_text, tab_doc = st.tabs(["✏️ Text reply", "📎 Upload supporting doc"])

        with tab_text:
            edit_val = st.text_input(
                "Amount (₦)",
                value=str(item["amount_ngn"]),
                key=f"hitl_edit_{current}",
                placeholder="Enter confirmed amount",
            )
            if st.button("✅ Confirm", key=f"confirm_{current}", use_container_width=True, type="primary"):
                _confirm_item(item, edit_val)

        with tab_doc:
            doc = st.file_uploader(
                "Upload supporting document",
                type=["pdf", "jpg", "png"],
                key=f"hitl_doc_{current}",
                label_visibility="collapsed",
            )
            if st.button("📤 Submit with document", key=f"submit_doc_{current}", use_container_width=True):
                doc_name = doc.name if doc else None
                _confirm_item(item, str(item["amount_ngn"]), supporting_doc=doc_name)


def _confirm_item(item: dict, raw_value: str, supporting_doc: str | None = None) -> None:
    """Validate the entered value, store in payload, advance the queue."""
    try:
        amount = float(raw_value.replace(",", "").replace("₦", "").strip())
    except ValueError:
        st.error("Please enter a valid number.")
        return

    entry: dict = {"amount": amount}
    if supporting_doc:
        entry["supporting_doc"] = supporting_doc

    st.session_state.hitl_payload[item["label"]] = entry

    # Echo confirmation into the chat history so there's a full audit trail
    st.session_state.messages.append({
        "role": "assistant",
        "content": f"✅ HITL confirmed: **{item['label']}** set to ₦{amount:,.2f}.",
    })

    st.session_state.hitl_items = st.session_state.hitl_items[1:]
    st.rerun()


# ─────────────────────────────────────────────────────────────────────────────
# Final approval card — shown after all items are confirmed
# ─────────────────────────────────────────────────────────────────────────────

def _render_final_approval_card() -> None:
    with st.container(border=True):
        st.markdown("### ✅ All items verified")
        st.markdown("Review the confirmed figures below, then approve to submit your filing.")

        rows = []
        for label, entry in st.session_state.hitl_payload.items():
            amount = entry.get("amount", 0) if isinstance(entry, dict) else entry
            rows.append({"Item": label, "Amount (₦)": f"₦{amount:,.2f}"})

        if rows:
            import pandas as pd  # pandas ships as a transitive dep of streamlit
            st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)

        st.divider()
        col_approve, col_cancel = st.columns(2)

        if col_approve.button("🚀 Approve Final Filing", use_container_width=True, type="primary"):
            _approve_filing()

        if col_cancel.button("❌ Cancel", use_container_width=True):
            _cancel_filing()


def _approve_filing() -> None:
    flat_payload = {
        label: (entry.get("amount", 0) if isinstance(entry, dict) else entry)
        for label, entry in st.session_state.hitl_payload.items()
    }

    # ═════════════════════════════════════════════════════════════════════════
    # 🔌 INTEGRATION POINT — Final submission to LangGraph / FIRS portal
    #
    # Currently:  generates a local receipt text file only.
    # To wire up: before generating the receipt, call the LangGraph Sidekick
    #             node to perform the actual portal submission:
    #
    #   response = api_client.call_langgraph_invoke("confirm filing")
    #
    #   The Sidekick node (agentic_core/nodes/sidekick_node.py) should:
    #     1. Use the MCP attach_chrome_cdp tool to open a browser session
    #     2. Navigate to the FIRS/LIRS portal
    #     3. Fill fields using flat_payload values
    #     4. Return the official reference number in filing_payload["ref"]
    #
    #   Once the Sidekick node is implemented, replace the hardcoded
    #   "latest" reference below with:
    #     ref = response.get("filing_payload", {}).get("ref", "PENDING")
    # ═════════════════════════════════════════════════════════════════════════
    receipt_bytes = api_client.generate_filing_receipt_report(flat_payload)
    st.session_state.output_reports.append({
        "label": "Filing Receipt",
        "filename": "filing_receipt_latest.txt",
        "bytes": receipt_bytes,
    })

    st.session_state.messages.append({
        "role": "assistant",
        "content": "🎉 Filing approved and submitted! Your receipt has been added to the **Reports** panel on the left.",
    })
    st.session_state.hitl_pending = False
    st.session_state.hitl_items = []
    st.rerun()


def _cancel_filing() -> None:
    st.session_state.messages.append({
        "role": "assistant",
        "content": "Filing cancelled. You can restart the verification process at any time.",
    })
    st.session_state.hitl_pending = False
    st.session_state.hitl_items = []
    st.session_state.hitl_payload = {}
    st.rerun()
