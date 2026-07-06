"""Data model for a scraped flight itinerary.

Kept deliberately small for Phase 1 (the scraper core). Later phases extend it
with things like fare-brand, seat/bag details, and per-leg breakdowns.
"""

from __future__ import annotations

from datetime import date

from pydantic import BaseModel


class Itinerary(BaseModel):
    """One flight option scraped from a Google Flights results list.

    Prices on the round-trip results list are the *round-trip total* for the
    cheapest matching return, which is what Google displays on the outbound
    list. `depart_time`/`arrive_time`/`duration` describe the outbound leg.
    """

    price: int
    currency: str = "USD"
    airline: str
    depart_time: str
    arrive_time: str
    duration: str
    stops: int
    depart_date: date
    return_date: date
    book_url: str

    def summary(self) -> str:
        """One-line human summary for CLI output."""
        stops = "nonstop" if self.stops == 0 else f"{self.stops} stop(s)"
        return (
            f"{self.currency} {self.price} — {self.airline} — "
            f"{self.depart_time}→{self.arrive_time} ({self.duration}, {stops}) — "
            f"{self.depart_date} to {self.return_date}"
        )
