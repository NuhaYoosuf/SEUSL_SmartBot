"""
SEUSL Web Scraper
-----------------
Scrapes official SEUSL website pages and saves content as .txt files
into the scraped_data/ folder for testing alongside the existing /data folder.

Usage:
    pip install requests beautifulsoup4
    python seusl_web_scraper.py

Output: scraped_data/*.txt  (does NOT modify existing /data folder)
"""

import os
import time
import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse

# Output folder — separate from existing /data to avoid overwriting
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "scraped_data")
ALLOWLIST_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "scraper", "seusl_allowlist_urls.txt"
)
EXCLUDE_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "scraper", "seusl_exclude_patterns.txt"
)
PRIORITY_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "scraper", "seusl_crawl_priority.txt"
)

# SEUSL pages to scrape
PAGES = {
    "university_overview":         "https://www.seu.ac.lk/overview.php",
    "vision_mission":              "https://www.seu.ac.lk/vision_and_mission.php",
    "corporate_direction":         "https://www.seu.ac.lk/corporate_direction.php",
    "undergraduate_studies":       "https://www.seu.ac.lk/undergraduate_studies.php",
    "postgraduate_studies":        "https://www.seu.ac.lk/postgraduate_studies.php",
    "foreign_students":            "https://www.seu.ac.lk/foreign_students.php",
    "faculty_arts_culture":        "https://www.seu.ac.lk/fac/index.php",
    "faculty_management_commerce": "https://www.seu.ac.lk/fmc/index.php",
    "faculty_applied_sciences":    "https://www.seu.ac.lk/fas/index.php",
    "faculty_islamic_studies":     "https://www.seu.ac.lk/fia/index.php",
    "faculty_engineering":         "https://www.seu.ac.lk/fe/index.php",
    "faculty_technology":          "https://www.seu.ac.lk/ft/index.php",
    "examination":                 "https://www.seu.ac.lk/generaladmin/exams/",
    "student_welfare":             "https://www.seu.ac.lk/generaladmin/ssw/",
    "library":                     "https://www.seu.ac.lk/library/index.php",
    "downloads":                   "https://www.seu.ac.lk/download.php",
    "guidelines":                  "https://www.seu.ac.lk/guidelines.php",
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; SEUSLResearchBot/1.0)"
}


def make_page_key(url: str, used_keys: set[str]) -> str:
    """Create deterministic file-safe key from URL path/query and deduplicate when needed."""
    parsed = urlparse(url)
    path = parsed.path.strip("/")
    query = parsed.query

    if not path:
        base = "home"
    else:
        # Build readable key from URL path parts while preserving meaning.
        path_key = re.sub(r"[^a-zA-Z0-9]+", "_", path).strip("_").lower()
        base = path_key or "page"

    if query:
        query_key = re.sub(r"[^a-zA-Z0-9]+", "_", query).strip("_").lower()
        base = f"{base}_{query_key}"

    key = base
    counter = 2
    while key in used_keys:
        key = f"{base}_{counter}"
        counter += 1
    used_keys.add(key)
    return key


def load_pages_from_allowlist(file_path: str) -> dict[str, str]:
    """Load seed URLs from allowlist text file. Falls back to built-in pages when unavailable."""
    if not os.path.exists(file_path):
        return {}

    pages: dict[str, str] = {}
    used_keys: set[str] = set()

    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            url = line.strip()
            if not url or url.startswith("#"):
                continue
            if not url.startswith(("http://", "https://")):
                continue
            key = make_page_key(url, used_keys)
            pages[key] = url

    return pages


def load_exclude_patterns(file_path: str) -> list[str]:
    """Load URL exclusion patterns from text file."""
    if not os.path.exists(file_path):
        return []

    patterns: list[str] = []
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            rule = line.strip()
            if not rule or rule.startswith("#"):
                continue
            patterns.append(rule)
    return patterns


def load_priority_urls(file_path: str) -> list[str]:
    """Load crawl priorities from file format: PRIORITY | CATEGORY | URL."""
    if not os.path.exists(file_path):
        return []

    priority_urls: list[str] = []
    seen: set[str] = set()
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            row = line.strip()
            if not row or row.startswith("#"):
                continue
            parts = [part.strip() for part in row.split("|")]
            if len(parts) != 3:
                continue
            url = parts[2]
            if url.startswith(("http://", "https://")) and url not in seen:
                priority_urls.append(url)
                seen.add(url)
    return priority_urls


def is_excluded_url(url: str, patterns: list[str]) -> bool:
    """Apply simple substring-based exclusion checks for URL filtering."""
    lowered_url = url.lower()
    for pattern in patterns:
        if pattern.lower() in lowered_url:
            return True
    return False


