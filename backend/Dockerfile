# Production Dockerfile for CodeSentinel FastAPI backend — T-174
# Multi-stage build: build stage installs deps, runtime stage is minimal.

# ── Stage 1: Build ────────────────────────────────────────────────────────────
FROM python:3.12-slim AS builder

WORKDIR /build

# Install build tools (needed for some C-extension packages)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    git \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt


# ── Stage 2: Runtime ──────────────────────────────────────────────────────────
FROM python:3.12-slim AS runtime

# Install runtime-only system deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install security scanners
RUN pip install semgrep --no-cache-dir

# Copy Python packages from builder
COPY --from=builder /root/.local /home/appuser/.local

# Create non-root user — T-174 requirement
RUN useradd -m -u 1001 -s /bin/bash appuser

WORKDIR /app

# Copy application code
COPY --chown=appuser:appuser . .

# Ensure local pip packages are on PATH
ENV PATH="/home/appuser/.local/bin:$PATH"
ENV PYTHONPATH="/app"
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
