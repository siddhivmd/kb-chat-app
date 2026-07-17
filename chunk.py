from extract import extract_pdf_text

def chunk_text(pages, chunk_size=300, overlap=50):
    """
    Split page-level text into overlapping chunks.
    Keeps track of which page each chunk came from.
    """
    chunks = []
    chunk_id = 0

    for page in pages:
        text = page["text"]
        start = 0
        while start < len(text):
            end = start + chunk_size
            chunk_text_piece = text[start:end]
            chunks.append({
                "chunk_id": chunk_id,
                "text": chunk_text_piece,
                "page_number": page["page_number"]
            })
            chunk_id += 1
            start += chunk_size - overlap  # move forward, but overlap a bit

    return chunks

if __name__ == "__main__":
    pdf_path = "sample.pdf"
    pages = extract_pdf_text(pdf_path)
    chunks = chunk_text(pages)

    print(f"Created {len(chunks)} chunks from {len(pages)} pages")
    print("--- First chunk ---")
    print(chunks[0])
    print("--- Second chunk (should overlap with first) ---")
    print(chunks[1])
