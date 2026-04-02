"""Repository root and shared paths."""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

PIT_DICTIONARY_PATH = REPO_ROOT / "mcp_server" / "data" / "pit_dictionary.json"
