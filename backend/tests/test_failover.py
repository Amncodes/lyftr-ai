from unittest.mock import patch
from tests.conftest import make_mock_llm_response


def test_key_1_failure_with_key_2_fallback(client):
    """
    Test fallback to key_2 when key_1 fails with HTTP 429.
    Should return a real model-generated response with key_id='key_2' and fallback_attempts=1.
    """
    mock_resp = make_mock_llm_response("Fallback response from key 2", prompt_tokens=20, completion_tokens=10)
    with patch("litellm.completion", return_value=mock_resp):
        response = client.post(
            "/chat",
            json={"session_id": "s-failover-1", "message": "Test failover"},
            headers={"X-Simulate-Failure": "key_1=429"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["reply"] == "Fallback response from key 2"
        meta = data["metadata"]
        assert meta["key_id"] == "key_2"
        assert meta["fallback_attempts"] == 1
        assert meta["resolution_source"] == "LIVE_INFERENCE"


def test_all_keys_failing_returns_503(client):
    """
    Test when all configured keys fail (e.g. key_1=429,key_2=500 or *=429),
    backend returns HTTP 503 with {"detail": "all providers unavailable"}.
    """
    response = client.post(
        "/chat",
        json={"session_id": "s-failover-2", "message": "All keys fail"},
        headers={"X-Simulate-Failure": "key_1=429,key_2=500"},
    )
    assert response.status_code == 503
    assert response.json() == {"detail": "all providers unavailable"}

    # Test wildcard failure syntax
    response_star = client.post(
        "/chat",
        json={"session_id": "s-failover-3", "message": "All keys fail wildcard"},
        headers={"X-Simulate-Failure": "*=429"},
    )
    assert response_star.status_code == 503
    assert response_star.json() == {"detail": "all providers unavailable"}


def test_simulated_failures_not_stored_in_history(client):
    """
    Failed requests (HTTP 503) must not be inserted into SQLite history.
    """
    client.post(
        "/chat",
        json={"session_id": "s-failover-not-stored", "message": "Failed message"},
        headers={"X-Simulate-Failure": "*=429"},
    )
    # Checking session history for this session should return 404
    history_resp = client.get("/sessions/s-failover-not-stored/messages")
    assert history_resp.status_code == 404
