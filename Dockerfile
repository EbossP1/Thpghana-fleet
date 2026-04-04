# ─────────────────────────────────────────────────────────────────
# THP Ghana Fleet Management — Dockerfile (Supabase edition)
# No local database — connects to Supabase hosted PostgreSQL
# ─────────────────────────────────────────────────────────────────
FROM python:3.12-slim

RUN apt-get update && \
    apt-get install -y --no-install-recommends libpq5 curl && \
    rm -rf /var/lib/apt/lists/*

RUN groupadd -r fleet && useradd -r -g fleet -d /app -s /sbin/nologin fleet

WORKDIR /app

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir gunicorn

COPY backend/ ./backend/
COPY frontend/ ./frontend/

RUN chown -R fleet:fleet /app

USER fleet

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -sf http://localhost:8000/ || exit 1

EXPOSE 8000

CMD ["gunicorn", "backend.main:app", \
     "-k", "uvicorn.workers.UvicornWorker", \
     "-b", "0.0.0.0:8000", \
     "-w", "2", \
     "--timeout", "120", \
     "--access-logfile", "-", \
     "--error-logfile", "-"]
