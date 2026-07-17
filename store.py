import chromadb
from sentence_transformers import SentenceTransformer
from extract import extract_pdf_text
from chunk import chunk_text

# Load the free local embedding model (downloads once, then cached)
print("Loading embedding model...")
embedder = SentenceTransformer("multi-qa-MiniLM-L6-cos-v1")

# Set up ChromaDB (stores data in a local folder called chroma_db)
client = chromadb.PersistentClient(path="chroma_db")
collection = client.get_or_create_collection(
    name="documents",
    metadata={"hnsw:space": "cosine"}
)
# 

def store_pdf(pdf_path, source_name):
    pages = extract_pdf_text(pdf_path)
    chunks = chunk_text(pages)

    texts = [c["text"] for c in chunks]
    print(f"Embedding {len(texts)} chunks...")
    embeddings = embedder.encode(texts).tolist()

    ids = [f"{source_name}_{c['chunk_id']}" for c in chunks]
    metadatas = [{"source": source_name, "page_number": c["page_number"]} for c in chunks]

    collection.add(
        ids=ids,
        embeddings=embeddings,
        documents=texts,
        metadatas=metadatas
    )
    print(f"Stored {len(chunks)} chunks from {source_name}")

if __name__ == "__main__":
    store_pdf("sample.pdf", "sample.pdf")

    # Quick test: search for something
    query = "What is the objective of this assessment?"
    query_embedding = embedder.encode([query]).tolist()
    results = collection.query(query_embeddings=query_embedding, n_results=2)

    print("\n--- Search results for:", query, "---")
    for doc, meta in zip(results["documents"][0], results["metadatas"][0]):
        print(f"\n[Page {meta['page_number']}] {doc[:200]}...")
