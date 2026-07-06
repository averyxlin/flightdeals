"""Chromium session management — the browser lifecycle, isolated from scraping.

`Chromium` owns everything Playwright: starting the driver, launching the
browser, creating a context/page, and tearing it all down. The `Scraper` holds
one of these and stays focused on *what* to scrape, not *how* the browser is
run. Swapping engines or launch options later touches only this file.
"""

from __future__ import annotations

from pathlib import Path

from playwright.async_api import Browser, Page, Playwright, async_playwright


class Chromium:
    """An async-context-managed Chromium browser with a single ready `page`.

        async with Chromium(headless=False) as browser:
            await browser.page.goto(...)
    """

    def __init__(self, headless: bool = True) -> None:
        self.headless = headless
        self._pw: Playwright | None = None
        self._browser: Browser | None = None
        self._page: Page | None = None

    async def __aenter__(self) -> "Chromium":
        self._pw = await async_playwright().start()
        self._browser = await self._pw.chromium.launch(headless=self.headless)
        # A realistic locale keeps prices in USD and text in English, which the
        # aria-label parser depends on.
        context = await self._browser.new_context(locale="en-US")
        self._page = await context.new_page()
        return self

    async def __aexit__(self, *exc) -> None:
        if self._browser is not None:
            await self._browser.close()
        if self._pw is not None:
            await self._pw.stop()
        self._page = None
        self._browser = None
        self._pw = None

    @property
    def page(self) -> Page:
        """The live page, or raise if used outside `async with`."""
        if self._page is None:
            raise RuntimeError("Chromium must be used inside 'async with'")
        return self._page

    def set_default_timeout(self, timeout_ms: float) -> None:
        self.page.set_default_timeout(timeout_ms)

    async def dump(self, prefix: str, out_dir: Path | None = None) -> Path:
        """Save a full-page screenshot + HTML for debugging; return the directory."""
        out = out_dir or Path.cwd()
        await self.page.screenshot(path=str(out / f"{prefix}.png"), full_page=True)
        (out / f"{prefix}.html").write_text(await self.page.content(), encoding="utf-8")
        return out
