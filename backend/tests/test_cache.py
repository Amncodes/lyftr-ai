import time
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


def test_cache_hit_latency_lower_than_live_inference(client):
    """
    6. Ensure cache-hit latency is lower than the original live request latency.
    """
    def delayed_completion(*args, **kwargs):
        time.sleep(0.04)  # 40ms simulated live network latency
        return make_mock_llm_response("Fast cached reply", 15, 5)

    with patch("litellm.completion", side_effect=delayed_completion):
        r1 = client.post(
            "/chat",
            json={"session_id": "lat-s1", "message": "Benchmark latency question"},
        )
        assert r1.status_code == 200
        latency_live = r1.json()["metadata"]["latency_ms"]

        r2 = client.post(
            "/chat",
            json={"session_id": "lat-s2", "message": "Benchmark latency question"},
        )
        assert r2.status_code == 200
        latency_cache = r2.json()["metadata"]["latency_ms"]

        assert r2.json()["metadata"]["resolution_source"] == "LLM_CACHE"
        assert latency_cache < latency_live


def test_conversation_history_distinguishes_cache_key(client):
    """
    Cache keys must include the complete conversation history.
    Submitting 'Yes' after different conversation histories must never return the same response.
    """
    resp_py = make_mock_llm_response("Python is great for AI.", 25, 8)
    resp_jv = make_mock_llm_response("Java is robust for enterprise.", 25, 8)
    resp_py_yes = make_mock_llm_response("Great, here is Python code.", 35, 10)
    resp_jv_yes = make_mock_llm_response("Great, here is Java code.", 35, 10)

    with patch("litellm.completion") as mock_comp:
        mock_comp.side_effect = [resp_py, resp_py_yes, resp_jv, resp_jv_yes]

        # Session 1: Python conversation
        client.post("/chat", json={"session_id": "s-hist-py", "message": "Do you know Python?"})
        r_py_yes = client.post("/chat", json={"session_id": "s-hist-py", "message": "Yes"})

        # Session 2: Java conversation
        client.post("/chat", json={"session_id": "s-hist-jv", "message": "Do you know Java?"})
        r_jv_yes = client.post("/chat", json={"session_id": "s-hist-jv", "message": "Yes"})

        # Both said 'Yes' as second message, but their conversation history is different!
        assert r_py_yes.json()["reply"] == "Great, here is Python code."
        assert r_jv_yes.json()["reply"] == "Great, here is Java code."
        assert r_py_yes.json()["reply"] != r_jv_yes.json()["reply"]
        assert mock_comp.call_count == 4
