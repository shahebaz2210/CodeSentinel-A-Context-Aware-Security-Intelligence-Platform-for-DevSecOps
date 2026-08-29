# Production Dockerfile for CodeSentinel Celery worker — T-175
# Shares the backend Python code; different entrypoint.

FROM python:3.12-slim AS builder

WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    git \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt


FROM python:3.12-slim AS runtime

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install security scanners used by Agent 2
RUN pip install semgrep --no-cache-dir

COPY --from=builder /root/.local /home/worker/.local

RUN useradd -m -u 1001 -s /bin/bash worker

WORKDIR /app

# Copy backend application code
COPY --chown=worker:worker backend/ ./
# Copy workers package
COPY --chown=worker:worker workers/ ./workers/

ENV PATH="/home/worker/.local/bin:$PATH"
ENV PYTHONPATH="/app"
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

USER worker

# T-175: Celery worker entrypoint
CMD ["celery", "-A", "workers.celery_app", "worker", \
     "--loglevel=info", \
     "--concurrency=2", \
     "--queues=scans,validations,default", \
     "--max-tasks-per-child=50"]
