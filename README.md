# flightdeals

A personal flight-deal watcher. You tell it a route, your travel dates (fixed or a flexible range),
and a max price — it checks Google Flights on a schedule and emails you when a **non-stop,
carry-on** fare drops under your target. No always-on server: it runs free as a GitHub Actions cron
job. This is also a hands-on web-scraping learning project, built one phase at a time.

> DISCLAIMER: Scraping Google Flights is against Google's ToS. I'm using this for personal use only.

## How it works

Rather than hitting a flights API, we drive a real browser. Playwright launches Chromium and walks
through Google Flights like a person would: fill in the origin, destination, and dates, click the
Stops and Bags filters, then read the results off the page. It returns the cheapest non-stop,
carry-on itinerary for the date pair you asked for.

(Google Flights randomizes its CSS class names and swaps UI elements on interaction, so the scraper
targets stable roles and aria-labels instead of brittle selectors.)

## Usage

```bash
uv sync                              # install dependencies
uv run playwright install chromium   # one-time: fetch the browser

uv run flightdeals \
    --from SFO --to YYZ --depart 2026-09-01 --return 2026-09-12 [--headed] [--debug]
```

- `--from` / `--to` — airport codes
- `--depart` / `--return` — dates (`YYYY-MM-DD`)
- `--headed` — show the browser window instead of running headless
- `--debug` — dump a screenshot + HTML on failure

## Roadmap

The scraper core above is the first piece. Still to come: flexible date-range search, SQLite +
CLI to manage watched routes, and email alerts with dedup on a scheduled GitHub Actions cron.
