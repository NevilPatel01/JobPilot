import httpx

from app.scrapers.base import JobSource, RawJob


class HackerNewsScraper(JobSource):
    source_name = "hackernews"

    async def fetch(self) -> list[RawJob]:
        params = {"query": "hiring remote", "tags": "job", "hitsPerPage": 100}
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
            jobs.append(
                RawJob(
                    title=title[:255],
                    company=company[:255],
                    url=url,
                    description=hit.get("comment_text") or title,
                    source_id=str(hit.get("objectID", "")),
                    location="Remote",
                )
            )
        return jobs
