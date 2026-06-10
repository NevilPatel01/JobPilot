from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup
from playwright.async_api import async_playwright


async def _fetch_page(url: str) -> str:
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        try:
            await page.goto(url, timeout=20000, wait_until="domcontentloaded")
            await page.wait_for_timeout(1500)
            html = await page.content()
        finally:
            await browser.close()
    return html


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

    for page_url in pages_to_try:
        if page_url in seen:
            continue
        seen.add(page_url)
        try:
            html = await _fetch_page(page_url)
            text = _extract_text(html)
            if len(text) > 100:
                collected.append(text[:4000])
                sources.append({"url": page_url, "title": _company_name_from_url(page_url)})
        except Exception:
            continue

    full_text = "\n\n".join(collected)
    return {
        "company_name": _company_name_from_url(url),
        "company_url": url,
        "raw_text": full_text[:12000],
        "sources": sources,
        "summary": full_text[:1500] if full_text else "",
    }
