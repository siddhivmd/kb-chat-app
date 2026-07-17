# 📄 Knowledge Base Chat

A Retrieval-Augmented Generation (RAG) application that lets users upload PDF documents and ask questions answered strictly from their content. Answers are grounded in the uploaded documents only — if the information isn't present, the app says so instead of hallucinating.

Built as part of an AI/ML Internship Assessment.

---

## Features

- 📤 Upload one or more PDF documents
- 🔍 Automatic text extraction, chunking, and embedding
- 💬 Ask natural-language questions in a chat interface
- 📌 Every answer includes the **source document and page number**
- 📊 Every answer includes a **confidence score** (High / Medium / Low)
- 🚫 Refuses to answer when the information isn't in the documents — no hallucinated responses
- ⚡ Graceful error handling with automatic model fallback if the LLM API has issues

---

## Architecture

```
PDF Upload → Text Extraction → Chunking → Embedding → Vector Store (ChromaDB)
                                                              │
User Question → Embedding → Similarity Search ───────────────┘
                                    │
                        Top-matching chunks + Question
                                    │
                              LLM (Groq / Llama 3.3)
                                    │
                    Answer + Source + Page + Confidence Score
```

**Pipeline steps:**

1. **`extract.py`** — Extracts text from each page of the uploaded PDF using `pdfplumber`, keeping track of page numbers.
2. **`chunk.py`** — Splits page text into overlapping chunks (default: 300 characters, 50-character overlap) so context isn't lost at chunk boundaries.
3. **`store.py`** — Embeds each chunk using a local `sentence-transformers` model (`multi-qa-MiniLM-L6-cos-v1`) and stores the embeddings, along with source/page metadata, in a persistent **ChromaDB** collection.
4. **`query.py`** — Embeds the user's question, retrieves the most similar chunks from ChromaDB, and checks a similarity threshold:
   - If the best match is below the threshold, the app skips the LLM call entirely and returns *"I don't know based on the provided documents."*
   - Otherwise, it builds a context-only prompt and sends it to the LLM, which is instructed to answer **only** from the given context.
5. **`app.py`** — Streamlit interface: sidebar for uploading/processing PDFs, main chat area for asking questions, with sources and confidence shown alongside every answer.

### Design decisions

- **Local embeddings, hosted LLM**: Embeddings run locally (free, fast, no API cost) via `sentence-transformers`; only the final answer generation calls an external LLM.
- **Similarity threshold before calling the LLM**: If retrieval confidence is too low, the app never calls the LLM at all — this is the primary hallucination-prevention mechanism, backed by a strict prompt instruction as a second layer.
- **Confidence score**: Derived directly from vector similarity (cosine distance converted to a 0–100% score), giving users a transparent signal for how grounded an answer is.
- **Model fallback**: The LLM call tries multiple models in sequence, so a transient issue with one model doesn't take down the whole app.

---

## Tech Stack

| Component | Technology |
|---|---|
| Frontend | Streamlit |
| PDF parsing | pdfplumber |
| Embeddings | sentence-transformers (`multi-qa-MiniLM-L6-cos-v1`) |
| Vector store | ChromaDB |
| LLM | Groq API (Llama 3.3 70B) |

---

## Setup & Installation

### 1. Clone the repository

```bash
git clone <your-repo-url>
cd kb-chat-app
```

### 2. Install dependencies

```bash
pip install streamlit pdfplumber sentence-transformers chromadb python-dotenv groq
```

### 3. Set up environment variables

Copy `.env.example` to `.env` and add your API key:

```bash
cp .env.example .env
```

```
GROQ_API_KEY=your_groq_api_key_here
```

Get a free Groq API key at [console.groq.com/keys](https://console.groq.com/keys).

### 4. Run the app

```bash
streamlit run app.py
```

The app will open in your browser at `http://localhost:8501`.

---

## Usage

1. **Upload a PDF** using the sidebar file uploader (multiple files supported).
2. Click **"Process Documents"** — this extracts, chunks, and embeds the content into the vector store.
3. Once processing is complete, ask questions in the chat box at the bottom.
4. Each answer shows:
   - The generated response
   - An expandable **Sources** section listing the document and page number(s) used
   - A **confidence score and label** (High / Medium / Low)
5. If you ask something not covered in the uploaded documents, the app will respond: *"I don't know based on the provided documents."*

---

## Project Structure

```
kb-chat-app/
├── app.py           # Streamlit UI
├── extract.py       # PDF text extraction
├── chunk.py         # Text chunking logic
├── store.py         # Embedding + storing in ChromaDB
├── query.py         # Retrieval + LLM answer generation
├── .env.example     # Environment variable template
├── requirements.txt # Python dependencies
└── README.md
```

---

## Limitations & Future Improvements

- Currently supports PDF only; could be extended to `.docx`, `.txt`, or web pages.
- Chunking is character-based rather than sentence/paragraph-aware — could be improved with semantic chunking.
- No persistent chat history across sessions (resets on app restart).
- Could add support for re-ranking retrieved chunks for improved relevance on longer documents.
