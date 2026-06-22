from typing import Any

from app.core.config import settings
from app.jobs.pipeline.contracts import NormalizedJob
from app.jobs.pipeline.normalizer import normalize_job
from app.jobs.sources.base import CanadianJobSource, SourceAuthError, SourceRateLimited
from app.jobs.sources.helpers import annual_salary, parse_date, province_code, remote_type


class AdzunaSource(CanadianJobSource):
    source_name = "adzuna"
    display_name = "Adzuna Canada"
    requires_credentials = True
    rate_limit_label = "Provider plan quota"
    base_url = "https://api.adzuna.com/v1/api/jobs"

    @property
    def credentials_available(self) -> bool:
        return bool(settings.adzuna_app_id and settings.adzuna_app_key)

    async def fetch(self, query: str, city: str, max_pages: int = 1) -> list[NormalizedJob]:
        if not self.credentials_available:
            raise SourceAuthError("ADZUNA_APP_ID and ADZUNA_APP_KEY are not configured")
        jobs: list[NormalizedJob] = []
        for page in range(1, max_pages + 1):
            response = await self.client.get(
                f"{self.base_url}/{settings.adzuna_country}/search/{page}",
                params={
                    "app_id": settings.adzuna_app_id,
                    "app_key": settings.adzuna_app_key,
                    "what": query,
                    "where": city,
                    "results_per_page": 20,
                    "content-type": "application/json",
                },
            )
            if response.status_code in (401, 403):
                raise SourceAuthError("Adzuna rejected the configured credentials")
            if response.status_code == 429:
                raise SourceRateLimited("Adzuna rate limit reached")
            response.raise_for_status()
            results = response.json().get("results", [])
            if not results:
                break
            jobs.extend(job for item in results if (job := self.parse_item(item, city)))
        return jobs

    @staticmethod
    def parse_item(data: dict[str, Any], default_city: str) -> NormalizedJob | None:
        title = str(data.get("title") or "").strip()
        url = str(data.get("redirect_url") or data.get("link") or "").strip()
        if not title or not url:
            return None
        company_data = data.get("company") or {}
        company = company_data.get("display_name") if isinstance(company_data, dict) else company_data
        location = data.get("location") or {}
        display = location.get("display_name", "") if isinstance(location, dict) else str(location)
        areas = location.get("area", []) if isinstance(location, dict) else []
        province = next((province_code(str(area)) for area in areas if province_code(str(area))), None)
        province = province or province_code(display, default_city)
        city = next(
            (str(area) for area in reversed(areas) if str(area).casefold() not in {"canada", "ca"} and not province_code(str(area))),
            default_city,
        )
        description = str(data.get("description") or "")
        return normalize_job(
            {
                "title": title,
                "company": str(company or "Unknown"),
                "location": display or f"{city}, {province or 'Canada'}",
                "province": province,
                "city": city,
                "remote_type": remote_type(f"{title} {description}"),
                "salary_min": annual_salary(data.get("salary_min")),
                "salary_max": annual_salary(data.get("salary_max")),
                "currency": "CAD",
                "description": description,
                "apply_url": url,
                "source": "adzuna",
                "source_job_id": str(data.get("id") or "") or None,
                "posted_date": parse_date(data.get("created")),
                "raw_payload": data,
            }
        )
