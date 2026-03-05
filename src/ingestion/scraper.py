"""
Telecom Egypt Website Scraper
Crawls https://te.eg and saves cleaned page content for RAG ingestion.
"""
import json
import re
import time
import logging
from urllib.parse import urljoin, urlparse
from pathlib import Path

import requests
from bs4 import BeautifulSoup
import html2text

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from config.settings import (
    TARGET_URL, RAW_DIR, SCRAPE_MAX_PAGES,
    SCRAPE_DELAY, SCRAPE_TIMEOUT,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger(__name__)

# ─── Helpers ──────────────────────────────────────────────────────────────────

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9,ar;q=0.8",
}

EXCLUDED_EXTENSIONS = {
    ".pdf", ".jpg", ".jpeg", ".png", ".gif", ".svg", ".mp4", ".mp3",
    ".zip", ".exe", ".css", ".js", ".ico", ".webp", ".woff", ".woff2", ".ttf",
}

EXCLUDED_PATHS = {
    "/login", "/signup", "/register", "/auth", "/api/", "/cdn-cgi/",
    "/wp-admin", "/wp-json", "/feed",
}


def is_valid_url(url: str, base_domain: str) -> bool:
    """Check if a URL should be crawled."""
    parsed = urlparse(url)

    # Must be same domain
    if base_domain not in parsed.netloc:
        return False

    # Skip non-http schemes
    if parsed.scheme not in ("http", "https"):
        return False

    # Skip excluded extensions
    path_lower = parsed.path.lower()
    for ext in EXCLUDED_EXTENSIONS:
        if path_lower.endswith(ext):
            return False

    # Skip excluded paths
    for excl in EXCLUDED_PATHS:
        if excl in path_lower:
            return False

    # Skip fragments and mailto
    if url.startswith("mailto:") or url.startswith("tel:"):
        return False

    return True


def clean_text(html_content: str) -> str:
    """Extract clean text from HTML."""
    soup = BeautifulSoup(html_content, "lxml")

    # Remove unwanted tags
    for tag in soup(["script", "style", "nav", "footer", "header", "noscript", "iframe", "meta", "link"]):
        tag.decompose()

    # Convert to markdown-ish text
    converter = html2text.HTML2Text()
    converter.ignore_links = False
    converter.ignore_images = True
    converter.ignore_emphasis = False
    converter.body_width = 0  # No wrapping
    text = converter.handle(str(soup))

    # Clean up whitespace
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r" {2,}", " ", text)
    return text.strip()


def extract_metadata(soup: BeautifulSoup, url: str) -> dict:
    """Extract page metadata."""
    title = ""
    if soup.title:
        title = soup.title.get_text(strip=True)

    description = ""
    meta_desc = soup.find("meta", attrs={"name": "description"})
    if meta_desc:
        description = meta_desc.get("content", "")

    og_title = ""
    og = soup.find("meta", attrs={"property": "og:title"})
    if og:
        og_title = og.get("content", "")

    return {
        "url": url,
        "title": title or og_title,
        "description": description,
    }


# ─── Main Scraper ────────────────────────────────────────────────────────────

class TelecomEgyptScraper:
    """Breadth-first crawler for te.eg."""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(HEADERS)
        self.visited: set[str] = set()
        self.queue: list[str] = [TARGET_URL]
        self.base_domain = urlparse(TARGET_URL).netloc
        self.pages: list[dict] = []

    def _normalize_url(self, url: str) -> str:
        """Normalize URL by removing fragments and trailing slashes."""
        parsed = urlparse(url)
        clean = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
        if clean.endswith("/") and len(parsed.path) > 1:
            clean = clean.rstrip("/")
        return clean

    def _fetch(self, url: str) -> requests.Response | None:
        """Fetch a page with error handling."""
        try:
            resp = self.session.get(url, timeout=SCRAPE_TIMEOUT, allow_redirects=True)
            resp.raise_for_status()
            content_type = resp.headers.get("Content-Type", "")
            if "text/html" not in content_type:
                return None
            return resp
        except requests.RequestException as e:
            logger.warning(f"Failed to fetch {url}: {e}")
            return None

    def _extract_links(self, soup: BeautifulSoup, page_url: str) -> list[str]:
        """Extract all valid links from a page."""
        links = []
        for a_tag in soup.find_all("a", href=True):
            href = a_tag["href"].strip()
            absolute = urljoin(page_url, href)
            normalized = self._normalize_url(absolute)
            if normalized not in self.visited and is_valid_url(normalized, self.base_domain):
                links.append(normalized)
        return links

    def crawl(self) -> list[dict]:
        """Run the breadth-first crawl."""
        logger.info(f"Starting crawl of {TARGET_URL} (max {SCRAPE_MAX_PAGES} pages)")

        while self.queue and len(self.visited) < SCRAPE_MAX_PAGES:
            url = self.queue.pop(0)
            normalized = self._normalize_url(url)

            if normalized in self.visited:
                continue

            self.visited.add(normalized)
            logger.info(f"[{len(self.visited)}/{SCRAPE_MAX_PAGES}] Crawling: {normalized}")

            resp = self._fetch(normalized)
            if resp is None:
                continue

            soup = BeautifulSoup(resp.text, "lxml")
            text = clean_text(resp.text)

            # Skip very short pages (likely error pages or redirects)
            if len(text) < 50:
                logger.debug(f"Skipping {normalized} — too short ({len(text)} chars)")
                continue

            metadata = extract_metadata(soup, normalized)
            page_data = {
                "url": normalized,
                "title": metadata["title"],
                "description": metadata["description"],
                "content": text,
                "char_count": len(text),
            }
            self.pages.append(page_data)

            # Discover new links
            new_links = self._extract_links(soup, normalized)
            self.queue.extend(new_links)

            # Rate limiting
            time.sleep(SCRAPE_DELAY)

        logger.info(f"Crawl complete. Scraped {len(self.pages)} pages from {len(self.visited)} visited URLs.")
        return self.pages

    def save(self, pages: list[dict] | None = None):
        """Save scraped data to disk."""
        pages = pages or self.pages
        output_file = RAW_DIR / "te_eg_pages.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(pages, f, ensure_ascii=False, indent=2)
        logger.info(f"Saved {len(pages)} pages to {output_file}")

        # Also save individual text files for inspection
        text_dir = RAW_DIR / "pages"
        text_dir.mkdir(exist_ok=True)
        for i, page in enumerate(pages):
            safe_name = re.sub(r"[^\w\-]", "_", page.get("title", f"page_{i}"))[:80]
            with open(text_dir / f"{i:03d}_{safe_name}.txt", "w", encoding="utf-8") as f:
                f.write(f"URL: {page['url']}\n")
                f.write(f"Title: {page['title']}\n")
                f.write(f"{'=' * 60}\n\n")
                f.write(page["content"])


# ─── CLI Entry Point ─────────────────────────────────────────────────────────

def main():
    scraper = TelecomEgyptScraper()
    pages = scraper.crawl()
    scraper.save(pages)
    return pages


if __name__ == "__main__":
    main()
