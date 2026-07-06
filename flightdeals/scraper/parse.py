"""Parse Google Flights results into `Itinerary` objects.

Google Flights renders with **obfuscated, randomized CSS class names**, so
scraping by class is hopeless. Every flight result, however, carries a rich,
stable `aria-label` (the screen-reader description) such as:

    "From 312 US dollars round trip total. Nonstop flight with Air Canada.
     Leaves San Francisco International Airport at 7:00 AM on Saturday,
     August 1 and arrives at Toronto Pearson International Airport at
     3:20 PM on Saturday, August 1. Total duration 5 hr 20 min. Select flight"

Reading that string is far more robust than any CSS/XPath. The `Parser` below is
configured once with a search's context (the query dates + booking URL, which
aren't reliably present in the label) and then turns each result's raw
`aria-label` into an `Itinerary` — fully testable without a browser.

Parsing degrades gracefully: as long as a price is present we return an
`Itinerary`, filling unmatched fields with sensible placeholders rather than
crashing on a label whose wording drifted. Compiled regexes live in
`patterns.py`; small text helpers in `utils.py`.
"""

from __future__ import annotations

from datetime import date

from . import patterns, utils
from .models import Itinerary


class Parser:
    """Turns Google Flights `aria-label` strings into `Itinerary` objects.

    Holds the per-search context (dates + booking URL) so callers only pass the
    label text for each result row.
    """

    def __init__(self, depart_date: date, return_date: date, book_url: str) -> None:
        self.depart_date = depart_date
        self.return_date = return_date
        self.book_url = book_url

    @staticmethod
    def parse_price(aria_label: str) -> int | None:
        """Extract the integer price (dollars) from an aria-label, or None."""
        m = patterns.PRICE.search(aria_label)
        if not m:
            return None
        return int(m.group(1).replace(",", ""))

    @staticmethod
    def parse_stops(aria_label: str) -> int:
        """0 for a nonstop flight, else the stated number of stops."""
        if patterns.NONSTOP.search(aria_label):
            return 0
        m = patterns.STOPS.search(aria_label)
        return int(m.group(1)) if m else 0

    def parse_result(self, aria_label: str) -> Itinerary | None:
        """Turn one result's aria-label into an `Itinerary`, or None if no price.

        A missing price means this element isn't a real flight row (headers,
        ads, "view more" tiles), so we skip it.
        """
        price = self.parse_price(aria_label)
        if price is None:
            return None

        depart_time, arrive_time = utils.extract_times(aria_label)
        return Itinerary(
            price=price,
            airline=utils.first_match(patterns.AIRLINE, aria_label, "Unknown"),
            depart_time=depart_time,
            arrive_time=arrive_time,
            duration=utils.first_match(patterns.DURATION, aria_label, "?"),
            stops=self.parse_stops(aria_label),
            depart_date=self.depart_date,
            return_date=self.return_date,
            book_url=self.book_url,
        )

    def parse_all(self, aria_labels: list[str]) -> list[Itinerary]:
        """Parse every label, dropping rows with no price."""
        parsed = (self.parse_result(label) for label in aria_labels)
        return [it for it in parsed if it is not None]

    @staticmethod
    def cheapest(itineraries: list[Itinerary]) -> Itinerary | None:
        """The lowest-priced itinerary, or None if the list is empty."""
        if not itineraries:
            return None
        return min(itineraries, key=lambda it: it.price)
