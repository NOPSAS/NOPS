FROM python:3.12-slim AS base

# Systemavhengigheter (trengs for psycopg2-binary, Pillow, osv.)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Kopier og installer avhengigheter separat for å utnytte Docker cache-lag
# Build context is project root, so paths are relative to project root
COPY apps/api/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

ENV PYTHONPATH=/app:/app/services

# -----------------------------------------------------------------------------
# Produksjonsbilde
# -----------------------------------------------------------------------------
FROM base AS production

RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*

COPY apps/api/ .
COPY services/ /app/services/

# Ikke kjør som root i produksjon
RUN useradd -m -u 1001 byggsjekk && chown -R byggsjekk:byggsjekk /app
USER byggsjekk

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]

# -----------------------------------------------------------------------------
# Utviklingsbilde (brukes av docker-compose.dev.yml)
# Hot-reload via volummontering og --reload-flagget
# -----------------------------------------------------------------------------
FROM base AS development

# Installer dev-avhengigheter
COPY apps/api/requirements-dev.txt* ./
RUN if [ -f requirements-dev.txt ]; then pip install --no-cache-dir -r requirements-dev.txt; fi

COPY apps/api/ .
COPY services/ /app/services/

EXPOSE 8000

CMD ["uvicorn", "main:app", "--reload", "--host", "0.0.0.0", "--port", "8000"]
