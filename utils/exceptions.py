"""Custom exceptions for graceful fallbacks across the stack."""


class NaijaTaxError(Exception):
    """Base error for domain-specific failures."""


class UnreadablePDFError(NaijaTaxError):
    """Raised when a PDF cannot be opened, read, or parsed as expected.
    Typical causes: Unknown file path, corrupted download, wrong file type,
    or a PDF that is encrypted or otherwise unreadable by our tools.
    """

    default_message = """
        We couldn't open or read your PDF.
        Please make sure the file is a valid, unencrypted bank statement PDF and try again."""

    def __init__(self, message: str | None = None) -> None:
        super().__init__(message if message is not None else self.default_message)


class TableExtractionError(NaijaTaxError):
    """Raised when structured table extraction (e.g. Camelot) fails.
    The PDF may still be readable as text; callers can fall back to plain
    text extraction when appropriate.
    """

    default_message = """
        We couldn't extract tables from your PDF automatically.
        The file may use an unusual layout; try a different export from your bank or contact support."""

    def __init__(self, message: str | None = None) -> None:
        super().__init__(message if message is not None else self.default_message)


class PIIScrubError(NaijaTaxError):
    """Raised when personally identifiable information cannot be masked safely.
    Processing stops so sensitive data is not sent onward by mistake.
    """

    default_message = """
        We couldn't reliably remove sensitive details from this content, 
        so we stopped to protect your privacy. Try shortening the text or removing account numbers manually."""

    def __init__(self, message: str | None = None) -> None:
        super().__init__(message if message is not None else self.default_message)
