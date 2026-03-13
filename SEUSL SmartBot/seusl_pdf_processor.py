"""
SEUSL PDF Processor
--------------------
Extracts text from SEUSL-related PDF documents (handbooks, brochures,
exam regulations, etc.) and saves them as .txt files into pdf_extracted_data/
for use in the RAG knowledge base.

Usage:
    1. Place your SEUSL PDF files inside the  'seusl_pdfs/'  folder.
    2. Run:
           pip install pdfplumber PyPDF2
           python seusl_pdf_processor.py

Output:  pdf_extracted_data/*.txt  (does NOT modify existing /data folder)

Supported sources:
    - Student handbooks
    - Admission brochures
    - Examination regulations
    - Faculty prospectuses
    - Academic calendars
    - Any other official SEUSL PDF document
"""

import os
import re

# ---------------------------------------------------------------------------
# Attempt to import pdfplumber (preferred) then fall back to PyPDF2
# ---------------------------------------------------------------------------
try:
    import pdfplumber
    PDF_BACKEND = "pdfplumber"
except ImportError:
    pdfplumber = None
    PDF_BACKEND = None

try:
    import PyPDF2
    if PDF_BACKEND is None:
        PDF_BACKEND = "PyPDF2"
except ImportError:
    PyPDF2 = None

if PDF_BACKEND is None:
    raise ImportError(
        "No PDF library found.\n"
        "Install one with:  pip install pdfplumber PyPDF2"
    )

print(f"Using PDF backend: {PDF_BACKEND}")

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
PDF_INPUT_DIR   = os.path.join(os.path.dirname(os.path.abspath(__file__)), "seusl_pdfs")
OUTPUT_DIR      = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pdf_extracted_data")


# ---------------------------------------------------------------------------
# Extraction helpers
# ---------------------------------------------------------------------------

def extract_with_pdfplumber(pdf_path: str) -> str:
    """Extract text from a PDF using pdfplumber (better layout preservation)."""
    pages_text = []
    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages, start=1):
            text = page.extract_text()
            if text:
                pages_text.append(f"--- Page {i} ---\n{text.strip()}")
    return "\n\n".join(pages_text)


def extract_with_pypdf2(pdf_path: str) -> str:
    """Extract text from a PDF using PyPDF2 (fallback)."""
    pages_text = []
    with open(pdf_path, "rb") as f:
        reader = PyPDF2.PdfReader(f)
        for i, page in enumerate(reader.pages, start=1):
            text = page.extract_text()
            if text:
                pages_text.append(f"--- Page {i} ---\n{text.strip()}")
    return "\n\n".join(pages_text)


def extract_text(pdf_path: str) -> str:
    """Extract text using whichever backend is available."""
    if PDF_BACKEND == "pdfplumber" and pdfplumber:
        return extract_with_pdfplumber(pdf_path)
    elif PyPDF2:
        return extract_with_pypdf2(pdf_path)
    return ""


def clean_text(text: str) -> str:
    """Normalize whitespace in extracted PDF text."""
    # Replace multiple spaces with single space (common in PDFs)
    text = re.sub(r'[ \t]+', ' ', text)
    # Remove lines that are just page numbers or single characters
    lines = [ln.strip() for ln in text.splitlines()]
    cleaned, prev_blank = [], False
    for line in lines:
        if re.fullmatch(r'\d+', line):   # skip lone page-number lines
            continue
        if line == "":
            if not prev_blank:
                cleaned.append("")
            prev_blank = True
        else:
            cleaned.append(line)
            prev_blank = False
    return "\n".join(cleaned).strip()


# ---------------------------------------------------------------------------
# Save helper
# ---------------------------------------------------------------------------

def save_text(name: str, source_pdf: str, content: str):
    """Write extracted text to OUTPUT_DIR/<name>.txt"""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    filepath = os.path.join(OUTPUT_DIR, f"{name}.txt")
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(f"SOURCE: SEUSL PDF Document\n")
        f.write(f"FILE: {source_pdf}\n")
        f.write("=" * 60 + "\n\n")
        f.write(content)
    print(f"  ✔  Saved → {filepath}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("=" * 60)
    print("  SEUSL PDF Processor")
    print(f"  Input  folder: {PDF_INPUT_DIR}")
    print(f"  Output folder: {OUTPUT_DIR}")
    print("=" * 60)

    # Create input folder if it doesn't exist yet
    os.makedirs(PDF_INPUT_DIR, exist_ok=True)

    pdf_files = [f for f in os.listdir(PDF_INPUT_DIR) if f.lower().endswith(".pdf")]

    if not pdf_files:
        print(f"\n⚠  No PDF files found in '{PDF_INPUT_DIR}'")
        print("   Please place your SEUSL PDF documents (handbooks, brochures,")
        print("   exam regulations, academic calendars, etc.) into that folder")
        print("   and run this script again.\n")
        return

    success, fail = 0, 0

    for pdf_file in pdf_files:
        pdf_path = os.path.join(PDF_INPUT_DIR, pdf_file)
        name = os.path.splitext(pdf_file)[0].replace(" ", "_").lower()

        print(f"\n[{pdf_file}]")
        print(f"  Extracting text ({PDF_BACKEND})...")

        try:
            raw_text = extract_text(pdf_path)
            if not raw_text.strip():
                print("  ⚠  No extractable text (may be a scanned/image-based PDF)")
                fail += 1
                continue

            clean = clean_text(raw_text)
            save_text(name, pdf_file, clean)
            char_count = len(clean)
            print(f"  ✔  Extracted {char_count:,} characters")
            success += 1

        except Exception as e:
            print(f"  ✗  Error processing {pdf_file}: {e}")
            fail += 1

    print("\n" + "=" * 60)
    print(f"  Completed: {success} processed | {fail} failed")
    print(f"  Files saved to: {OUTPUT_DIR}")
    print("=" * 60)

    if success > 0:
        print("\n✅ Next step: update vector.py to also load from './pdf_extracted_data'")
        print("   Add another DirectoryLoader pointing to that folder,")
        print("   or merge all loaders into one using MergedDataLoader.")


if __name__ == "__main__":
    main()
