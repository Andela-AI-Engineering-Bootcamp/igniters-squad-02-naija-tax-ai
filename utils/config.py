import os
from pathlib import Path
from dotenv import load_dotenv
from openai import AsyncOpenAI

load_dotenv(override=True)
PDF_STORAGE_PATH = Path(__file__).parent.parent / "naija_tax_uploads"
MCP_SERVER_URL = os.environ.get("MCP_SERVER_URL")
LANGGRAPH_API_URL = os.environ.get("LANGGRAPH_API_URL")
MCP_HOST = os.environ.get("MCP_HOST", "127.0.0.1")
MCP_PORT = os.environ.get("MCP_PORT", "8000")
MCP_TRANSPORT = os.environ.get("MCP_TRANSPORT", "stdio")
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")
OPENROUTER_BASE_URL = os.environ.get(
    "OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"
)


def openrouter_client() -> AsyncOpenAI:
    if not OPENROUTER_API_KEY:
        raise ValueError(
            "OPENROUTER_API_KEY is required for the bank statement parser agent. "
            "Set it in your environment or .env file."
        )
    return AsyncOpenAI(
        base_url=OPENROUTER_BASE_URL.rstrip("/"),
        api_key=OPENROUTER_API_KEY,
    )
