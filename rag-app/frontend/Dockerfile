# frontend/Dockerfile  (STARTER)
# ================================
# Build context: ./frontend
# Runs the Streamlit UI

# TODO: FROM python:3.11-slim

FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8501

CMD ["streamlit", "run", "app.py", "--server.address=0.0.0.0", "--server.port=8501"]