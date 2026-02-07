# =============================================================================
# JobFit AI — Backend Dockerfile (Multi-Stage)
# =============================================================================

# --- Base stage: shared dependencies ---
FROM python:3.11-slim AS base
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# --- Development stage ---
FROM base AS dev
COPY . .
EXPOSE 8000 5678
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# --- Production stage ---
FROM base AS prod
COPY . .
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
