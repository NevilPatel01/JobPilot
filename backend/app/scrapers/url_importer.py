import json
import re

from bs4 import BeautifulSoup

from app.scrapers.base import RawJob


def extract_job_fields(soup: BeautifulSoup, url: str) -> RawJob:
    title = ""
    company = ""
    description = ""
    location = None
    salary_min = None
    salary_max = None
    is_remote = "remote" in url.lower()

    for script in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(script.string or "{}")
            if isinstance(data, list):
                data = data[0] if data else {}
            if data.get("@type") == "JobPosting":
                title = data.get("title", "") or title
                hiring = data.get("hiringOrganization", {})
                if isinstance(hiring, dict):
                    company = hiring.get("name", "") or company
                description = data.get("description", "") or description
                loc = data.get("jobLocation", {})
                if isinstance(loc, dict):
                    addr = loc.get("address", {})
                    if isinstance(addr, dict):
                        location = addr.get("addressLocality") or location
                if data.get("jobLocationType") == "TELECOMMUTE":
                    is_remote = True
        except (json.JSONDecodeError, TypeError):
            continue

    if not title:
        og_title = soup.find("meta", property="og:title")
        if og_title and og_title.get("content"):
            title = og_title["content"]
        elif soup.title and soup.title.string:
            title = soup.title.string.strip()

    if not company:
        og_site = soup.find("meta", property="og:site_name")
        if og_site and og_site.get("content"):
            company = og_site["content"]

    if not description:
        og_desc = soup.find("meta", property="og:description")
        if og_desc and og_desc.get("content"):
            description = og_desc["content"]
        else:
            main = soup.find("main") or soup.find("article") or soup.body
            if main:
                description = main.get_text(separator=" ", strip=True)[:5000]

    if "|" in title and not company:
        parts = title.split("|", 1)
        company, title = parts[0].strip(), parts[1].strip()

    if not company:
        company = "Unknown Company"

    text_lower = (description + title).lower()
    if "remote" in text_lower:
        is_remote = True

    salary_match = re.search(r"\$[\d,]+(?:k)?(?:\s*[-–]\s*\$?[\d,]+(?:k)?)?", description, re.I)
    salary_range_str = salary_match.group(0) if salary_match else None
    if salary_range_str:
        nums = re.findall(r"[\d,]+", salary_range_str.replace("k", "000"))
        if nums:
            salary_min = int(nums[0].replace(",", ""))
            if len(nums) > 1:
                salary_max = int(nums[1].replace(",", ""))

    return RawJob(
        title=title[:255] if title else "Untitled Position",
        company=company[:255],
        url=url,
        description=description,
        location=location,
        salary_min=salary_min,
        salary_max=salary_max,
        is_remote=is_remote,
    )


async def import_from_url(url: str) -> RawJob:
    from playwright.async_api import async_playwright

    html = ""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        try:
            await page.goto(url, timeout=15000, wait_until="domcontentloaded")
            await page.wait_for_timeout(2000)
            html = await page.content()
        finally:
            await browser.close()

    soup = BeautifulSoup(html, "lxml")
    return extract_job_fields(soup, url)
