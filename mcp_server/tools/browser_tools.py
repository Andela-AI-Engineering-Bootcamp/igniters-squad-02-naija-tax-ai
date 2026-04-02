"""Playwright + Chrome DevTools Protocol helpers."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from playwright.sync_api import BrowserContext, Page, Playwright, sync_playwright

_playwright: Playwright | None = None
_context: BrowserContext | None = None
_page: Page | None = None

DEFAULT_FIRS_TAXPROMAX_URL = "https://taxpromax.firs.gov.ng/"

# DOM scan for map_active_form: visible interactive controls (input, select, textarea, button).
_MAP_ACTIVE_FORM_JS = r"""() => {
  function visible(el) {
    if (!el || el.disabled) return false;
    const st = window.getComputedStyle(el);
    if (st.display === "none" || st.visibility === "hidden" || parseFloat(st.opacity) === 0)
      return false;
    const r = el.getBoundingClientRect();
    if (r.width <= 0 || r.height <= 0) return false;
    if (el.tagName === "INPUT" && el.type === "hidden") return false;
    return true;
  }
  function labelText(el) {
    if (el.labels && el.labels.length > 0)
      return (el.labels[0].textContent || "").trim().replace(/\s+/g, " ");
    if (el.id) {
      try {
        const lb = document.querySelector('label[for="' + CSS.escape(el.id) + '"]');
        if (lb) return (lb.textContent || "").trim().replace(/\s+/g, " ");
      } catch (e) {}
    }
    const al = el.getAttribute("aria-labelledby");
    if (al) {
      const parts = al.split(/\s+/).map(function(id) {
        const n = document.getElementById(id);
        return n ? (n.textContent || "").trim() : "";
      }).filter(Boolean);
      if (parts.length) return parts.join(" ");
    }
    const aria = el.getAttribute("aria-label");
    if (aria) return aria.trim();
    if (el.placeholder) return el.placeholder.trim();
    let p = el.parentElement;
    while (p) {
      if (p.tagName === "LABEL") return (p.textContent || "").trim().replace(/\s+/g, " ");
      p = p.parentElement;
    }
    return "";
  }
  function cssSelector(el) {
    if (el.id) {
      try {
        const idSel = "#" + CSS.escape(el.id);
        if (document.querySelectorAll(idSel).length === 1) return idSel;
      } catch (e) {}
    }
    const nm = el.getAttribute("name");
    if (nm) {
      const esc = nm.replace(/\\/g, "\\\\").replace(/"/g, '\\"');
      const sel = '[name="' + esc + '"]';
      const nodes = document.querySelectorAll(sel);
      if (nodes.length === 1) return sel;
      const tag = el.tagName.toLowerCase();
      const same = Array.prototype.filter.call(nodes, function(n) {
        return n.tagName === el.tagName;
      });
      if (same.length === 1) return tag + sel;
    }
    const tag = el.tagName.toLowerCase();
    const parent = el.parentElement;
    if (!parent) return tag;
    const siblings = Array.prototype.filter.call(parent.children, function(c) {
      return c.tagName === el.tagName;
    });
    const idx = siblings.indexOf(el) + 1;
    return tag + ":nth-of-type(" + idx + ")";
  }
  const out = [];
  document.querySelectorAll("input, select, textarea, button").forEach(function(el) {
    if (!visible(el)) return;
    const tn = el.tagName;
    var tagOut;
    var typeOut;
    if (tn === "SELECT") {
      tagOut = "select";
      typeOut = "select";
    } else if (tn === "TEXTAREA") {
      tagOut = "textarea";
      typeOut = "textarea";
    } else if (tn === "BUTTON") {
      tagOut = "button";
      typeOut = (el.getAttribute("type") || "submit").toLowerCase();
    } else if (tn === "INPUT") {
      tagOut = "input";
      typeOut = (el.type || "text").toLowerCase();
    } else {
      return;
    }
    out.push({
      tag: tagOut,
      type: typeOut,
      id: el.id || "",
      name: el.getAttribute("name") || "",
      label: labelText(el),
      selector: cssSelector(el)
    });
  });
  return out;
}"""


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


def map_active_form() -> dict[str, Any]:
    """
    Scan the active page for visible interactive controls (``input``, ``select``,
    ``textarea``, ``button``), pair labels, and return ``form_map`` plus minified JSON.
    """
    page = get_active_page()
    if page is None:
        return {
            "status": "error",
            "detail": "No active browser session; call launch_firs_portal first.",
        }
    try:
        raw: Any = page.evaluate(_MAP_ACTIVE_FORM_JS)
        form_map: list[dict[str, Any]] = raw if isinstance(raw, list) else []
        form_map_json = json.dumps(form_map, ensure_ascii=False, separators=(",", ":"))
        return {
            "status": "ok",
            "form_map": form_map,
            "form_map_json": form_map_json,
        }
    except Exception as e:
        return {"status": "error", "detail": str(e)}


def dynamic_inject(selector: str, value: str) -> dict[str, Any]:
    """
    Fill a field on the active page and highlight it (``#e8f5e9``).

    Uses ``page.locator(selector).first`` — prefer unique selectors from
    :func:`map_active_form`.
    """
    page = get_active_page()
    if page is None:
        return {
            "status": "error",
            "detail": "No active browser session; call launch_firs_portal first.",
        }
    sel = (selector or "").strip()
    if not sel:
        return {"status": "invalid", "detail": "selector is required."}

    try:
        loc = page.locator(sel).first
        loc.wait_for(state="attached", timeout=10_000)
        tag = loc.evaluate("el => el.tagName.toLowerCase()")
        inp_type = ""
        if tag == "input":
            inp_type = loc.evaluate("el => (el.type || 'text').toLowerCase()")

        if tag == "input" and inp_type == "file":
            return {
                "status": "error",
                "detail": "file inputs are not supported.",
            }

        if tag == "select":
            try:
                loc.select_option(value=value, timeout=5_000)
            except Exception:
                loc.select_option(label=value, timeout=5_000)
        elif tag == "input" and inp_type in ("checkbox", "radio"):
            v = value.strip().lower()
            checked = v in ("true", "1", "yes", "on", "checked")
            loc.set_checked(checked)
        elif tag == "button":
            loc.evaluate(
                """(el, v) => {
                  el.textContent = v;
                }""",
                value,
            )
        elif tag == "input" and inp_type in ("button", "submit", "reset", "image"):
            loc.fill(value)
        else:
            loc.fill(value)

        loc.evaluate(
            """el => {
              el.style.backgroundColor = '#e8f5e9';
              el.style.outline = '2px solid #81c784';
            }"""
        )
        return {
            "status": "ok",
            "detail": "Value set and field highlighted.",
            "selector": sel,
        }
    except Exception as e:
        return {"status": "error", "detail": str(e)}