def order_pages_by_priority(pages: dict[str, str], priority_urls: list[str]) -> dict[str, str]:
    """Return pages reordered by configured priority URLs while keeping remaining URLs."""
    if not priority_urls:
        return pages

    url_to_items: dict[str, list[tuple[str, str]]] = {}
    for name, url in pages.items():
        url_to_items.setdefault(url, []).append((name, url))

    ordered: dict[str, str] = {}

    # Add matching priority URLs first.
    for p_url in priority_urls:
        for name, url in url_to_items.pop(p_url, []):
            ordered[name] = url

    # Keep all remaining pages in their original insertion order.
    for name, url in pages.items():
        if name in ordered:
            continue
        ordered[name] = url

    return ordered


def clean_text(text: str) -> str:
    """Remove excess whitespace from extracted text."""
    lines = [line.strip() for line in text.splitlines()]
    cleaned, prev_blank = [], False
    for line in lines:
        if line == "":
            if not prev_blank:
                cleaned.append("")
            prev_blank = True
        else:
            cleaned.append(line)
            prev_blank = False
    return "\n".join(cleaned).strip()


def scrape_page(name: str, url: str) -> str:
    """Fetch a page, strip boilerplate, return clean text."""
    print(f"  Fetching: {url}")
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"  ⚠  FAILED — {e}")
        return ""

    soup = BeautifulSoup(resp.text, "html.parser")

    # Remove noisy tags
    for tag in soup(["script", "style", "nav", "footer", "header",
                     "noscript", "iframe", "aside"]):
        tag.decompose()

    # Prefer main content container over full body
    main = (
        soup.find("main")
        or soup.find("div", {"id": "content"})
        or soup.find("div", {"class": "content"})
        or soup.find("div", {"id": "main-content"})
        or soup.find("div", {"id": "main"})
        or soup.find("body")
    )

    raw = main.get_text(separator="\n") if main else soup.get_text(separator="\n")
    return clean_text(raw)


def save_text(name: str, url: str, content: str):
    """Write scraped text to OUTPUT_DIR/<name>.txt"""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    filepath = os.path.join(OUTPUT_DIR, f"{name}.txt")
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(f"SOURCE: SEUSL Official Website\n")
        f.write(f"URL: {url}\n")
        f.write(f"PAGE: {name.replace('_', ' ').title()}\n")
        f.write("=" * 60 + "\n\n")
        f.write(content)
    print(f"  ✔  Saved → {filepath}")


def main():
    pages_to_scrape = load_pages_from_allowlist(ALLOWLIST_FILE) or PAGES
    exclude_patterns = load_exclude_patterns(EXCLUDE_FILE)
    priority_urls = load_priority_urls(PRIORITY_FILE)

    if exclude_patterns:
        pages_to_scrape = {
            name: url
            for name, url in pages_to_scrape.items()
            if not is_excluded_url(url, exclude_patterns)
        }

    if priority_urls:
        pages_to_scrape = order_pages_by_priority(pages_to_scrape, priority_urls)

    print("=" * 60)
    print("  SEUSL Web Scraper")
    print(f"  Output: {OUTPUT_DIR}")
    if os.path.exists(ALLOWLIST_FILE):
        print(f"  URL source: {ALLOWLIST_FILE}")
    else:
        print("  URL source: built-in defaults (allowlist file not found)")
    if os.path.exists(EXCLUDE_FILE):
        print(f"  Exclude rules: {EXCLUDE_FILE} ({len(exclude_patterns)} patterns)")
    else:
        print("  Exclude rules: none (exclude file not found)")
    if os.path.exists(PRIORITY_FILE):
        print(f"  Priority map: {PRIORITY_FILE} ({len(priority_urls)} URLs)")
    else:
        print("  Priority map: none (priority file not found)")
    print(f"  Total pages queued: {len(pages_to_scrape)}")
    print("=" * 60)

    success, fail = 0, 0

    for name, url in pages_to_scrape.items():
        print(f"\n[{name}]")
        content = scrape_page(name, url)
        if content:
            save_text(name, url, content)
            success += 1
        else:
            fail += 1
        time.sleep(1)  # Polite delay between requests

    print("\n" + "=" * 60)
    print(f"  Completed: {success} scraped | {fail} failed")
    print(f"  Files saved to: {OUTPUT_DIR}")
    print("=" * 60)

    if success > 0:
        print("\n✅ Next step: update vector.py to also load from './scraped_data'")
        print("   Change: glob='*.txt' with path='./data' to include './scraped_data'")


if __name__ == "__main__":
    main()
