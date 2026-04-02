from mcp.server.fastmcp import FastMCP

from mcp_server.tools.bank_parser import extract_tables_from_pdf, parse_and_scrub as parse_and_scrub_impl
from mcp_server.tools.browser_tools import (
    connect_cdp_session,
    dynamic_inject as dynamic_inject_impl,
    launch_firs_portal as launch_firs_portal_impl,
    map_active_form as map_active_form_impl,
)
from mcp_server.tools.pii_scrubber import scrub_text
from mcp_server.tools.tax_rag import query_tax_law
from utils.config import MCP_HOST, MCP_PORT, MCP_TRANSPORT

_host = MCP_HOST
_port = int(MCP_PORT)

mcp = FastMCP("Naija Tax MCP", host=_host, port=_port)


@mcp.tool()
def scrub_pii(text: str) -> str:
    """Mask BVN and NUBAN-like digit sequences in user-supplied text."""
    return scrub_text(text)


@mcp.tool()
async def parse_bank_pdf(pdf_path: str) -> dict:
    """Extract tables (Camelot) or page text (PyMuPDF) from a bank statement PDF."""
    return await extract_tables_from_pdf(pdf_path)


@mcp.tool()
async def parse_and_scrub(pdf_path: str) -> dict:
    """Extract text from a bank PDF and return regex-scrubbed content (BVN, NUBAN, phones, email)."""
    return await parse_and_scrub_impl(pdf_path)


@mcp.tool()
def query_nigerian_tax_law(query: str, top_k: int = 5) -> dict:
    """Retrieve Nigerian Finance Act snippets relevant to the query (Chroma when configured)."""
    return query_tax_law(query, top_k=top_k)


@mcp.tool()
def attach_chrome_cdp(cdp_http_url: str) -> dict:
    """Attach to Chrome via CDP HTTP endpoint (e.g. http://127.0.0.1:9222). Stub until Playwright is wired."""
    return connect_cdp_session(cdp_http_url)


@mcp.tool()
def launch_firs_portal(url: str | None = None) -> dict:
    """Launch visible Google Chrome to FIRS TaxPromax; session is kept for map_active_form / dynamic_inject."""
    return launch_firs_portal_impl(url=url)


@mcp.tool()
def map_active_form() -> dict:
    """Semantic DOM map of visible input, select, textarea, and button controls (labels + CSS selectors)."""
    return map_active_form_impl()


@mcp.tool()
def dynamic_inject(selector: str, value: str) -> dict:
    """Set a field value by CSS selector and highlight it in light green for the user."""
    return dynamic_inject_impl(selector, value)


def main() -> None:
    if MCP_TRANSPORT == "stdio":
        mcp.run(transport=MCP_TRANSPORT)
    else:
        # Host/port are set on FastMCP via MCP_HOST / MCP_PORT (use 0.0.0.0 in Docker).
        mcp.run(transport="sse")


if __name__ == "__main__":
    main()
