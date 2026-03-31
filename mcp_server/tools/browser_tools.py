"""Playwright + Chrome DevTools Protocol helpers (to be wired)."""

from __future__ import annotations

from typing import Any


def connect_cdp_session(cdp_http_url: str) -> dict[str, Any]:
    """
    Attach to a user-launched Chrome instance via CDP (e.g. http://127.0.0.1:9222).

    When implemented, this should validate the endpoint and return session metadata.
    """
    url = (cdp_http_url or "").strip()
    if not url:
        return {
            "status": "invalid",
            "detail": "cdp_http_url is required (e.g. http://127.0.0.1:9222).",
        }
    return {
        "status": "not_configured",
        "detail": "Playwright CDP attach is not implemented yet.",
        "cdp_http_url": url,
    }


def describe_active_page() -> dict[str, Any]:
    """Return a minimal snapshot of the active browser page (title, URL) once CDP is wired."""
    return {
        "status": "not_configured",
        "detail": "No active CDP session; browser_tools not wired yet.",
    }
