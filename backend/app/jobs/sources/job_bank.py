import hashlib
import re
from datetime import date, timedelta
from urllib.parse import urljoin

from bs4 import BeautifulSoup, Tag

from app.jobs.pipeline.contracts import NormalizedJob
from app.jobs.pipeline.normalizer import normalize_job
from app.jobs.sources.base import CanadianJobSource, SourceRateLimited
from app.jobs.sources.helpers import province_code


class JobBankSource(CanadianJobSource):
    source_name = "job_bank"
    display_name = "Job Bank Canada"
    requires_credentials = False
    rate_limit_label = "Public search, conservative request rate"
    base_url = "https://www.jobbank.gc.ca/jobsearch/jobsearch"

    @property
    def credentials_available(self) -> bool:
        return True

    async def fetch(self, query: str, city: str, max_pages: int = 1) -> list[NormalizedJob]:
        jobs: list[NormalizedJob] = []
        for page in range(1, max_pages + 1):
            response = await self.client.get(
                self.base_url,
                params={"searchstring": query, "location": city, "postedDate": "30", "sort": "posted", "page": page},
                headers={
                    "User-Agent": "JobPilot/1.0 (personal Canadian job search tool)",
                    "Accept": "text/html,application/xhtml+xml",
                    "Accept-Language": "en-CA,en;q=0.9",
                },
            )
            if response.status_code == 429:
                raise SourceRateLimited("Job Bank request rate limit reached")
            response.raise_for_status()
            parsed = self.parse_search_html(response.text, city)
            if not parsed:
                break
            jobs.extend(parsed)
        return jobs

    @classmethod
    def parse_search_html(cls, html: str, default_city: str) -> list[NormalizedJob]:
        soup = BeautifulSoup(html, "html.parser")
        jobs: list[NormalizedJob] = []
        for article in soup.find_all("article", class_="action-buttons"):
            if not isinstance(article, Tag):
                continue
            link = article.find("a", class_="resultJobItem")
            if not isinstance(link, Tag):
                continue
            href = str(link.get("href") or "")
            title_element = link.find("span", class_="noctitle")
            if not href or not title_element:
                continue
            title = title_element.get_text(" ", strip=True)
            company_element = link.find("li", class_="business")
            company = company_element.get_text(" ", strip=True) if company_element else "Unknown"
            location_element = link.find("li", class_="location")
            location = location_element.get_text(" ", strip=True) if location_element else default_city
            location = re.sub(r"^Location\s*", "", location, flags=re.IGNORECASE).strip()
            city, province = cls.parse_location(location, default_city)
            salary_element = link.find("li", class_="salary")
            salary_min, salary_max = cls.parse_salary(salary_element.get_text(" ", strip=True) if salary_element else "")
            date_element = link.find("li", class_="date")
            posted_date = cls.parse_posted_date(date_element.get_text(" ", strip=True) if date_element else "")
            description_element = link.find(class_=re.compile(r"description|summary", re.I))
            description = description_element.get_text(" ", strip=True) if description_element else ""
            job_id_match = re.search(r"/(\d+)/?$", href)
            source_id = job_id_match.group(1) if job_id_match else hashlib.sha256(href.encode()).hexdigest()[:16]
            url = urljoin("https://www.jobbank.gc.ca", href)
            jobs.append(
                normalize_job(
                    {
                        "title": title,
                        "company": company,
                        "location": location,
                        "province": province,
                        "city": city,
                        "salary_min": salary_min,
                        "salary_max": salary_max,
                        "currency": "CAD",
                        "description": description,
                        "apply_url": url,
                        "source": "job_bank",
                        "source_job_id": source_id,
                        "posted_date": posted_date,
                        "raw_payload": {"search_location": default_city},
                    }
                )
            )
        return jobs

    @staticmethod
    def parse_location(location: str, default_city: str) -> tuple[str, str | None]:
        parenthesized = re.match(r"^(.+?)\s*\(([A-Z]{2})\)$", location)
        if parenthesized:
            return parenthesized.group(1).strip(), parenthesized.group(2)
        parts = [part.strip() for part in location.split(",") if part.strip()]
        city = parts[0] if parts else default_city
        province = province_code(parts[-1] if len(parts) > 1 else "", city)
        return city, province

    @staticmethod
    def parse_salary(text: str) -> tuple[int | None, int | None]:
        if not text or "not available" in text.casefold():
            return None, None
        values = [float(value.replace(",", "")) for value in re.findall(r"\$?([\d,]+(?:\.\d+)?)", text)]
        if not values:
            return None, None
        low, high = min(values[:2]), max(values[:2])
        normalized = text.casefold()
        if any(term in normalized for term in ("hourly", "per hour", "/hr")):
            low, high = low * 2080, high * 2080
        elif "biweekly" in normalized or "bi-weekly" in normalized:
            low, high = low * 26, high * 26
        if high < 10000:
            return None, None
        return round(low), round(high)

    @staticmethod
    def parse_posted_date(text: str) -> date | None:
        iso = re.search(r"(\d{4}-\d{2}-\d{2})", text)
        if iso:
            return date.fromisoformat(iso.group(1))
        days = re.search(r"(\d+)\s+days?\s+ago", text, re.IGNORECASE)
        if days:
            return date.today() - timedelta(days=int(days.group(1)))
        if "yesterday" in text.casefold():
            return date.today() - timedelta(days=1)
        if "today" in text.casefold():
            return date.today()
        return None
