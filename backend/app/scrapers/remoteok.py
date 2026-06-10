import httpx

from app.scrapers.base import JobSource, RawJob
from app.services.location import is_canadian_job


class RemoteOKScraper(JobSource):
    source_name = "remoteok"

    async def fetch(self) -> list[RawJob]:
        headers = {"User-Agent": "JobPilot/1.0 (open-source job aggregator)"}
        async with httpx.AsyncClient(timeout=15) as client:
            try:
                r = await client.get("https://remoteok.com/api", headers=headers)
                r.raise_for_status()
                data = r.json()[1:]
            except Exception as e:
                print(f"[RemoteOK] fetch failed: {e}")
                return []

        jobs: list[RawJob] = []
        for item in data:
            if not item.get("position") or not item.get("company"):
                continue

            location = item.get("location") or "Remote"
            description = item.get("description", "") or ""
            title = item["position"]
            if not is_canadian_job(location, description, title):
                continue

            jobs.append(
                RawJob(
                    title=title,
                    company=item["company"],
                    url=item.get("url", f"https://remoteok.com/jobs/{item['id']}"),
                    description=description,
                    tech_stack=item.get("tags", []) or [],
                    source_id=str(item["id"]),
                    location=location,
                )
            )
        return jobs
