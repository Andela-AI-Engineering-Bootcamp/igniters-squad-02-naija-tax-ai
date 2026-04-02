#!/usr/bin/env python3
"""Open visible Chrome to FIRS TaxPromax for human login (Task A3)."""

from __future__ import annotations

import sys
from pathlib import Path

# Repo root on sys.path when run as `python scripts/launch_firs_portal.py`
_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from mcp_server.tools import map_active_form, close_firs_session, launch_firs_portal


def main() -> None:
    result = launch_firs_portal()
    print(result)
    if result.get("status") != "ok":
        raise SystemExit(1)

    try:
        input("Press any button to read input on the page\n")

        data = map_active_form()
        print(data)
    except Exception:
        pass

    try:
        input("Press Enter to close the browser and exit…\n")
    except EOFError:
        pass
    finally:
        print(close_firs_session())


if __name__ == "__main__":
    main()
