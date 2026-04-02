"""Playwright + Chrome DevTools Protocol helpers."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from playwright.sync_api import BrowserContext, Page, Playwright, sync_playwright

_playwright: Playwright | None = None
_context: BrowserContext | None = None
_page: Page | None = None

DEFAULT_FIRS_TAXPROMAX_URL = "https://taxpromax.firs.gov.ng/"


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _persistent_profile_dir() -> Path:
    return _repo_root() / ".cache" / "firs_chrome_profile"


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


def get_active_page() -> Page | None:
    """Return the live Playwright page from :func:`launch_firs_portal`, or ``None``."""
    if _page is None or _page.is_closed():
        return None
    return _page


def close_firs_session() -> dict[str, Any]:
    """Close the persistent Chrome context and stop Playwright (releases globals)."""
    global _playwright, _context, _page

    if _context is not None:
        try:
            _context.close()
        except Exception:
            pass
    _context = None
    _page = None

    if _playwright is not None:
        try:
            _playwright.stop()
        except Exception:
            pass
    _playwright = None

    return {"status": "ok", "detail": "FIRS browser session closed."}


def launch_firs_portal(url: str | None = None) -> dict[str, Any]:
    """
    Launch visible Google Chrome (persistent context), navigate to FIRS TaxPromax.

    Stores the active :class:`~playwright.sync_api.Page` in module globals for
    :func:`describe_active_page` and later tools (form map, inject).
    """
    global _playwright, _context, _page

    target = (url or os.environ.get("FIRS_TAXPROMAX_URL") or DEFAULT_FIRS_TAXPROMAX_URL).strip()

    if _page is not None and not _page.is_closed():
        return {
            "status": "ok",
            "detail": "Browser already running.",
            "url": _page.url,
        }

    if _playwright is not None or _context is not None:
        close_firs_session()

    profile = _persistent_profile_dir()
    profile.mkdir(parents=True, exist_ok=True)

    try:
        _playwright = sync_playwright().start()
        _context = _playwright.chromium.launch_persistent_context(
            str(profile),
            headless=False,
            channel="chrome",
            viewport={"width": 1920, "height": 1080}
        )
        _page = _context.pages[0] if _context.pages else _context.new_page()
        _page.goto(target, wait_until="domcontentloaded")
        return {
            "status": "ok",
            "detail": "Launched Chrome and navigated to TaxPromax.",
            "url": _page.url,
        }
    except Exception as e:
        close_firs_session()
        return {
            "status": "error",
            "detail": str(e),
            "url": target,
        }


def describe_active_page() -> dict[str, Any]:
    """Return title and URL of the page launched by :func:`launch_firs_portal`."""
    if _page is None or _page.is_closed():
        return {
            "status": "not_configured",
            "detail": "No active browser session; call launch_firs_portal first.",
        }
    try:
        return {
            "status": "ok",
            "title": _page.title(),
            "url": _page.url,
        }
    except Exception as e:
        return {"status": "error", "detail": str(e)}
