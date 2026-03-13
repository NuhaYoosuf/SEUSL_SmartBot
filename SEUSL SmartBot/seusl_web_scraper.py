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
import requests
from bs4 import BeautifulSoup

# Output folder — separate from existing /data to avoid overwriting
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "scraped_data")

# SEUSL pages to scrape
PAGES = {
    "university_overview":        "https://www.seu.ac.lk/",
    "faculty_arts_culture":       "https://www.seu.ac.lk/fac/",
    "faculty_management_commerce":"https://www.seu.ac.lk/fmc/",
    "faculty_applied_sciences":   "https://www.seu.ac.lk/fas/",
    "faculty_islamic_studies":    "https://www.seu.ac.lk/fia/",
    "faculty_engineering":        "https://fe.seu.ac.lk/",
    "faculty_technology":         "https://www.seu.ac.lk/ft/",
    "admissions":                 "https://www.seu.ac.lk/admission/",
    "library":                    "https://www.seu.ac.lk/library/",
    "ict_centre":                 "https://www.seu.ac.lk/ictcentre/index.php",
    "career_guidance":            "https://www.seu.ac.lk/careerguidanceunit/index.php",
    "research_innovation":        "https://www.seu.ac.lk/ric/index.php",
    "contact":                    "https://www.seu.ac.lk/contact.php",
    "ospim":                      "https://www.seu.ac.lk/ospim/index.php",
    "student_welfare":            "https://www.seu.ac.lk/sssw/index.php",
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; SEUSLResearchBot/1.0)"
}


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
    print("=" * 60)
    print("  SEUSL Web Scraper")
    print(f"  Output: {OUTPUT_DIR}")
    print("=" * 60)

    success, fail = 0, 0

    for name, url in PAGES.items():
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
