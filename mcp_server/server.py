"""
MCP server bootstrap using the official MCP Python SDK (FastMCP).
OpenAI client libraries can attach via stdio (local) or SSE (Docker/network).
"""

from __future__ import annotations

import os

from mcp.server.fastmcp import FastMCP

from mcp_server.tools.bank_parser import extract_tables_from_pdf
from mcp_server.tools.browser_tools import connect_cdp_session
from mcp_server.tools.pii_scrubber import scrub_text
from mcp_server.tools.tax_rag import query_tax_law

_host = os.environ.get("MCP_HOST", "127.0.0.1")
_port = int(os.environ.get("MCP_PORT", "8000"))

mcp = FastMCP("Naija Tax MCP", host=_host, port=_port)


@mcp.tool()
def scrub_pii(text: str) -> str:
    """Mask BVN and NUBAN-like digit sequences in user-supplied text."""
    return scrub_text(text)


@mcp.tool()
def parse_bank_pdf(pdf_path: str) -> dict:
    """Extract tables (Camelot) or page text (PyMuPDF) from a bank statement PDF."""
    return extract_tables_from_pdf(pdf_path)


@mcp.tool()
def query_nigerian_tax_law(query: str, top_k: int = 5) -> dict:
    """Retrieve Nigerian Finance Act snippets relevant to the query (Chroma when configured)."""
    return query_tax_law(query, top_k=top_k)


@mcp.tool()
def attach_chrome_cdp(cdp_http_url: str) -> dict:
    """Attach to Chrome via CDP HTTP endpoint (e.g. http://127.0.0.1:9222). Stub until Playwright is wired."""
    return connect_cdp_session(cdp_http_url)


def main() -> None:
    transport = os.environ.get("MCP_TRANSPORT", "sse")
    if transport == "stdio":
        mcp.run(transport="stdio")
    else:
        # Host/port are set on FastMCP via MCP_HOST / MCP_PORT (use 0.0.0.0 in Docker).
        mcp.run(transport="sse")


if __name__ == "__main__":
    main()
