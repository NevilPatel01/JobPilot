import re
from datetime import date, datetime, timezone
from typing import Any


PROVINCES = {
    "alberta": "AB", "ab": "AB",
    "british columbia": "BC", "bc": "BC", "b.c.": "BC",
    "manitoba": "MB", "mb": "MB",
    "new brunswick": "NB", "nb": "NB",
    "newfoundland and labrador": "NL", "newfoundland": "NL", "nl": "NL",
    "nova scotia": "NS", "ns": "NS",
    "ontario": "ON", "on": "ON",
    "prince edward island": "PE", "pei": "PE", "pe": "PE",
    "quebec": "QC", "québec": "QC", "qc": "QC",
    "saskatchewan": "SK", "sk": "SK",
}
CITY_PROVINCES = {
    "calgary": "AB", "edmonton": "AB",
    "vancouver": "BC", "victoria": "BC", "surrey": "BC",
    "toronto": "ON", "ottawa": "ON", "hamilton": "ON", "burlington": "ON",
    "mississauga": "ON", "oakville": "ON", "kitchener": "ON", "waterloo": "ON",
    "regina": "SK", "saskatoon": "SK",
}


def province_code(value: str | None, city: str | None = None) -> str | None:
    text = (value or "").strip().casefold()
    if text in PROVINCES:
        return PROVINCES[text]
    for name, code in PROVINCES.items():
        if re.search(rf"\b{re.escape(name)}\b", text):
            return code
    return CITY_PROVINCES.get((city or "").strip().casefold())


def parse_date(value: Any) -> date | None:
    if value is None or value == "":
        return None
    text = str(value)
    match = re.search(r"(\d{4}-\d{2}-\d{2})", text)
    if match:
        return date.fromisoformat(match.group(1))
    if text.replace(".", "", 1).isdigit():
        timestamp = float(text)
        if timestamp > 1e12:
            timestamp /= 1000
        return datetime.fromtimestamp(timestamp, timezone.utc).date()
    return None


def remote_type(text: str, explicit_remote: bool | None = None) -> str:
    normalized = text.casefold()
    if "hybrid" in normalized:
        return "hybrid"
    if explicit_remote or any(term in normalized for term in ("remote", "work from home", "wfh", "distributed")):
        return "remote"
    return "onsite" if normalized.strip() else "unknown"


def annual_salary(value: Any, period: str | None = None) -> int | None:
    if value in (None, ""):
        return None
    amount = float(value)
    normalized = (period or "year").casefold()
    if "hour" in normalized:
        amount *= 2080
    elif "month" in normalized:
        amount *= 12
    elif "week" in normalized:
        amount *= 52
    return round(amount)
