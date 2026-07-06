"""Compiled regexes for reading Google Flights `aria-label` strings.

Kept separate from `parse.py` so the parsing logic reads cleanly and the
patterns can be tuned/tested in one place as Google's wording drifts.

Reference label shape:

    "From 312 US dollars round trip total. Nonstop flight with Air Canada.
     Leaves San Francisco International Airport at 7:00 AM on Saturday,
     August 1 and arrives at Toronto Pearson International Airport at
     3:20 PM on Saturday, August 1. Total duration 5 hr 20 min. Select flight"
"""

from __future__ import annotations

import re

PRICE = re.compile(r"([\d,]+)\s+US dollars", re.IGNORECASE)
NONSTOP = re.compile(r"\bnonstop\b", re.IGNORECASE)
STOPS = re.compile(r"(\d+)\s+stop", re.IGNORECASE)
AIRLINE = re.compile(r"flight with ([^.]+?)\.", re.IGNORECASE)
DURATION = re.compile(r"total duration ([^.]+?)\.", re.IGNORECASE)
LEAVES = re.compile(r"leaves.*?at (\d{1,2}:\d{2}\s*[AP]M)", re.IGNORECASE | re.DOTALL)
ARRIVES = re.compile(r"arrives.*?at (\d{1,2}:\d{2}\s*[AP]M)", re.IGNORECASE | re.DOTALL)
TIME = re.compile(r"\d{1,2}:\d{2}\s*[AP]M", re.IGNORECASE)
