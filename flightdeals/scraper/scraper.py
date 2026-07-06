"""Google Flights scraper — the Phase 1 orchestrator.

This ties the pieces together for one search:
  - `Chromium`     — browser lifecycle (chromium.py)
  - `SearchForm`   — fill the form, submit, apply filters (form.py)
  - `Extractor`    — read result aria-labels off the page (extract.py)
  - `Parser`       — turn labels into `Itinerary` objects (parse.py)

It's the hands-on learning piece: drive a real Chromium the way a person would,
then read the results out of the rendered DOM. Run it:

    uv run python -m flightdeals.scraper.scraper \\
        --from SFO --to YYZ --depart 2026-08-01 --return 2026-08-12 --headed
"""

from __future__ import annotations

import argparse
import asyncio
from datetime import date, datetime

from playwright.async_api import Page, TimeoutError as PlaywrightTimeoutError

from ..errors import ResultsError
from .chromium import Chromium
from .constants import FLIGHTS_URL, STEP_TIMEOUT_MS
from .extract import Extractor
from .form import SearchForm
from .models import Itinerary
from .page_utils import dump_debug
from .parse import Parser


class Scraper:
    """Runs one Google Flights search end to end.

    `search()` owns the browser session (opens a `Chromium`, runs the flow, tears
    it down), so callers just:

        best = await Scraper(headless=False).search("SFO", "YYZ", dep, ret)
    """

    def __init__(self, headless: bool = True, debug: bool = False) -> None:
        self.chromium = Chromium(headless=headless)
        self.debug = debug

    @property
    def page(self) -> Page:
        return self.chromium.page

    async def search(
        self, origin: str, dest: str, depart: date, ret: date
    ) -> Itinerary | None:
        """Search and return the cheapest nonstop carry-on option (or None)."""
        async with self.chromium:
            self.chromium.set_default_timeout(STEP_TIMEOUT_MS)
            form = SearchForm(self.page)
            extractor = Extractor(self.page)
            try:
                await self.page.goto(FLIGHTS_URL, wait_until="domcontentloaded")
                await form.dismiss_consent()
                await form.fill_info(origin, dest, depart, ret)
                await form.submit()
                await form.await_results()
                await form.apply_filters(carryon=True, nonstop=True)
                labels = await extractor.collect_labels()
                booking_url = self.page.url
            except (PlaywrightTimeoutError, ResultsError) as exc:
                await dump_debug(self.chromium, "failure", self.debug)
                raise ResultsError(f"scrape failed: {exc}") from exc

            parser = Parser(depart, ret, booking_url)
            itineraries = parser.parse_all(labels)
            if not itineraries:
                await dump_debug(self.chromium, "no-results", self.debug)
            return parser.cheapest(itineraries)


def _parse_date(value: str) -> date:
    return datetime.strptime(value, "%Y-%m-%d").date()


def _build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Scrape Google Flights for the cheapest nonstop carry-on fare.")
    p.add_argument("--from", dest="origin", default="SFO", help="Origin airport code")
    p.add_argument("--to", dest="dest", default="YYZ", help="Destination airport code")
    p.add_argument("--depart", type=_parse_date, required=True, help="Departure date YYYY-MM-DD")
    p.add_argument("--return", dest="ret", type=_parse_date, required=True, help="Return date YYYY-MM-DD")
    p.add_argument("--headed", action="store_true", help="Show the browser window (great while learning)")
    p.add_argument("--debug", action="store_true", help="Dump screenshot + HTML on failure")
    return p


async def _run(args: argparse.Namespace) -> int:
    scraper = Scraper(headless=not args.headed, debug=args.debug)
    try:
        best = await scraper.search(args.origin, args.dest, args.depart, args.ret)
    except ResultsError as exc:
        print(f"No results: {exc}")
        return 1

    if best is None:
        print("No qualifying nonstop carry-on itinerary found.")
        return 1
    print(f"Cheapest {args.origin}->{args.dest}:")
    print(f"  {best.summary()}")
    print(f"  Book: {best.book_url}")
    return 0


def main() -> None:
    args = _build_arg_parser().parse_args()
    raise SystemExit(asyncio.run(_run(args)))


if __name__ == "__main__":
    main()
