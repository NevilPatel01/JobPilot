import httpx

from app.scrapers.base import JobSource, RawJob
from app.services.location import is_canadian_job


class HackerNewsScraper(JobSource):
    source_name = "hackernews"

    async def fetch(self) -> list[RawJob]:
        params = {"query": "hiring canada", "tags": "job", "hitsPerPage": 100}
        async with httpx.AsyncClient(timeout=15) as client:
            try:
                r = await client.get("https://hn.algolia.com/api/v1/search", params=params)
                r.raise_for_status()
                hits = r.json().get("hits", [])
            except Exception as e:
                print(f"[HN] fetch failed: {e}")
                return []

        jobs: list[RawJob] = []
        for hit in hits:
            title = hit.get("title") or hit.get("story_title") or ""
            url = hit.get("url") or f"https://news.ycombinator.com/item?id={hit.get('objectID', '')}"
            if not title:
                continue
            company = hit.get("author", "Unknown")
            description = hit.get("comment_text") or title
            if not is_canadian_job(None, description, title):
                continue

            jobs.append(
                RawJob(
                    title=title[:255],
                    company=company[:255],
                    url=url,
                    description=description,
                    source_id=str(hit.get("objectID", "")),
                    location="Canada",
                )
            )
        return jobs
