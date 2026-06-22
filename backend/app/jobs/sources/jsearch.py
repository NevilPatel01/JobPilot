from typing import Any

from app.core.config import settings
from app.jobs.pipeline.contracts import NormalizedJob
from app.jobs.pipeline.normalizer import normalize_job
from app.jobs.sources.base import CanadianJobSource, SourceAuthError, SourceRateLimited
from app.jobs.sources.helpers import annual_salary, parse_date, province_code, remote_type


class JSearchSource(CanadianJobSource):
    source_name = "jsearch"
    display_name = "JSearch"
    requires_credentials = True
    rate_limit_label = "RapidAPI plan quota"

    @property
    def credentials_available(self) -> bool:
        return bool(settings.rapidapi_key)

    async def fetch(self, query: str, city: str, max_pages: int = 1) -> list[NormalizedJob]:
        if not self.credentials_available:
            raise SourceAuthError("RAPIDAPI_KEY is not configured")
        jobs: list[NormalizedJob] = []
        for page in range(1, max_pages + 1):
            response = await self.client.get(
                f"https://{settings.jsearch_host}/search",
                headers={"X-RapidAPI-Key": settings.rapidapi_key, "X-RapidAPI-Host": settings.jsearch_host},
                params={
                    "query": f"{query} in {city}, Canada",
                    "page": str(page),
                    "num_pages": "1",
                    "date_posted": "month",
                    "country": "ca",
                },
            )
            if response.status_code in (401, 403):
                raise SourceAuthError("JSearch rejected the configured RapidAPI key")
            if response.status_code == 429:
                raise SourceRateLimited("JSearch rate limit reached")
            response.raise_for_status()
            payload = response.json()
            results = payload.get("data", payload.get("jobs", payload.get("results", [])))
            if not results:
                break
            jobs.extend(job for item in results if (job := self.parse_item(item, city)))
        return jobs

    @staticmethod
    def parse_item(data: dict[str, Any], default_city: str) -> NormalizedJob | None:
        title = str(data.get("job_title") or data.get("title") or data.get("position") or "").strip()
        url = str(data.get("job_apply_link") or data.get("link") or "").strip()
        if not title or not url:
            return None
        company_data = data.get("employer_name") or data.get("company_name") or data.get("company")
        company = company_data.get("name") if isinstance(company_data, dict) else company_data
        city = str(data.get("job_city") or data.get("city") or default_city)
        state = str(data.get("job_state") or data.get("state") or "")
        country = str(data.get("job_country") or data.get("country") or "CA").upper()
        if country not in {"CA", "CANADA"}:
            return None
        description = str(data.get("job_description") or data.get("description") or "")
        salary_period = str(data.get("job_salary_period") or "YEAR")
        is_remote = bool(data.get("job_is_remote"))
        return normalize_job(
            {
                "title": title,
                "company": str(company or "Unknown"),
                "location": ", ".join(part for part in (city, state) if part),
                "province": province_code(state, city),
                "city": city,
                "remote_type": remote_type(f"{description} {data.get('job_employment_type', '')}", is_remote),
                "job_type": data.get("job_employment_type"),
                "salary_min": annual_salary(data.get("job_min_salary"), salary_period),
                "salary_max": annual_salary(data.get("job_max_salary"), salary_period),
                "currency": data.get("job_salary_currency") or "CAD",
                "description": description,
                "apply_url": url,
                "source": "jsearch",
                "source_job_id": str(data.get("job_id") or data.get("id") or "") or None,
                "posted_date": parse_date(data.get("job_posted_at_datetime_utc") or data.get("job_posted_at_timestamp")),
                "raw_payload": data,
            }
        )
