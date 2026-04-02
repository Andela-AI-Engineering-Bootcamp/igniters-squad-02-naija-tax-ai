"""Optional LLM agent that structures bank PDFs via MCP parse_bank_pdf (not used by MCP server)."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from agents import Agent, OpenAIChatCompletionsModel, Runner, trace
from agents.mcp import MCPServerStdio, create_static_tool_filter

from models.bank_statement_models import BankStatementDocument
from utils.config import openrouter_client

PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = PROJECT_ROOT / "output"


def dump_json_file(pdf_path: Path, content: str) -> Path:
    """Store extracted structured output to JSON under ``output/``."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_path = OUTPUT_DIR / f"{pdf_path.stem}_{stamp}.json"
    out_path.write_text(content, encoding="utf-8")
    return out_path


async def bank_statement_parser_agent(pdf_path: Path) -> str:
    params = {
        "command": "uv",
        "args": ["run", "mcp_server/server.py"],
        "cwd": PROJECT_ROOT,
    }

    instructions = (
        "You parse Nigerian bank statement PDFs. Call the parse_bank_pdf tool first with the given path "
        "to obtain Camelot tables or per-page text. Then map rows into the required output schema: "
        "header fields from the statement, and every transaction line with date, description, deposit, "
        "withdrawal, and balance. Use 0.0 for deposit or withdrawal when that column is empty. "
        "Use empty strings only when a header field is not present on the document."
    )
    request = (
        "Extract a structured bank statement from this PDF. "
        f"Call parse_bank_pdf with pdf_path set to: {pdf_path.resolve()}"
    )

    model = OpenAIChatCompletionsModel(
        model="openai/gpt-4.1-mini",
        openai_client=openrouter_client(),
    )
    bank_pdf_tools = create_static_tool_filter(allowed_tool_names=["parse_bank_pdf"])
    async with MCPServerStdio(
        params=params,
        client_session_timeout_seconds=30,
        tool_filter=bank_pdf_tools,
    ) as server:
        agent = Agent(
            name="bank_statement_parser",
            instructions=instructions,
            model=model,
            mcp_servers=[server],
            output_type=BankStatementDocument,
        )
        with trace("bank_statement_parser"):
            result = await Runner.run(agent, request)
            final = result.final_output
            if isinstance(final, BankStatementDocument):
                json_str = final.model_dump_json(indent=2)
            else:
                json_str = str(final)
            dump_json_file(pdf_path, json_str)
            return "File Saved Successfully"
