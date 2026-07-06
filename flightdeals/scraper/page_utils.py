"""Incidental Playwright page/browser helpers.

These aren't part of the form or extraction logic proper — they're supporting
utilities (waiting for the page to settle, dumping diagnostics) kept out of the
classes so those stay focused.
"""

from __future__ import annotations

from playwright.async_api import Page, TimeoutError as PlaywrightTimeoutError

from .chromium import Chromium
from .constants import STEP_TIMEOUT_MS


async def settle(page: Page, timeout_ms: float = STEP_TIMEOUT_MS) -> None:
    """Best-effort wait for the results to re-render after an interaction.

    `networkidle` is advisory — if it never fires (long-poll connections, etc.)
    we simply proceed; the list is usually already stable.
    """
    try:
        await page.wait_for_load_state("networkidle", timeout=timeout_ms)
    except PlaywrightTimeoutError:
        pass


async def dump_debug(chromium: Chromium, tag: str, enabled: bool) -> None:
    """Save a screenshot + HTML when debugging, so selector breakage is visible."""
    if not enabled:
        return
    out = await chromium.dump(f"debug-{tag}")
    print(f"[debug] wrote debug-{tag}.png and debug-{tag}.html to {out}")
