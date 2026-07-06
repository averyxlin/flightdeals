"""Project-wide exception hierarchy.

Every error the app raises derives from `FlightDealsError`, so callers (the CLI
now, the poller later) can catch one base type. Later phases add siblings here
(e.g. storage/notify errors) rather than scattering exceptions across modules.
"""

from __future__ import annotations


class FlightDealsError(Exception):
    """Base class for all first-party errors."""


class ScrapeError(FlightDealsError):
    """A scrape could not be completed (navigation, filters, or extraction)."""


class ResultsError(ScrapeError):
    """The page never reached a scrapeable results state."""
