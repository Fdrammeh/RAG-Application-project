Configurable RAG Application

A containerized RAG application built with FastAPI, ChromaDB, Ollama, Streamlit, and Docker.
The application retrieves relevant information from documents and uses the Ollama llama3.2:1b model to generate answers based on the retrieved context.
Configuration
Application settings are managed through environment variables using backend/config.py.

Services:
FastAPI: http://localhost:8000
Streamlit: http://localhost:8501
Ollama: http://localhost:11434

Test the Application
Check health:
curl http://localhost:8000/health

API tests are located in backend/tests/test_api.py.
Run locally:
cd backend
pytest tests/ -v
The tests verify /, /health, and /stats.
