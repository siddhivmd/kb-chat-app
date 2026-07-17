import os
from dotenv import load_dotenv
from groq import Groq
from sentence_transformers import SentenceTransformer
import chromadb
import time

load_dotenv()

def get_confidence_label(similarity):
    if similarity >= 0.5:
        return "High"
    elif similarity >= 0.3:
        return "Medium"
    else:
        return "Low"

embedder = SentenceTransformer("multi-qa-MiniLM-L6-cos-v1")
client_db = chromadb.PersistentClient(path="chroma_db")
collection = client_db.get_or_create_collection(
    name="documents",
    metadata={"hnsw:space": "cosine"}
)

groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

CONFIDENCE_THRESHOLD = 0.3

def answer_question(question, n_results=4):
    query_embedding = embedder.encode([question]).tolist()
    results = collection.query(query_embeddings=query_embedding, n_results=n_results)

    docs = results["documents"][0]
    metadatas = results["metadatas"][0]
    distances = results["distances"][0]

    if not docs:
        return {
            "answer": "I don't know based on the provided documents.",
            "sources": [],
            "confidence": 0,
            "confidence_label": "Low"
        }

    best_distance = distances[0]
    similarity = max(0, 1 - best_distance)

    if similarity < CONFIDENCE_THRESHOLD:
        return {
            "answer": "I don't know based on the provided documents.",
            "sources": [],
            "confidence": round(similarity * 100, 1),
            "confidence_label": get_confidence_label(similarity)
        }

    context = "\n\n".join(
        f"[Source: {m['source']}, Page {m['page_number']}]\n{d}"
        for d, m in zip(docs, metadatas)
    )

    prompt = f"""Answer the question using ONLY the context below. 
Do not use any outside knowledge. 
If the answer is not present in the context, respond exactly with: "I don't know based on the provided documents."

Context:
{context}

Question: {question}

Answer:"""

    models_to_try = ["llama-3.3-70b-versatile", "llama-3.1-8b-instant"]
    answer_text = None
    last_error = None

    for model_name in models_to_try:
        for attempt in range(2):
            try:
                response = groq_client.chat.completions.create(
                    model=model_name,
                    messages=[{"role": "user", "content": prompt}],
                )
                answer_text = response.choices[0].message.content.strip()
                break
            except Exception as e:
                last_error = e
                print(f"GROQ ERROR ({model_name}, attempt {attempt + 1}):", e)
                time.sleep(1.5)
        if answer_text:
            break

    if not answer_text:
        return {
            "answer": f"Sorry, the AI service is temporarily unavailable. Please try again in a moment. (Error: {type(last_error).__name__})",
            "sources": [],
            "confidence": 0,
            "confidence_label": "Low"
        }

    seen = set()
    sources = []
    for m in metadatas:
        key = (m["source"], m["page_number"])
        if key not in seen:
            seen.add(key)
            sources.append({"source": m["source"], "page": m["page_number"]})

    return {
        "answer": answer_text,
        "sources": sources,
        "confidence": round(similarity * 100, 1),
        "confidence_label": get_confidence_label(similarity)
    }

if __name__ == "__main__":
    print("=== Test 1: In-scope question ===")
    result = answer_question("What is the objective of this assessment?")
    print("Answer:", result["answer"])
    print("Confidence:", result["confidence"], "%")
    print("Sources:", result["sources"])

    print("\n=== Test 2: Out-of-scope question ===")
    result = answer_question("What is the capital of France?")
    print("Answer:", result["answer"])
    print("Confidence:", result["confidence"], "%", f"({result['confidence_label']})")