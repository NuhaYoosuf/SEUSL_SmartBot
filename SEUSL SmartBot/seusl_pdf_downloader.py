"""
SEUSL PDF Downloader
--------------------
Downloads official PDF documents from the SEUSL website into seusl_pdfs/.
Also crawls key pages to discover additional PDF links.

Usage:
    python seusl_pdf_downloader.py
"""

import os
import re
import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, unquote

PDF_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "seusl_pdfs")
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; SEUSLResearchBot/1.0)"}

# Known direct PDF URLs from the SEUSL website
KNOWN_PDFS = [
    "https://www.seu.ac.lk/downloads/guidelines/Guidelines%20to%20Supervisors%20and%20Invigilators.pdf",
    "https://www.seu.ac.lk/downloads/guidelines/Regulations%20Related%20to%20Maintain%20Attendance%20and%20Calculation%20of%20Percentage%20Attendance.pdf",
    "https://www.seu.ac.lk/downloads/guidelines/Regulations%20Related%20to%20Setting,%20printing%20evaluation%20of%20exam.pdf",
    "https://www.seu.ac.lk/downloads/guidelines/Guideline%20for%20Field%20Trips.pdf",
    "https://www.seu.ac.lk/downloads/guidelines/ToR%20of%20the%20Grievence%20Hearing%20Committee.pdf",
    "https://www.seu.ac.lk/downloads/guidelines/Grievence%20Application%20form.pdf",
    "https://www.seu.ac.lk/ft/downloads/Book%20of%20Abstract_%20Undergraduate%20research%20conference%20final%20version.pdf",
]

# Pages to crawl for additional PDF links
CRAWL_PAGES = [
    "https://www.seu.ac.lk/download.php",
    "https://www.seu.ac.lk/guidelines.php",
    "https://www.seu.ac.lk/ft/index.php",
    "https://www.seu.ac.lk/fac/index.php",
    "https://www.seu.ac.lk/fmc/index.php",
    "https://www.seu.ac.lk/fas/index.php",
    "https://www.seu.ac.lk/fia/index.php",
    "https://www.seu.ac.lk/fe/index.php",
    "https://www.seu.ac.lk/library/index.php",
    "https://www.seu.ac.lk/generaladmin/exams/",
    "https://www.seu.ac.lk/generaladmin/ssw/",
    "https://www.seu.ac.lk/iqau/",
]


def discover_pdf_links(page_url: str) -> list[str]:
    """Crawl a page and extract all PDF links."""
    try:
        resp = requests.get(page_url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"  ⚠  Could not crawl {page_url}: {e}")
        return []

    soup = BeautifulSoup(resp.text, "html.parser")
    pdf_links = []
    for a_tag in soup.find_all("a", href=True):
        href = a_tag["href"]
        full_url = urljoin(page_url, href)
        if full_url.lower().endswith(".pdf"):
            pdf_links.append(full_url)
    return pdf_links


def safe_filename(url: str) -> str:
    """Create a safe filename from a URL."""
    parsed = urlparse(url)
    name = unquote(os.path.basename(parsed.path))
    # Clean up the filename
    name = re.sub(r'[<>:"/\\|?*]', '_', name)
    name = re.sub(r'_+', '_', name).strip('_')
    if not name.lower().endswith('.pdf'):
        name += '.pdf'
    return name


def download_pdf(url: str, output_dir: str) -> bool:
    """Download a single PDF file."""
    filename = safe_filename(url)
    filepath = os.path.join(output_dir, filename)

    if os.path.exists(filepath):
        print(f"  ⏭  Already exists: {filename}")
        return True

    try:
        resp = requests.get(url, headers=HEADERS, timeout=30, stream=True)
        resp.raise_for_status()

        content_type = resp.headers.get("Content-Type", "")
        if "pdf" not in content_type.lower() and "octet-stream" not in content_type.lower():
            print(f"  ⚠  Skipping (not a PDF): {filename} [{content_type}]")
            return False

        with open(filepath, "wb") as f:
            for chunk in resp.iter_content(chunk_size=8192):
                f.write(chunk)

        size_kb = os.path.getsize(filepath) / 1024
        print(f"  ✔  Downloaded: {filename} ({size_kb:.1f} KB)")
        return True

    except requests.exceptions.RequestException as e:
        print(f"  ✗  Failed to download {filename}: {e}")
        return False


def main():
    os.makedirs(PDF_DIR, exist_ok=True)

    print("=" * 60)
    print("  SEUSL PDF Downloader")
    print(f"  Output: {PDF_DIR}")
    print("=" * 60)

    # Collect all PDF URLs
    all_pdf_urls = set(KNOWN_PDFS)

    print(f"\n📡 Crawling {len(CRAWL_PAGES)} pages for PDF links...")
    for page_url in CRAWL_PAGES:
        print(f"  Scanning: {page_url}")
        found = discover_pdf_links(page_url)
        if found:
            print(f"    Found {len(found)} PDF link(s)")
            all_pdf_urls.update(found)
        time.sleep(0.5)

    # Filter to only seu.ac.lk PDFs
    seusl_pdfs = [u for u in all_pdf_urls if "seu.ac.lk" in u]
    print(f"\n📄 Total unique SEUSL PDFs found: {len(seusl_pdfs)}")

    # Download
    print(f"\n⬇  Downloading PDFs to {PDF_DIR}...\n")
    success, fail = 0, 0
    for url in sorted(seusl_pdfs):
        if download_pdf(url, PDF_DIR):
            success += 1
        else:
            fail += 1
        time.sleep(0.5)

    print("\n" + "=" * 60)
    print(f"  Completed: {success} downloaded | {fail} failed/skipped")
    print(f"  Files saved to: {PDF_DIR}")
    print("=" * 60)

    if success > 0:
        print("\n✅ Next step: run  python seusl_pdf_processor.py  to extract text")


if __name__ == "__main__":
    main()
