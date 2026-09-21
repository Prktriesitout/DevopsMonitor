"""Metrics exposition tests for the Prometheus endpoint."""

import re

from fastapi.testclient import TestClient

from src.main import app


client = TestClient(app)


def _handler_total(text, handler):
    """Sum http_requests_total samples for a handler path."""
    total = 0.0
    pattern = re.compile(
        r"^http_requests_total\{([^}]*)\}\s+([0-9.eE+-]+)"
    )
    for line in text.splitlines():
        match = pattern.match(line)
        label = 'handler="%s"' % handler
        if match is not None and label in match.group(1):
            total += float(match.group(2))
    return total


def test_metrics_endpoint_exposes_http_metrics():
    """GET /metrics exposes core HTTP request metrics."""
    client.get("/api/data")
    response = client.get("/metrics")
    assert response.status_code == 200
    text = response.text
    assert "http_requests_total" in text
    assert "http_request_duration_seconds" in text


def test_metrics_include_runtime_metrics():
    """GET /metrics exposes Python runtime/process metrics."""
    response = client.get("/metrics")
    assert response.status_code == 200
    text = response.text
    assert any(
        marker in text
        for marker in ("python_info", "python_gc_", "process_")
    )


def test_metrics_increment_after_data_request():
    """Hitting /api/data increments its request counter."""
    before = _handler_total(client.get("/metrics").text, "/api/data")
    assert client.get("/api/data").status_code == 200
    after = _handler_total(client.get("/metrics").text, "/api/data")
    assert after > before


def test_metrics_reflect_simulate_error_requests():
    """Hitting /api/simulate-error increments its counter."""
    before = _handler_total(
        client.get("/metrics").text, "/api/simulate-error"
    )
    assert client.get("/api/simulate-error").status_code == 500
    after = _handler_total(
        client.get("/metrics").text, "/api/simulate-error"
    )
    assert after > before
