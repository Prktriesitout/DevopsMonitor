"""Unit tests for the fun demo endpoints."""

from fastapi.testclient import TestClient

from src.main import app


client = TestClient(app)


def test_landing_page():
    """GET / returns HTML with interactive buttons."""
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "Health Check" in response.text
    assert "/api/health" in response.text


def test_joke_endpoint():
    """GET /api/joke returns a JSON object with a joke."""
    response = client.get("/api/joke")
    assert response.status_code == 200
    payload = response.json()
    assert "joke" in payload
    assert isinstance(payload["joke"], str)
    assert len(payload["joke"]) > 0


def test_quote_endpoint():
    """GET /api/quote returns a quote and author."""
    response = client.get("/api/quote")
    assert response.status_code == 200
    payload = response.json()
    assert "quote" in payload
    assert "author" in payload
    assert isinstance(payload["quote"], str)
    assert isinstance(payload["author"], str)


def test_dice_default_sides():
    """GET /api/dice returns result between 1 and 6 by default."""
    response = client.get("/api/dice")
    assert response.status_code == 200
    payload = response.json()
    assert payload["sides"] == 6
    assert 1 <= payload["result"] <= 6


def test_dice_custom_sides():
    """GET /api/dice?sides=20 returns result between 1 and 20."""
    response = client.get("/api/dice?sides=20")
    assert response.status_code == 200
    payload = response.json()
    assert payload["sides"] == 20
    assert 1 <= payload["result"] <= 20


def test_dice_invalid_sides_too_low():
    """GET /api/dice?sides=1 returns 422 (validation error)."""
    response = client.get("/api/dice?sides=1")
    assert response.status_code == 422


def test_dice_invalid_sides_too_high():
    """GET /api/dice?sides=101 returns 422 (validation error)."""
    response = client.get("/api/dice?sides=101")
    assert response.status_code == 422


def test_coinflip():
    """GET /api/coinflip returns heads or tails."""
    response = client.get("/api/coinflip")
    assert response.status_code == 200
    payload = response.json()
    assert payload["result"] in ("heads", "tails")


def test_fortune():
    """GET /api/fortune returns a fortune string."""
    response = client.get("/api/fortune")
    assert response.status_code == 200
    payload = response.json()
    assert "fortune" in payload
    assert isinstance(payload["fortune"], str)
    assert len(payload["fortune"]) > 0


def test_fun_stats_increments():
    """fun-stats counter increments with fun requests."""
    stats_before = client.get(
        "/api/fun-stats"
    ).json()
    count_before = stats_before[
        "fun_requests_served"
    ]

    client.get("/api/joke")
    client.get("/api/coinflip")

    stats_after = client.get(
        "/api/fun-stats"
    ).json()
    assert stats_after[
        "fun_requests_served"
    ] >= count_before + 2


def test_existing_health_unchanged():
    """GET /api/health still works identically."""
    response = client.get("/api/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "healthy"


def test_existing_data_unchanged():
    """GET /api/data still works identically."""
    response = client.get("/api/data")
    assert response.status_code == 200
    payload = response.json()
    assert payload["service"] == "devops-monitored-app"


def test_existing_simulate_error_unchanged():
    """GET /api/simulate-error still returns 500."""
    response = client.get("/api/simulate-error")
    assert response.status_code == 500
    payload = response.json()
    assert payload["detail"] == "Simulated Database Timeout"
