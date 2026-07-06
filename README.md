# flightdeals

Scrape Google Flights for the cheapest **non-stop, carry-on** fares and (eventually) email when a
deal drops under a target price. Built one phase at a time as a web-scraping learning exercise.

> Scraping Google Flights is against Google's ToS — keep this personal-use and low-volume.

## Phase 1 — scraper core (done)

Playwright drives a real Chromium through Google Flights (fill the form, click the Stops/Bags
filters, read the results), returning the cheapest nonstop carry-on itinerary for a date pair.

```bash
uv sync
uv run playwright install chromium
uv run python -m flightdeals.scraper.scraper \
    --from SFO --to YYZ --depart 2026-09-01 --return 2026-09-12 [--headed] [--debug]
```

`--headed` shows the browser; `--debug` dumps a screenshot + HTML on failure.

Later phases: date-range search, SQLite + CLI, email/dedup + scheduled runs.
