"""Small text-extraction helpers for parsing aria-label strings.

Kept out of `parse.py` so the `Parser` stays focused on turning a label into an
`Itinerary`, while these stay reusable, pure, and independently testable.
"""

from __future__ import annotations

import re

from . import patterns


def first_match(pattern: re.Pattern[str], text: str, default: str) -> str:
    """First capture group of `pattern` in `text`, stripped, else `default`."""
    m = pattern.search(text)
    return m.group(1).strip() if m else default


def extract_times(aria_label: str) -> tuple[str, str]:
    """(depart_time, arrive_time) from a label.

    Prefers the "Leaves ... at TIME" / "arrives ... at TIME" phrasing; falls
    back to the first two clock times found. Missing times become "?".
    """
    dep = patterns.LEAVES.search(aria_label)
    arr = patterns.ARRIVES.search(aria_label)
    if dep and arr:
        return dep.group(1).strip(), arr.group(1).strip()
    times = patterns.TIME.findall(aria_label)
    depart = times[0].strip() if len(times) >= 1 else "?"
    arrive = times[1].strip() if len(times) >= 2 else "?"
    return depart, arrive
