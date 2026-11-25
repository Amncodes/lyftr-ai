from unittest.mock import patch
import litellm
from app.config import settings
from tests.conftest import make_mock_llm_response


def test_key_1_failure_with_key_2_fallback(client):
    """
    Test fallback to key_2 when key_1 fails with HTTP 429 via X-Simulate-Failure.
    Should return a real model-generated response with key_id='key_2' and fallback_attempts=1.
    """
    mock_resp = make_mock_llm_response("Fallback response from key 2", prompt_tokens=20, completion_tokens=10)
    with patch("litellm.completion", return_value=mock_resp) as mock_comp:
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

        # Verify that the call actually used the second key
        assert mock_comp.call_args.kwargs["api_key"] == settings.key_dict["key_2"]


def test_real_exception_triggers_failover_to_second_key(client):
    """
    Test real exception from provider on key_1 (e.g. RateLimitError/APIError),
    verifying it catches the exception and falls back to key_2 with key_2's actual credentials.
    """
    mock_success_resp = make_mock_llm_response("Recovered via key_2", prompt_tokens=22, completion_tokens=9)

    call_count = 0

    def fail_first_then_succeed(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            # key_1 fails with RateLimitError
            raise litellm.RateLimitError(
                message="Rate limit exceeded",
                llm_provider="openai",
                model="gpt-4o-mini",
            )
        # key_2 succeeds
        return mock_success_resp

    with patch("litellm.completion", side_effect=fail_first_then_succeed) as mock_comp:
        response = client.post(
            "/chat",
            json={"session_id": "s-real-exc-1", "message": "Hello failover"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["reply"] == "Recovered via key_2"
        assert data["metadata"]["key_id"] == "key_2"
        assert data["metadata"]["fallback_attempts"] == 1
        assert mock_comp.call_count == 2
        # First call used key_1, second call used key_2
        assert mock_comp.call_args_list[0].kwargs["api_key"] == settings.key_dict["key_1"]
        assert mock_comp.call_args_list[1].kwargs["api_key"] == settings.key_dict["key_2"]


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
