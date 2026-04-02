"""Agent C: browser copilot — launch, map, dictionary-assisted inject."""

from __future__ import annotations

import json
from typing import Any

from langchain_core.messages import AIMessage

from agentic_core.schemas import NigerianPITProfile
from agentic_core.state import NaijaTaxState
from mcp_server.tools.browser_tools import dynamic_inject, launch_firs_portal, map_active_form
from utils.paths import PIT_DICTIONARY_PATH


def _load_pit_dictionary() -> dict[str, Any]:
    raw = PIT_DICTIONARY_PATH.read_text(encoding="utf-8")
    return json.loads(raw)


def _field_value(profile: NigerianPITProfile, field: str) -> str | None:
    if not hasattr(profile, field):
        return None
    v = getattr(profile, field)
    if v is None:
        return None
    if isinstance(v, float):
        return f"{v:.2f}"
    return str(v)


def _inject_from_map(
    profile: NigerianPITProfile, form_map: list[dict[str, Any]], pit_dict: dict[str, Any]
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for ctrl in form_map:
        if ctrl.get("tag") == "button":
            continue
        label = (ctrl.get("label") or "").upper()
        sel = (ctrl.get("selector") or "").strip()
        if not sel:
            continue
        for key, meta in pit_dict.items():
            syns = [key.upper()] + [s.upper() for s in meta.get("synonyms", [])]
            if not any(s and s in label for s in syns):
                continue
            field = meta.get("profile_field")
            if not field or str(field).startswith("_"):
                break
            val = _field_value(profile, str(field))
            if val is None:
                break
            attempt = 0
            last: dict[str, Any] = {}
            while attempt < 3:
                last = dynamic_inject(sel, val)
                if last.get("status") == "ok":
                    break
                attempt += 1
                remapped = map_active_form()
                if remapped.get("status") == "ok":
                    for c2 in remapped.get("form_map") or []:
                        if (c2.get("label") or "").upper() == label and c2.get("selector"):
                            sel = c2["selector"].strip()
                            break
            out.append({"field": field, "selector": sel, "inject": last})
            break
    return out


def sidekick_launch_node(state: NaijaTaxState) -> dict[str, Any]:
    result = launch_firs_portal()
    msg = (
        "Sidekick: Chrome session started for TaxPromax. Log in manually, then resume "
        "so the agent can map and inject form fields."
        if result.get("status") not in ("error",)
        else f"Sidekick: launch reported {result.get('detail', result)}."
    )
    return {
        "filing_payload": {
            "browser_launch": result,
            "stage": "post_launch",
        },
        "hitl_pending": True,
        "messages": [AIMessage(content=msg)],
    }


def sidekick_fill_node(state: NaijaTaxState) -> dict[str, Any]:
    pit_dict = _load_pit_dictionary()
    try:
        profile = NigerianPITProfile.model_validate(state.get("clean_income_profile") or {})
    except Exception:
        profile = NigerianPITProfile()

    mapped = map_active_form()
    if mapped.get("status") != "ok":
        return {
            "filing_payload": {
                "map": mapped,
                "stage": "map_failed",
            },
            "messages": [
                AIMessage(
                    content=(
                        "Sidekick: could not read the active form — ensure the browser "
                        f"session is open. ({mapped.get('detail')})"
                    )
                )
            ],
        }

    form_map: list[dict[str, Any]] = mapped.get("form_map") or []
    injections = _inject_from_map(profile, form_map, pit_dict)

    submit_msg = (
        "Sidekick: fields filled where labels matched the PIT dictionary. "
        "Review highlights in the browser, then click the portal submit control yourself "
        "when satisfied."
    )
    return {
        "filing_payload": {
            "form_map_sample": form_map[:15],
            "injections": injections,
            "stage": "filled",
        },
        "hitl_pending": True,
        "messages": [AIMessage(content=submit_msg)],
    }
