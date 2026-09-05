# Multi-stage production build for PRAMAAN / CARVE-FECL
# Stage 1: Build React Frontend SPA
FROM node:20-alpine AS frontend-builder
WORKDIR /app/frontend

COPY frontend/package*.json ./
RUN npm ci

COPY frontend/ ./
RUN npm run build

# Stage 2: Python Runtime Environment
FROM python:3.10-slim AS runner
WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app/backend:/app \
    DIG_INFERENCE_MODE=offline \
    DIG_DATABASE_PATH=/app/var/demo.sqlite3 \
    PORT=18000

# Install production dependencies
COPY pyproject.toml .
RUN pip install --no-cache-dir fastapi "uvicorn[standard]" pydantic pydantic-settings PyYAML scikit-learn joblib python-multipart httpx

# Copy backend codebase and research assets
COPY backend/ backend/
COPY data/ data/
COPY research/ research/
COPY scripts/ scripts/

# Install local package
RUN pip install --no-cache-dir -e .

# Copy built frontend assets
COPY --from=frontend-builder /app/frontend/dist /app/frontend/dist

# Seed synthetic demo SQLite state on build
RUN mkdir -p /app/var && PYTHONPATH=/app/backend:/app python scripts/seed_demo.py --database /app/var/demo.sqlite3 --reset

EXPOSE 18000 8080 7860 8000
CMD ["sh", "-c", "python -m uvicorn backend.app.main:app --host 0.0.0.0 --port ${PORT:-18000}"]
