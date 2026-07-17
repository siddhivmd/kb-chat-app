import pdfplumber

def extract_pdf_text(pdf_path):
    """Extract text from a PDF, page by page, keeping page numbers."""
    pages = []
    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages):
            text = page.extract_text()
            if text:  # skip blank/image-only pages for now
                pages.append({
                    "page_number": i + 1,
                    "text": text
                })
    return pages

if __name__ == "__main__":
    pdf_path = "sample.pdf"  # we'll change this to a real file next
    result = extract_pdf_text(pdf_path)
    print(f"Extracted {len(result)} pages")
    print("--- First page preview ---")
    print(result[0]["text"][:300])