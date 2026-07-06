"""Pull the raw result data out of the rendered results page.

`Extractor` is read-only: it does not interact with the form, only reads the
aria-label off each flight row. Turning those labels into `Itinerary` objects is
`Parser`'s job (parse.py) — this class just harvests the strings.
"""

from __future__ import annotations

from playwright.async_api import Page

from .constants import FLIGHT_ROW


class Extractor:
    """Reads flight-result aria-labels from a results `page`."""

    def __init__(self, page: Page) -> None:
        self.page = page

    async def collect_labels(self) -> list[str]:
        """Every result row's aria-label (the accessible fare description)."""
        # Result rows carry the fare in their aria-label, not visible text.
        items = self.page.locator(FLIGHT_ROW)
        count = await items.count()
        labels: list[str] = []
        for i in range(count):
            label = await items.nth(i).get_attribute("aria-label")
            if label:
                labels.append(label)
        return labels
