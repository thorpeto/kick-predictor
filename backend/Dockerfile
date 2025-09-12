FROM python:3.11-slim

WORKDIR /app

# Systemabhängigkeiten installieren
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Kopiere nur die requirements.txt zuerst für besseres Caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Kopiere den Rest des Codes
COPY . .

# GCP liest den Port aus der Umgebungsvariable
ENV PORT=8000

# Health check für Cloud Run
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:${PORT}/health || exit 1

EXPOSE ${PORT}

# Anpassung für GCP: der Port wird als Umgebungsvariable eingelesen
CMD exec uvicorn main:app --host 0.0.0.0 --port ${PORT}
