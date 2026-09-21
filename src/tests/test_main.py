"""Endpoint unit tests for the FastAPI service."""

from datetime import datetime

from fastapi.testclient import TestClient

from src.main import app


client = TestClient(app)


def test_health_endpoint():
    """GET /api/health returns healthy status and timestamp."""
    response = client.get("/api/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "healthy"
    assert "timestamp" in payload
    parsed = datetime.fromisoformat(
        payload["timestamp"].replace("Z", "+00:00")
    )
    assert parsed.tzinfo is not None


def test_data_endpoint():
    """GET /api/data returns the mock operational payload."""
    response = client.get("/api/data")
    assert response.status_code == 200
    payload = response.json()
    assert payload["service"] == "devops-monitored-app"
    assert payload["status"] == "active"
    assert payload["items_processed"] == 100


def test_simulate_error_endpoint():
    """GET /api/simulate-error returns HTTP 500 with detail."""
    response = client.get("/api/simulate-error")
    assert response.status_code == 500
    payload = response.json()
    assert payload["detail"] == "Simulated Database Timeout"
