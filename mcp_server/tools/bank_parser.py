"""PyMuPDF + Camelot helpers for table extraction from bank PDFs."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import fitz  # PyMuPDF

from utils.exceptions import TableExtractionError, UnreadablePDFError


def _text_fallback(path: Path) -> list[dict[str, Any]]:
    """Extract plain text per page when table libraries fail."""
    doc = fitz.open(path)
    try:
        pages: list[dict[str, Any]] = []
        for i in range(len(doc)):
            pages.append({"page": i + 1, "text": doc.load_page(i).get_text()})
        return pages
    finally:
        doc.close()


def extract_tables_from_pdf(pdf_path: str) -> dict[str, Any]:
    """
    Try Camelot lattice/stream for tables; fall back to PyMuPDF text per page.
    """
    path = Path(pdf_path)
    if not path.is_file():
        raise UnreadablePDFError(f"File not found: {pdf_path}")

    try:
        import camelot  # lazy: heavy dependency
    except ImportError as e:
        return {
            "source": "pymupdf",
            "tables": [],
            "pages": _text_fallback(path),
            "note": f"Camelot unavailable: {e}",
        }

    tables_out: list[dict[str, Any]] = []
    try:
        for flavor in ("lattice", "stream"):
            try:
                tables = camelot.read_pdf(str(path), pages="all", flavor=flavor)
                for t in tables:
                    tables_out.append(
                        {
                            "flavor": flavor,
                            "page": int(t.page),
                            "shape": getattr(t, "shape", None),
                            "data": t.df.to_dict(orient="records"),
                        }
                    )
                if tables_out:
                    break
            except Exception:
                continue
    except Exception as exc:
        raise TableExtractionError(str(exc)) from exc

    if not tables_out:
        return {
            "source": "pymupdf_fallback",
            "tables": [],
            "pages": _text_fallback(path),
        }

    return {"source": "camelot", "tables": tables_out}
