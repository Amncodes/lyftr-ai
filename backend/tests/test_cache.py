from unittest.mock import patch
import litellm
from tests.conftest import make_mock_llm_response


def test_cache_first_request_live_and_second_request_cache_hit(client):
    """
    10. First request returning LIVE_INFERENCE.
    11. Identical request in a new session returning LLM_CACHE.
    17. Cache-hit metadata with key_id=null and fallback_attempts=0.
    """
    mock_resp = make_mock_llm_response("Capital of France is Paris.", 30, 7)

    with patch("litellm.completion", return_value=mock_resp) as mock_comp:
        # First request in session 1
        r1 = client.post(
            "/chat",
            json={"session_id": "cache-s1", "message": "What is the capital of France?"},
        )
        assert r1.status_code == 200
        data1 = r1.json()
        assert data1["metadata"]["resolution_source"] == "LIVE_INFERENCE"
        assert data1["metadata"]["key_id"] == "key_1"
        assert data1["metadata"]["fallback_attempts"] == 0
        assert mock_comp.call_count == 1

        # Second identical request in a NEW session 2
        r2 = client.post(
            "/chat",
            json={"session_id": "cache-s2", "message": "What is the capital of France?"},
        )
        assert r2.status_code == 200
        data2 = r2.json()
        assert data2["reply"] == data1["reply"]
        assert data2["metadata"]["resolution_source"] == "LLM_CACHE"
        assert data2["metadata"]["key_id"] is None
        assert data2["metadata"]["fallback_attempts"] == 0
        assert data2["metadata"]["input_tokens"] == 30
        assert data2["metadata"]["output_tokens"] == 7
        # Litellm completion was not called again
        assert mock_comp.call_count == 1


def test_different_message_does_not_reuse_cache(client):
    """
    12. Different message not using incorrect cache entry.
    """
    mock_resp_1 = make_mock_llm_response("Paris", 20, 5)
    mock_resp_2 = make_mock_llm_response("Berlin", 22, 6)

    with patch("litellm.completion") as mock_comp:
        mock_comp.side_effect = [mock_resp_1, mock_resp_2]

        r1 = client.post(
            "/chat",
            json={"session_id": "s-diff-1", "message": "Capital of France?"},
        )
        assert r1.status_code == 200
        assert r1.json()["reply"] == "Paris"
        assert r1.json()["metadata"]["resolution_source"] == "LIVE_INFERENCE"

        r2 = client.post(
            "/chat",
            json={"session_id": "s-diff-2", "message": "Capital of Germany?"},
        )
        assert r2.status_code == 200
        assert r2.json()["reply"] == "Berlin"
        assert r2.json()["metadata"]["resolution_source"] == "LIVE_INFERENCE"
        assert mock_comp.call_count == 2
