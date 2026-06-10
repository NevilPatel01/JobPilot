import xml.etree.ElementTree as ET

import httpx

from app.scrapers.base import JobSource, RawJob


class WeWorkRemotelyScraper(JobSource):
    source_name = "weworkremotely"
    FEEDS = [
        "https://weworkremotely.com/categories/remote-programming-jobs.rss",
        "https://weworkremotely.com/categories/remote-design-jobs.rss",
        "https://weworkremotely.com/categories/remote-product-jobs.rss",
    ]

    async def fetch(self) -> list[RawJob]:
        jobs: list[RawJob] = []
        async with httpx.AsyncClient(timeout=15) as client:
            for feed_url in self.FEEDS:
                try:
                    r = await client.get(feed_url)
                    r.raise_for_status()
                    root = ET.fromstring(r.text)
                    for item in root.findall(".//item"):
                        title_el = item.find("title")
                        link_el = item.find("link")
                        region_el = item.find("region")
                        desc_el = item.find("description")
                        if title_el is not None and title_el.text:
                            raw_title = title_el.text.strip()
                            if ": " in raw_title:
                                company, job_title = raw_title.split(": ", 1)
                            elif "|" in raw_title:
                                company, job_title = raw_title.split("|", 1)
                            else:
                                company, job_title = "Unknown", raw_title
                            jobs.append(
                                RawJob(
                                    title=job_title.strip(),
                                    company=company.strip(),
                                    url=link_el.text if link_el is not None and link_el.text else "",
                                    description=desc_el.text if desc_el is not None and desc_el.text else "",
                                    location=region_el.text if region_el is not None and region_el.text else "Remote",
                                    source_id=link_el.text if link_el is not None else None,
                                )
                            )
                except Exception as e:
                    print(f"[WWR] {feed_url} failed: {e}")
        return jobs
