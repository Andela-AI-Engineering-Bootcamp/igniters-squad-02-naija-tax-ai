"""Deterministic bank-statement PDF extraction (PyMuPDF / Camelot). No LLM."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import fitz
import camelot

from mcp_server.tools.pii_scrubber import scrub_text
from utils.exceptions import UnreadablePDFError


def _ensure_pdf_readable(path: Path) -> None:
    try:
        doc = fitz.open(path)
    except Exception as e:
        raise UnreadablePDFError(f"Cannot open PDF: {e}") from e
    try:
        if len(doc) == 0:
            raise UnreadablePDFError("PDF has no pages")
    finally:
        doc.close()


def text_fallback(path: Path) -> list[dict[str, Any]]:
    """Extract plain text per page when table libraries fail."""
    doc = fitz.open(path)
    try:
        pages: list[dict[str, Any]] = []
        for i in range(len(doc)):
            pages.append({"page": i + 1, "text": doc.load_page(i).get_text()})
        return pages
    finally:
        doc.close()


def _flatten_extracted_to_text(extracted: dict[str, Any]) -> str:
    tables = extracted.get("tables") or []
    if tables:
        lines: list[str] = []
        for t in tables:
            for row in t.get("data") or []:
                if isinstance(row, dict):
                    cells = [
                        str(v)
                        for v in row.values()
                        if v is not None and str(v).strip()
                    ]
                else:
                    cells = [str(row)]
                lines.append(" ".join(cells))
        return "\n".join(lines)
    pages = extracted.get("pages") or []
    return "\n\n".join(p.get("text", "") for p in pages)


def _page_count_from_extracted(extracted: dict[str, Any]) -> int:
    pages = extracted.get("pages") or []
    if pages:
        return len(pages)
    tables = extracted.get("tables") or []
    if tables:
        return max(int(t.get("page", 1)) for t in tables)
    return 0


async def extract_tables_from_pdf(pdf_path: str) -> dict[str, Any]:
    """Extract tables via Camelot, or per-page text via PyMuPDF when no tables."""
    path = Path(pdf_path)
    if not path.is_file():
        raise UnreadablePDFError(f"File not found: {pdf_path}")

    _ensure_pdf_readable(path)

    tables_out: list[dict[str, Any]] = []
    try:
        tables = camelot.read_pdf(str(path), pages="all")
        for t in tables:
            tables_out.append(
                {
                    "page": int(t.page),
                    "shape": getattr(t, "shape", None),
                    "data": t.df.to_dict(orient="records"),
                }
            )
    except Exception:
        tables_out = []

    if not tables_out:
        return {
            "source": "pymupdf_fallback",
            "tables": [],
            "pages": text_fallback(path),
        }

    return {"source": "camelot", "tables": tables_out}


async def parse_and_scrub(pdf_path: str) -> dict[str, Any]:
    """
    Extract text from a bank-statement PDF and mask PII (regex only).

    Returns a JSON-serializable dict; does not raise for invalid PDFs (MCP-safe).
    """
    path = Path((pdf_path or "").strip())
    if not path.is_file():
        return {
            "status": "error",
            "error": "unreadable_pdf",
            "detail": f"File not found: {pdf_path}",
        }

    try:
        extracted = await extract_tables_from_pdf(pdf_path)
    except UnreadablePDFError as e:
        return {
            "status": "error",
            "error": "unreadable_pdf",
            "detail": str(e),
        }

    raw = _flatten_extracted_to_text(extracted)
    scrubbed = scrub_text(raw)
    return {
        "status": "ok",
        "scrubbed_text": scrubbed,
        "source": extracted.get("source", "unknown"),
        "page_count": _page_count_from_extracted(extracted),
    }
