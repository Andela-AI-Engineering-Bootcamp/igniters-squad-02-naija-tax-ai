from pydantic import BaseModel, Field
import re

_BVN = re.compile(r"\b(\d{11})\b")
_NUBAN = re.compile(r"\b(\d{10})\b")
_EMAIL = re.compile(
    r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b",
    re.IGNORECASE,
)
_ADDRESS = re.compile(r"\b([A-Za-z0-9\s]+, [A-Za-z0-9\s]+, [A-Za-z0-9\s]+)\b")


class PIIData(BaseModel):
    bvn: str = ""
    nuban: str = ""
    phone_number: str = ""
    email: str = ""
    address: str = ""
    name: str = ""
    date_of_birth: str = ""
    gender: str = ""
    nationality: str = ""
    town: str = ""


class PIIScrubber(BaseModel):
    scrubbed_text: str = Field(
        default="",
        description="User text with every identified PII substring removed or replaced.",
    )
    pii_data: PIIData


def _nonempty_pii_values(pii: PIIData) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for raw in pii.model_dump().values():
        if not isinstance(raw, str):
            continue
        v = raw.strip()
        if len(v) < 2:
            continue
        if v not in seen:
            seen.add(v)
            ordered.append(v)
    ordered.sort(key=len, reverse=True)
    return ordered


def _mask_known_values(text: str, values: list[str], mask: str) -> str:
    out = text
    for val in values:
        out = re.sub(re.escape(val), mask, out, flags=re.IGNORECASE)
    return out
