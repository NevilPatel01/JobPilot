import hashlib
import re
from collections.abc import Mapping
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from app.jobs.pipeline.contracts import NormalizedJob
from app.scrapers.base import RawJob


TRACKING_PARAMS = {
    "fbclid",
    "gclid",
    "mc_cid",
    "mc_eid",
    "ref",
    "referrer",
    "source",
}
PROVINCE_ALIASES = {
    "alberta": "AB",
    "british columbia": "BC",
    "b.c.": "BC",
    "manitoba": "MB",
    "new brunswick": "NB",
    "newfoundland and labrador": "NL",
    "nova scotia": "NS",
    "ontario": "ON",
    "prince edward island": "PE",
    "quebec": "QC",
    "québec": "QC",
    "saskatchewan": "SK",
}
PROVINCE_CODES = set(PROVINCE_ALIASES.values())


def canonicalize_url(url: str) -> str:
    candidate = url.strip()
    if "://" not in candidate:
        candidate = f"https://{candidate}"
    parts = urlsplit(candidate)
    host = (parts.hostname or "").lower()
    if host.startswith("www."):
        host = host[4:]
    port = f":{parts.port}" if parts.port and parts.port not in (80, 443) else ""
    path = re.sub(r"/{2,}", "/", parts.path or "/")
    if path != "/":
        path = path.rstrip("/")
    query = urlencode(
        sorted(
            (key, value)
            for key, value in parse_qsl(parts.query, keep_blank_values=True)
            if not key.lower().startswith("utm_") and key.lower() not in TRACKING_PARAMS
        )
    )
    return urlunsplit(("https", f"{host}{port}", path, query, ""))


def normalize_key(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", value.casefold())


def build_dedupe_hash(title: str, company: str, city: str | None) -> str:
    identity = "|".join((normalize_key(title), normalize_key(company), normalize_key(city or "")))
    return hashlib.sha256(identity.encode()).hexdigest()


def extract_province(location: str | None) -> str | None:
    if not location:
        return None
    normalized = location.casefold()
    for name, code in PROVINCE_ALIASES.items():
        if name in normalized:
            return code
    tokens = {token.upper() for token in re.findall(r"\b[a-zA-Z]{2}\b", location)}
    return next((code for code in PROVINCE_CODES if code in tokens), None)


def extract_city(location: str | None, province: str | None) -> str | None:
    if not location:
        return None
    first = location.split(",", 1)[0].strip()
    if not first or first.casefold() in {"canada", "remote", "remote canada"}:
        return None
    if province and first.upper() == province:
        return None
    return first[:120]


def detect_remote_type(location: str | None, is_remote: bool | None = None) -> str:
    text = (location or "").casefold()
    if "hybrid" in text:
        return "hybrid"
    if is_remote or "remote" in text:
        return "remote"
    if location:
        return "onsite"
    return "unknown"


def normalize_job(data: Mapping[str, Any]) -> NormalizedJob:
    location = str(data.get("location") or "").strip() or None
    province = str(data.get("province") or "").strip().upper() or extract_province(location)
    city = str(data.get("city") or "").strip() or extract_city(location, province)
    apply_url = str(data.get("apply_url") or data.get("url") or "").strip()
    canonical_url = canonicalize_url(apply_url)
    title = str(data.get("title") or "")
    company = str(data.get("company") or "")
    return NormalizedJob(
        title=title,
        company=company,
        location=location,
        province=province,
        city=city,
        remote_type=data.get("remote_type") or detect_remote_type(location, data.get("is_remote")),
        job_type=data.get("job_type") or data.get("employment_type"),
        salary_min=data.get("salary_min"),
        salary_max=data.get("salary_max"),
        currency=str(data.get("currency") or data.get("salary_currency") or "CAD").upper(),
        description=str(data.get("description") or ""),
        requirements=list(data.get("requirements") or []),
        skills=list(data.get("skills") or data.get("tech_stack") or []),
        seniority=data.get("seniority"),
        experience_min=data.get("experience_min"),
        experience_max=data.get("experience_max"),
        apply_url=apply_url,
        source=str(data.get("source") or "manual"),
        source_job_id=data.get("source_job_id") or data.get("source_id"),
        posted_date=data.get("posted_date"),
        closing_date=data.get("closing_date"),
        raw_payload=dict(data.get("raw_payload") or {}),
        canonical_url=canonical_url,
        dedupe_hash=build_dedupe_hash(title, company, city),
    )


def normalize_raw_job(raw: RawJob, source: str) -> NormalizedJob:
    return normalize_job(
        {
            "title": raw.title,
            "company": raw.company,
            "url": raw.url,
            "description": raw.description,
            "location": raw.location,
            "salary_min": raw.salary_min,
            "salary_max": raw.salary_max,
            "tech_stack": raw.tech_stack,
            "employment_type": raw.employment_type,
            "source_id": raw.source_id,
            "is_remote": raw.is_remote,
            "source": source,
        }
    )
