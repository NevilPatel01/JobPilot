import httpx

from app.scrapers.base import JobSource, RawJob


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
            if item.get("position") and item.get("company"):
                jobs.append(
                    RawJob(
                        title=item["position"],
                        company=item["company"],
                        url=item.get("url", f"https://remoteok.com/jobs/{item['id']}"),
                        description=item.get("description", "") or "",
                        tech_stack=item.get("tags", []) or [],
                        source_id=str(item["id"]),
                        location=item.get("location") or "Remote",
                    )
                )
        return jobs
