# Multi-stage production image for devops-monitored-app.
# Builder compiles wheels; runtime holds only runtime artifacts.

FROM python:3.11-slim AS builder

WORKDIR /app

ENV PIP_NO_CACHE_DIR=1 \
    PYTHONDONTWRITEBYTECODE=1

# Layer-cache ordering: requirements first, source later.
COPY src/requirements.txt ./requirements.txt

RUN pip install --no-cache-dir --upgrade pip \
    && pip wheel --no-cache-dir --wheel-dir /wheels -r ./requirements.txt

FROM python:3.11-slim AS runtime

ENV PIP_NO_CACHE_DIR=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Non-root user/group (UID/GID 10001) + minimal curl for HEALTHCHECK probe.
RUN groupadd -r appgroup \
    && useradd -r -u 10001 -g appgroup appuser \
    && apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install prebuilt wheels from builder stage.
COPY --from=builder /wheels /wheels
COPY src/requirements.txt ./requirements.txt

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir /wheels/* \
    && rm -rf /wheels ./requirements.txt

# Application source owned by non-root user.
COPY --chown=appuser:appgroup src/ ./src/

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=15s --timeout=3s CMD curl -f http://localhost:8000/api/health || exit 1

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
