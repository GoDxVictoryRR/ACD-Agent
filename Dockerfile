# Dockerfile — Lightweight production container for Ownership Lens
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DATA_SOURCE=icij \
    PORT=8000

WORKDIR /app

# Install runtime dependencies only
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY core/ core/
COPY agent/ agent/
COPY mcp_server/ mcp_server/
COPY api/ api/
COPY web/ web/
COPY data/seed/ data/seed/
COPY data/replay/ data/replay/
COPY data/demo.json data/
COPY data/make_synthetic.py data/
COPY data/load.py data/

# Create non-root user
RUN adduser --disabled-password --gecos "" appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

CMD ["sh", "-c", "uvicorn api.main:app --host 0.0.0.0 --port ${PORT}"]
