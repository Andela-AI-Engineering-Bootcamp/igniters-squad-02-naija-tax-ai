"""PII extraction (Ollama) plus deterministic masking in free text."""

from __future__ import annotations

import re

from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import ChatOllama
from utils.scrubber import PIIData, PIIScrubber, _NUBAN, _BVN, _EMAIL, _mask_known_values, _nonempty_pii_values



def scrub_text(text: str, mask: str = "***") -> str:
    if not text:
        return text
    out = _BVN.sub(mask, text)
    out = _NUBAN.sub(mask, out)
    out = _EMAIL.sub(mask, out)

    return out


def extract_pii_with_ollama(
    text: str,
    *,
    model: str = "llama3.2",
    base_url: str | None = None,
    temperature: float = 0.0,
    mask: str = "***",
) -> PIIScrubber:
    llm = ChatOllama(
        model=model,
        temperature=temperature,
        **({"base_url": base_url} if base_url else {}),
    )
    structured = llm.with_structured_output(PIIScrubber)
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "You are a privacy assistant for Nigerian user text.\n"
                "1) Copy into pii_data only values that clearly appear in the message. "
                "Use an empty string for any field that is not present. Do not invent data.\n"
                "2) bvn: 11-digit Bank Verification Number. nuban: 10-digit account number when "
                "labeled or clearly a bank account. phone_number: Nigerian or international "
                "mobile as written (you may normalize to digits in the value). "
                "address / town: postal or street location if stated.\n"
                "3) scrubbed_text: rewrite the user message so that every substring you placed "
                "in pii_data is removed or replaced by the literal token ***; keep other words "
                "and punctuation natural. If unsure, still fill pii_data accurately — "
                "downstream code will enforce redaction.\n"
                "4) Return valid JSON matching the schema only.",
            ),
            ("human", "{text}"),
        ]
    )
    chain = prompt | structured
    raw: PIIScrubber = chain.invoke({"text": text})
    merged = PIIData.model_validate(
        {**PIIData().model_dump(), **raw.pii_data.model_dump()}
    )
    scrubbed = _mask_known_values(text, _nonempty_pii_values(merged), mask)
    scrubbed = scrub_text(scrubbed, mask=mask)
    return PIIScrubber(scrubbed_text=scrubbed.strip(), pii_data=merged)


if __name__ == "__main__":
    _sample = (
        "Reach me on 08031234567, BVN 12345678901. My NUBAN is 1234567890. "
        "My address is Ikeja City Mall, Lagos"
    )
    result = extract_pii_with_ollama(_sample)
    assert "08031234567" not in result.scrubbed_text
    assert "12345678901" not in result.scrubbed_text
    assert "1234567890" not in result.scrubbed_text
    assert "Ikeja" not in result.scrubbed_text
    print(result)