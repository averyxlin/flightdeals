"""Tunable constants for the Google Flights scraper."""

from __future__ import annotations

# Google Flights, forced to English + USD so the aria-label parser sees the
# text/currency it expects.
FLIGHTS_URL = "https://www.google.com/travel/flights?hl=en&curr=USD"

# Generous but bounded waits — results are async and the network varies.
RESULTS_TIMEOUT_MS = 30_000
STEP_TIMEOUT_MS = 15_000

# A flight result row. The full fare description lives in the row div's
# aria-label (e.g. "From 357 US dollars round trip total. Nonstop flight with
# ..."). We key on "round trip total" because the bare "N US dollars" string
# also appears on inner price <span>s; matching the attribute (not visible
# text) sidesteps Google's randomized class names.
FLIGHT_ROW = '[aria-label*="round trip total"]'
