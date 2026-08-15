# ── Build stage ────────────────────────────────────────────
FROM python:3.12-slim

WORKDIR /app

# Install dependencies first so Docker caches this layer
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Railway injects $PORT at runtime; fall back to 8000 for local Docker runs
CMD python -m uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
