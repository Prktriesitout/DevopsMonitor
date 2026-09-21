"""FastAPI service with structured JSON logging and metrics."""

import json
import logging
import sys
import time
import traceback
from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException, Request
from prometheus_fastapi_instrumentator import Instrumentator

try:
    from src.config import get_settings
except ImportError:  # pragma: no cover
    from config import get_settings


settings = get_settings()


class JsonFormatter(logging.Formatter):
    """Format log records as single-line JSON."""

    def format(self, record: logging.LogRecord) -> str:
        """Render record with required telemetry fields."""
        timestamp = datetime.now(timezone.utc).isoformat()
        timestamp = timestamp.replace("+00:00", "Z")
        payload = {
            "timestamp": timestamp,
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "method": getattr(record, "method", "-"),
            "url": getattr(record, "url", "-"),
            "status_code": getattr(record, "status_code", 0),
            "duration_ms": getattr(record, "duration_ms", 0.0),
        }
        if record.exc_info and record.exc_info[0] is not None:
            exc = "".join(traceback.format_exception(*record.exc_info))
            payload["traceback"] = exc
        elif hasattr(record, "traceback"):
            payload["traceback"] = str(getattr(record, "traceback"))
        return json.dumps(payload)


logger = logging.getLogger("app.main")
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(JsonFormatter())
logger.handlers.clear()
logger.addHandler(handler)
logger.setLevel(getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO))
logger.propagate = False

app = FastAPI(title=settings.APP_NAME)

if settings.METRICS_ENABLED:
    Instrumentator().instrument(app).expose(app)


@app.middleware("http")
async def request_logging_middleware(request: Request, call_next):
    """Time requests and emit single-line JSON access logs."""
    start = time.perf_counter()
    try:
        response = await call_next(request)
        duration = round((time.perf_counter() - start) * 1000, 2)
        logger.info(
            "HTTP Request completed",
            extra={
                "method": request.method,
                "url": request.url.path,
                "status_code": response.status_code,
                "duration_ms": duration,
            },
        )
        return response
    except Exception:
        duration = round((time.perf_counter() - start) * 1000, 2)
        logger.error(
            "Unhandled exception",
            extra={
                "method": request.method,
                "url": request.url.path,
                "status_code": 500,
                "duration_ms": duration,
            },
            exc_info=True,
        )
        raise


@app.get("/api/health")
async def health():
    """Return service health with ISO-8601 UTC timestamp."""
    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    return {"status": "healthy", "timestamp": now}


@app.get("/api/data")
async def get_data():
    """Return mock operational data payload."""
    return {
        "service": "devops-monitored-app",
        "status": "active",
        "items_processed": 100,
    }


@app.get("/api/simulate-error")
async def simulate_error(request: Request):
    """Log and raise deterministic HTTP 500 for chaos testing."""
    try:
        raise HTTPException(
            status_code=500, detail="Simulated Database Timeout"
        )
    except HTTPException:
        logger.error(
            "Internal Server Error triggered",
            extra={
                "method": request.method,
                "url": request.url.path,
                "status_code": 500,
                "duration_ms": 0.0,
            },
            exc_info=True,
        )
        raise
