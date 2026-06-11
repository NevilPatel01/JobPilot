"""Detect whether a job listing is eligible for Canadian applicants."""

from __future__ import annotations

import re
from typing import Optional

TARGET_COUNTRY = "CA"

CANADA_MARKERS = (
    "canada",
    "canadian",
    "🇨🇦",
    "toronto",
    "vancouver",
    "montreal",
    "montréal",
    "calgary",
    "ottawa",
    "edmonton",
    "winnipeg",
    "quebec",
    "québec",
    "ontario",
    "british columbia",
    "alberta",
    "manitoba",
    "saskatchewan",
    "nova scotia",
    "new brunswick",
    "newfoundland",
    "prince edward island",
    "mississauga",
    "brampton",
    "hamilton",
    "kitchener",
    "victoria",
    "surrey",
    "halifax",
    "gta",
    "greater toronto",
)

CANADA_PHRASES = (
    "canada only",
    "canadians only",
    "must be in canada",
    "must be located in canada",
    "based in canada",
    "located in canada",
    "work in canada",
    "work from canada",
    "eligible to work in canada",
    "legally authorized to work in canada",
    "authorized to work in canada",
    "right to work in canada",
    "remote canada",
    "canada remote",
    "anywhere in canada",
    "across canada",
    "within canada",
)

NON_CANADA_MARKERS = (
    "us only",
    "usa only",
    "u.s. only",
    "united states only",
    "worldwide",
    "anywhere in the world",
    "global remote",
    "europe only",
    "uk only",
    "emea only",
    "latam only",
    "australia only",
    "asia only",
)

GENERIC_LOCATIONS = frozenset(
    {
        "remote",
        "anywhere",
        "worldwide",
        "global",
        "international",
        "anywhere in the world",
    }
)


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower()).strip()


def detect_country(
    location: Optional[str] = None,
    description: str = "",
    title: str = "",
) -> Optional[str]:
    """Return ISO country code when the listing is Canada-focused, else None."""
    loc = _normalize(location or "")
    text = _normalize(f"{title} {description}")
    combined = f"{loc} {text}"

    has_canada_signal = any(marker in combined for marker in CANADA_MARKERS) or any(
        phrase in combined for phrase in CANADA_PHRASES
    )
    has_non_canada_signal = any(marker in combined for marker in NON_CANADA_MARKERS)

    if has_non_canada_signal and not has_canada_signal:
        return None

    if loc in GENERIC_LOCATIONS and not has_canada_signal:
        return None

    if has_canada_signal:
        return TARGET_COUNTRY

    if "california" not in loc and re.search(r"(?:^|[,\s])ca(?:$|[,\s])", loc):
        return TARGET_COUNTRY

    return None


def is_canadian_job(
    location: Optional[str] = None,
    description: str = "",
    title: str = "",
) -> bool:
    return detect_country(location=location, description=description, title=title) == TARGET_COUNTRY
