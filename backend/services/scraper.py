import httpx
from bs4 import BeautifulSoup
import re


async def scrape_job_url(url: str) -> dict:
    """Scrape a job posting URL and extract structured data."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7",
    }

    async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
        response = await client.get(url, headers=headers)
        response.raise_for_status()
        html = response.text

    soup = BeautifulSoup(html, "html.parser")

    # Remove script and style elements
    for tag in soup(["script", "style", "nav", "footer", "header"]):
        tag.decompose()

    # Try to find job title
    title = _extract_title(soup)

    # Try to find company name
    company = _extract_company(soup, url)

    # Try to find location
    location = _extract_location(soup)

    # Try to find reference number (Kennziffer)
    ref_number = _extract_reference_number(soup, html)

    # Extract main description text
    description = _extract_description(soup)

    return {
        "job_title": title or "Unknown Position",
        "company": company or "Unknown Company",
        "company_location": location or "",
        "reference_number": ref_number or "",
        "job_description_raw": description or "",
        "job_url": url,
    }


def _extract_title(soup: BeautifulSoup) -> str:
    for selector in [
        "h1", "[data-testid='job-title']", ".job-title", ".job-header__title",
        ".posting-headline", '[class*="job-title"]', '[class*="position"]',
        "title", 'meta[property="og:title"]',
    ]:
        el = soup.select_one(selector)
        if el:
            text = el.get("content", "") if el.name == "meta" else el.get_text(strip=True)
            # Clean up common suffixes
            text = re.sub(r'\s*[-–|]\s*(m/w/d|m/w/x|f/m/d|all genders).*$', '', text, flags=re.IGNORECASE)
            if len(text) > 5:
                return text
    return ""


def _extract_company(soup: BeautifulSoup, url: str) -> str:
    for selector in [
        "[data-testid='company-name']", ".company-name", ".employer-name",
        ".job-company", '[class*="company"]', 'meta[property="og:site_name"]',
    ]:
        el = soup.select_one(selector)
        if el:
            text = el.get("content", "") if el.name == "meta" else el.get_text(strip=True)
            if len(text) > 1:
                return text
    # Try domain-based fallback
    domain = re.search(r'https?://(?:www\.)?([^/]+)', url)
    if domain:
        return domain.group(1).split(".")[0].capitalize()
    return ""


def _extract_location(soup: BeautifulSoup) -> str:
    for selector in [
        "[data-testid='location']", ".job-location", ".location",
        '[class*="location"]', '[class*="standort"]',
    ]:
        el = soup.select_one(selector)
        if el:
            text = el.get_text(strip=True)
            if len(text) > 2:
                return text
    return ""


def _extract_reference_number(soup: BeautifulSoup, html: str) -> str:
    # Common German job board patterns
    patterns = [
        r'Kennziffer[:\s]+([A-Za-z0-9\-_/]+)',
        r'Referenznummer[:\s]+([A-Za-z0-9\-_/]+)',
        r'Stellen-ID[:\s]+([A-Za-z0-9\-_/]+)',
        r'Job-ID[:\s]+([A-Za-z0-9\-_/]+)',
        r'Referenz[:\s]+([A-Za-z0-9\-_/]+)',
        r'Ref\.?\s*Nr\.?[:\s]+([A-Za-z0-9\-_/]+)',
    ]
    for pattern in patterns:
        match = re.search(pattern, html, re.IGNORECASE)
        if match:
            return match.group(1)
    return ""


def _extract_description(soup: BeautifulSoup) -> str:
    candidates = []
    for selector in [
        "[data-testid='job-description']", ".job-description", "#job-description",
        '[class*="description"]', '[class*="stellenbeschreibung"]',
        ".posting-content", "article", "main", ".content",
    ]:
        el = soup.select_one(selector)
        if el:
            text = el.get_text(separator="\n", strip=True)
            if len(text) > 200:
                candidates.append((len(text), text))

    if candidates:
        candidates.sort(key=lambda x: x[0], reverse=True)
        return candidates[0][1]

    # Fallback: largest text block on page
    body = soup.find("body")
    if body:
        return body.get_text(separator="\n", strip=True)
    return ""
