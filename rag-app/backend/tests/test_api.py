"""
CI Tests: FastAPI RAG API  (STARTER)
======================================
Run locally:
    cd backend
    pip install pytest httpx
    pytest tests/ -v

These tests run in CI (GitHub Actions) on every push.
They test the API layer only — they don't need Ollama or real documents.

Your goal: write 3 tests that verify the API endpoints respond correctly.

Tests to implement:
    test_root()   — GET /  returns 200
    test_health() — GET /health returns 200, response contains "status" or "chromadb"
    test_stats()  — GET /stats returns 200, response contains "document_count"

Key concepts:
    FastAPI TestClient (from httpx under the hood):
        from fastapi.testclient import TestClient
        from main import app

        client = TestClient(app)

        def test_something():
            response = client.get("/endpoint")
            assert response.status_code == 200
            data = response.json()
            assert "expected_key" in data
"""

from fastapi.testclient import TestClient

 
from main import app
client = TestClient(app)


# ── Tests ──────────────────────────────────────────────────────────────────

def test_root():
    """GET / should return 200."""
    response = client.get("/")
    assert response.status_code == 200
    


def test_health():
    """GET /health should return 200 with a status field."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data or "chromadb" in data


def test_stats():
    """GET /stats should return 200 with a document_count field."""
    response = client.get("/stats")
    assert response.status_code == 200
    data = response.json()
    assert "document_count" in data