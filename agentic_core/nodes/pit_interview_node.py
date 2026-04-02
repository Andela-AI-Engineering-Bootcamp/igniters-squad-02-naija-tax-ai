"""B7: optional reliefs interview via LangGraph interrupt."""

from __future__ import annotations

import json
from typing import Any

from langchain_core.messages import AIMessage
from langgraph.types import interrupt

from agentic_core.schemas import NigerianPITProfile
from agentic_core.state import NaijaTaxState

_RELIEF_KEYS = (
    "pension_contribution",
    "nhf_contribution",
    "nhis_premium",
    "life_assurance_premium",
)


def pit_interview_node(state: NaijaTaxState) -> dict[str, Any]:
    profile_dict = dict(state.get("clean_income_profile") or {})
    payload = interrupt(
        {
            "kind": "pit_interview",
            "message": (
                "Do you have pension, NHF, NHIS, or life assurance premiums to declare? "
                'Resume with a JSON object, e.g. '
                '{"pension_contribution": 0, "nhf_contribution": 0, '
                '"nhis_premium": 0, "life_assurance_premium": 0}'
            ),
            "fields": list(_RELIEF_KEYS),
        }
    )

    merged = dict(profile_dict)
    if isinstance(payload, dict):
        data = payload
    elif isinstance(payload, str):
        try:
            data = json.loads(payload)
        except json.JSONDecodeError:
            data = {}
    else:
        data = {}

    for k in _RELIEF_KEYS:
        if k in data:
            try:
                merged[k] = float(data[k])
            except (TypeError, ValueError):
                pass

    prof = NigerianPITProfile.model_validate(merged)
    return {
        "clean_income_profile": prof.model_dump(),
        "pit_interview_pending": False,
        "messages": [
            AIMessage(
                content="Interview: optional reliefs merged into NigerianPITProfile."
            )
        ],
    }
