"""The Google Flights search form + results-filter interactions.

`SearchForm` is everything we *do* to the page: dismiss consent, fill the
airports and dates, submit, wait for results, and toggle the Stops/Bags filters.
Extraction of the rendered results lives separately in `extract.py`.

Selectors are accessibility-first (`get_by_role`/`get_by_text`) because Google
Flights randomizes its CSS class names.
"""

from __future__ import annotations

from datetime import date

from playwright.async_api import Page, TimeoutError as PlaywrightTimeoutError

from ..errors import ResultsError
from .constants import FLIGHT_ROW, RESULTS_TIMEOUT_MS, STEP_TIMEOUT_MS
from .page_utils import settle


class SearchForm:
    """Drives the search form and result-page filters for one `page`."""

    def __init__(self, page: Page) -> None:
        self.page = page

    # -- public flow -------------------------------------------------------

    async def dismiss_consent(self) -> None:
        """Google may interstitial a cookie/consent page; accept if present."""
        try:
            await self.page.get_by_role("button", name="Accept all").click(timeout=4_000)
        except PlaywrightTimeoutError:
            pass  # no consent gate this time — fine.

    async def fill_info(self, origin: str, dest: str, depart: date, ret: date) -> None:
        """Fill the whole search form: origin, destination, and both dates."""
        await self._fill_airport("Where from", origin)
        await self._fill_airport("Where to", dest)
        await self._fill_dates(depart, ret)

    async def submit(self) -> None:
        """Click Search and confirm the results page navigation actually happened.

        A Search click that lands too soon after the calendar closes silently
        fails to navigate, so we verify the URL and retry once.
        """
        for _ in range(2):
            await self.page.get_by_role("button", name="Search").first.click()
            try:
                await self.page.wait_for_url("**/flights/search**", timeout=STEP_TIMEOUT_MS)
                return
            except PlaywrightTimeoutError:
                continue
        raise ResultsError("search did not navigate to the results page")

    async def await_results(self) -> None:
        """Block until at least one priced flight row has rendered.

        Waiting for a real result row (not just the heading) means downstream
        filtering and extraction run against loaded data. The fare text lives in
        the row's aria-label, so we match that attribute.
        """
        try:
            await self.page.locator(FLIGHT_ROW).first.wait_for(timeout=RESULTS_TIMEOUT_MS)
        except PlaywrightTimeoutError as exc:
            raise ResultsError("results list never appeared") from exc

    async def apply_filters(self, carryon: bool = True, nonstop: bool = True) -> None:
        """Apply the result-page filters that are enabled."""
        if nonstop:
            await self._apply_nonstop_filter()
        if carryon:
            await self._apply_carryon_filter()

    # -- form fields -------------------------------------------------------

    async def _fill_airport(self, label: str, code: str) -> None:
        """Type an airport code into a combobox and pick the first suggestion.

        Shared by both the origin ("Where from?") and destination ("Where to?")
        fields. Clicking either combobox makes Google swap in a focused overlay
        search input, so the original element is no longer the one you type into.
        We click to focus, then type via the keyboard (which lands in the
        overlay) and select the top suggestion.
        """
        await self.page.get_by_role("combobox", name=label).click()
        # Clicking swaps in a focused "Where else?" overlay input; wait for it so
        # our keystrokes actually land there instead of being dropped mid-animation.
        try:
            await self.page.get_by_role("combobox", name="Where else?").first.wait_for(
                state="visible", timeout=3_000
            )
        except PlaywrightTimeoutError:
            pass
        await self.page.keyboard.type(code, delay=80)
        # Wait for the autocomplete listbox, then take the top suggestion.
        option = self.page.get_by_role("option").first
        await option.wait_for(state="visible")
        await option.click()

    async def _fill_dates(self, depart: date, ret: date) -> None:
        """Pick departure and return dates from the calendar.

        Typing into the date field doesn't register; Google wants a calendar
        click. The day cells are plain divs with an accessible name like
        "Tuesday, September 1, 2026", and future months are already in the DOM,
        so Playwright auto-scrolls each cell into view before clicking.
        """
        await self.page.get_by_role("textbox", name="Departure").first.click()
        # Wait for the calendar to be fully open before picking — the Done button
        # only exists while it's open, so it's a reliable "ready" signal. Picking
        # mid-animation silently drops the departure selection.
        done = self.page.get_by_role("button", name="Done").first
        await done.wait_for(state="visible")
        await self._pick_day(depart)
        await self._pick_day(ret)
        # Close the date picker and wait for it to actually dismiss — clicking
        # Search while the calendar is still closing silently fails to navigate.
        try:
            await done.click(timeout=3_000)
            await done.wait_for(state="hidden", timeout=STEP_TIMEOUT_MS)
        except PlaywrightTimeoutError:
            pass

    async def _pick_day(self, day: date) -> None:
        """Click the calendar cell for `day` by its accessible date label.

        Waits for the cell to be visible first — the calendar animates open, and
        clicking before it's interactive silently drops the selection.
        """
        label = f"{day:%A}, {day:%B} {day.day}, {day.year}"
        cell = self.page.locator(f'[aria-label="{label}"]').first
        await cell.wait_for(state="visible")
        await cell.scroll_into_view_if_needed()
        await cell.click()

    # -- filters -----------------------------------------------------------

    async def _apply_nonstop_filter(self) -> None:
        """Open the Stops filter and choose 'Nonstop only'."""
        await self.page.get_by_role("button", name="Stops").first.click()
        await self.page.get_by_role("radio", name="Nonstop only").click()
        await self.page.keyboard.press("Escape")  # close the popover
        await settle(self.page)

    async def _apply_carryon_filter(self) -> None:
        """Open the Bags filter and set carry-on bags to 1."""
        await self.page.get_by_role("button", name="Bags").first.click()
        # The carry-on stepper exposes an "Add carry-on bag" increment control.
        await self.page.get_by_role("button", name="Add carry-on bag").click()
        await self.page.keyboard.press("Escape")  # close the popover
        await settle(self.page)
