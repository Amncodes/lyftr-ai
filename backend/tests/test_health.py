from unittest.mock import patch
from app.config import settings


def test_health_endpoint_healthy(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["keys_configured"] == len(settings.key_pool)
    assert data["cache_enabled"] is True


def test_health_endpoint_db_failure(client):
    with patch("app.routers.chat.text") as mock_text:
        mock_text.side_effect = Exception("DB Connection Lost")
        response = client.get("/health")
        assert response.status_code == 503
        assert "Database connection error" in response.json()["detail"]


def test_health_endpoint_no_keys(client):
    with patch.object(settings, "LLM_API_KEYS", ""):
        response = client.get("/health")
        assert response.status_code == 503
        assert "No LLM API keys configured" in response.json()["detail"]
