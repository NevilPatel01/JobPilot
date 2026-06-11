import asyncio
import logging
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

from app.agents.retry import SCRAPE_BASE_DELAY_SECONDS, SCRAPE_MAX_ATTEMPTS, SCRAPE_TIMEOUT_SECONDS, with_retry

logger = logging.getLogger(__name__)

MAX_PAGES = 4
PAGE_FETCH_TIMEOUT = 20.0


async def _fetch_page(url: str) -> str:
    async def _load() -> str:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            try:
                await page.goto(url, timeout=int(PAGE_FETCH_TIMEOUT * 1000), wait_until="domcontentloaded")
                await page.wait_for_timeout(1200)
                return await page.content()
            finally:
                await browser.close()

    return await with_retry(
        _load,
        max_attempts=SCRAPE_MAX_ATTEMPTS,
        timeout_seconds=PAGE_FETCH_TIMEOUT + 5,
        base_delay_seconds=SCRAPE_BASE_DELAY_SECONDS,
        label=f"company scrape {url}",
    )


def _extract_text(html: str) -> str:
    soup = BeautifulSoup(html, "lxml")
    for tag in soup(["script", "style", "nav", "footer", "header", "noscript"]):
        tag.decompose()
    text = soup.get_text(separator="\n", strip=True)
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    return "\n".join(lines[:200])


def _company_name_from_url(url: str) -> str:
    host = urlparse(url).netloc.replace("www.", "")
    return host.split(".")[0].title() if host else "Company"


async def research_company(url: str) -> dict:
    pages_to_try = [url]
    parsed = urlparse(url)
    base = f"{parsed.scheme}://{parsed.netloc}"
    for path in ["/about", "/about-us", "/company", "/careers"]:
        pages_to_try.append(urljoin(base, path))

    collected: list[str] = []
    sources: list[dict] = []
    seen: set[str] = set()

    async def _scrape_all() -> tuple[list[str], list[dict]]:
        nonlocal collected, sources
        for page_url in pages_to_try[:MAX_PAGES]:
            if page_url in seen:
                continue
            seen.add(page_url)
            try:
                html = await _fetch_page(page_url)
                text = _extract_text(html)
                if len(text) > 100:
                    collected.append(text[:4000])
                    sources.append({"url": page_url, "title": _company_name_from_url(page_url)})
            except Exception as e:
                logger.warning("Skip company page %s: %s", page_url, e)
                continue
        return collected, sources

    try:
        collected, sources = await asyncio.wait_for(_scrape_all(), timeout=SCRAPE_TIMEOUT_SECONDS)
    except asyncio.TimeoutError:
        logger.warning("Company research timed out for %s", url)

    full_text = "\n\n".join(collected)
    return {
        "company_name": _company_name_from_url(url),
        "company_url": url,
        "raw_text": full_text[:12000],
        "sources": sources,
        "summary": full_text[:1500] if full_text else "",
    }
