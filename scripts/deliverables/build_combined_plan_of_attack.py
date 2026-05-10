"""Concatenate the three plan-of-attack section PDFs into a single
submission-ready PDF.

Reads:
    deliverables/plan_of_attack_section_1.pdf
    deliverables/plan_of_attack_section_2.pdf
    deliverables/plan_of_attack_section_3.pdf

Writes:
    deliverables/plan_of_attack_combined.pdf

Each section starts on a fresh page in the combined PDF (because PDF
concatenation is page-based). Section 1 carries the document title and
research question; Sections 2 and 3 jump straight into their chapter
titles and content.
"""

from pathlib import Path

from pypdf import PdfReader, PdfWriter


REPO_ROOT = Path(__file__).resolve().parents[2]
DELIVERABLES = REPO_ROOT / "deliverables"

INPUTS = [
    DELIVERABLES / "plan_of_attack_section_1.pdf",
    DELIVERABLES / "plan_of_attack_section_2.pdf",
    DELIVERABLES / "plan_of_attack_section_3.pdf",
]
OUTPUT = DELIVERABLES / "plan_of_attack_combined.pdf"


def main():
    writer = PdfWriter()
    for path in INPUTS:
        if not path.exists():
            raise FileNotFoundError(f"Missing input PDF: {path}")
        reader = PdfReader(str(path))
        for page in reader.pages:
            writer.add_page(page)
        print(f"Added {len(reader.pages)} pages from {path.name}")

    with open(OUTPUT, "wb") as f:
        writer.write(f)
    print(f"Wrote {OUTPUT} ({len(writer.pages)} pages total)")


if __name__ == "__main__":
    main()
