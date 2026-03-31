"""Custom exceptions for graceful fallbacks across the stack."""


class NaijaTaxError(Exception):
    """Base error for domain-specific failures."""


class UnreadablePDFError(NaijaTaxError):
    """Raised when a PDF cannot be opened or parsed."""


class TableExtractionError(NaijaTaxError):
    """Raised when table extraction (Camelot/PyMuPDF) fails."""


class PIIScrubError(NaijaTaxError):
    """Raised when PII masking cannot be applied safely."""
