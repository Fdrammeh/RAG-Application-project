"""
Backend: FastAPI RAG API  (STARTER)
=====================================
Copy your completed my_rag_api.py here as main.py, then adapt it to
read configuration from environment variables via config.py.

Minimum changes from my_rag_api.py:
    1. Import settings from config instead of hardcoding values
       from config import settings
       OLLAMA_URL = settings.ollama_url
       MODEL      = settings.model_name
       DB_PATH    = settings.chroma_path
    2. Ensure the /health endpoint is present (used by the frontend)
    3. The app object must be named `app` (uvicorn main:app)

TODO: Paste your my_rag_api.py content here and make the adjustments above.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, field_validator
import chromadb
import requests
import os
from config import settings

app = FastAPI(title="RAG API", version="1.0")

# TODO: Add CORSMiddleware — allow all origins, methods, headers
app.add_middleware(CORSMiddleware, allow_origins=["*"],
    allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

# ── Config ─────────────────────────────────────────────────────────────────
OLLAMA_URL = settings.OLLAMA_URL
MODEL = settings.MODEL_NAME
DB_PATH = settings.CHROMA_PATH
DOCS_DIR = settings.DOCS_DIRECTORY

# ── ChromaDB setup ─────────────────────────────────────────────────────────
client = chromadb.PersistentClient(path=DB_PATH)
collection = client.get_or_create_collection("documents")


# ── Pydantic schemas ───────────────────────────────────────────────────────

class AskRequest(BaseModel):
    question: str
    n_results: int = 3
    max_distance: float = 1.2

    # TODO: Add a @field_validator("question") that raises ValueError
    #   if the question is an empty string (after stripping whitespace)
@field_validator("question")
@classmethod
def validate_question(cls, value):
    if not value.strip():
        raise ValueError("Question cannot be empty")
    return value

class SourceChunk(BaseModel):
    text: str
    source: str
    distance: float


class AskResponse(BaseModel):
    answer: str
    sources: list[SourceChunk]
    confidence: str


class IngestResponse(BaseModel):
    chunks_ingested: int
    message: str


# ── RAG helpers ────────────────────────────────────────────────────────────
# (Paste / adapt functions from your my_rag.py / rag_pipeline.py)

SYSTEM_PROMPT = (
    "You are a helpful AI assistant. Answer ONLY from the provided context. "
    "If the context doesn't contain the answer, say you don't have enough "
    "information. Cite source documents by name. Keep responses under 200 words."
)


def load_documents(directory: str) -> list[dict]:
  # TODO: copy from previous exercises

    documents= []
    for filename in sorted(os.listdir(directory)):
        if filename.endswith(('.txt', '.md')):
            with open(os.path.join(directory, filename), 'r') as f:
                content = f.read()
            # Split by paragraphs for chunking
            paragraphs = [p.strip() for p in content.split('\\n\\n') if p.strip()]
            for i, para in enumerate(paragraphs):
                documents.append({
                    "text": para,
                    "id": f"{filename}_{i}",
                    "metadata": {"source": filename, "chunk_index": str(i)}
                })
    return documents


def retrieve(
        query: str, 
        n_results: int = 3, 
        max_distance: float = 1.2
        ) -> list[dict]:
    """Query ChromaDB, filter by max_distance, return chunk dicts."""

    if collection.count() == 0:
        return []
    
    results = collection.query(
        query_texts=[query],
        n_results=min(n_results, collection.count())
    )

    chunks = []
    for i in range(len(results['documents'][0])):
        chunks.append({
            "text": results['documents'][0][i],
            "metadata": results['metadatas'][0][i],
            "distance": results['distances'][0][i]
        })
    return chunks



def compute_confidence(chunks: list[dict]) -> str:
     # TODO: "high" / "medium" / "low" based on best distance
    if not chunks:
        return "low"
    best_distance = min(chunk["distance"] for chunk in chunks)
    
    if best_distance < 0.5:
        return "high"
    elif best_distance < 1.0:
        return "medium"
    else:
        return "low"


def call_ollama(messages: list[dict]) -> str:
    """Call Ollama (non-streaming). Raise HTTPException 503 if unreachable."""
    # TODO: POST to Ollama
    # TODO: Catch ConnectionError → raise HTTPException(status_code=503, detail="...")
     # TODO

    try:
        response = requests.post(f"{OLLAMA_URL}/api/chat", json={
            "model": MODEL,
            "messages": messages,
            "stream": False
        })
        response.raise_for_status()
        return response.json()["message"]["content"]
    except requests.exceptions.ConnectionError:
        raise HTTPException(status_code=503, detail="Ollama is not running")
 


def check_ollama_health() -> bool:
    """Return True if Ollama is reachable, False otherwise."""
    # TODO: GET {OLLAMA_URL}/api/tags — return True on 200, False on ConnectionError
    try:
        response = requests.get(f"{OLLAMA_URL}/api/tags")
    except requests.exceptions.ConnectionError:
        return False
    return response.status_code == 200



# ── Endpoints ──────────────────────────────────────────────────────────────

@app.post("/ask", response_model=AskResponse)
def ask(req: AskRequest):
    """Retrieve context and generate a grounded answer."""
    # TODO: retrieve() with req.n_results and req.max_distance
    # TODO: If no chunks, return AskResponse with a "no documents" message,
    #       empty sources, confidence "low"
    # TODO: Build messages (SYSTEM_PROMPT + context + question)
    # TODO: call_ollama() — may raise 503
    # TODO: Return AskResponse with answer, sources, confidence
    
    chunks = retrieve(req.question, req.n_results, req.max_distance)

    if not chunks:
        return AskResponse(
            answer="I don't have relevant information to answer that.",
            sources=[], confidence="low"
        )
    confidence = compute_confidence(chunks)

    context = "\n\n".join(
        f"[Source: {chunk['metadata'].get('source', 'unknown')}]\n"
        f"{chunk['text']}"
        for chunk in chunks
    )

    messages = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT
        },
        {
            "role": "user",
            "content": f"Context:\n{context}\n\nQuestion: {req.question}"
        }
    ]

    answer = call_ollama(messages)

    sources = [
        SourceChunk(
            text=chunk["text"],
            source=chunk["metadata"].get("source", "unknown"),
            distance=round(chunk["distance"], 4)
        )
        for chunk in chunks
    ]

    return AskResponse(
        answer=answer,
        sources=sources,
        confidence=confidence
    )


@app.post("/ingest", response_model=IngestResponse)
def ingest():
    """Load documents from docs/ into ChromaDB."""
    # TODO: load_documents(DOCS_DIR)
    # TODO: collection.upsert(...)
    # TODO: Return IngestResponse with chunks_ingested and a message
    
    documents = load_documents(DOCS_DIR)
    collection.upsert(
        ids=[doc["id"] for doc in documents],
        documents=[doc["text"] for doc in documents],
        metadatas=[doc["metadata"] for doc in documents])

    return IngestResponse(
        chunks_ingested=len(documents),
        message=f"Ingested {len(documents)} chunks from {DOCS_DIR}."
    )

@app.get("/")
def root():
    return {"message": "RAG API is running"}

@app.get("/stats")
def stats():
    """Return document count and model info."""
    # TODO: return {"document_count": collection.count(), "model": MODEL, "db_path": DB_PATH}
    return {
        "document_count": collection.count(),
        "model": MODEL,
        "db_path": DB_PATH
    }


@app.get("/health")
def health():
    """Check ChromaDB and Ollama liveness."""
    # TODO: Try collection.count() → chromadb status "ok" or "error"
    # TODO: check_ollama_health() → ollama status "connected" or "disconnected"
    # TODO: overall status "ok" only if both are healthy
    # TODO: return {"status": ..., "chromadb": ..., "ollama": ..., "document_count": ...}
    
    try:
        collection.count()
        chromadb_status = "ok"
    except Exception:
        chromadb_status = "error"

    # Check Ollama
    ollama_ok = check_ollama_health()
    ollama_status = "connected" if ollama_ok else "disconnected"

    # Overall status
    overall_status = (
        "ok"
        if chromadb_status == "ok" and ollama_ok
        else "error"
    )

    return {
        "status": overall_status,
        "chromadb": chromadb_status,
        "ollama": ollama_status,
        "document_count": collection.count()
    }
    
