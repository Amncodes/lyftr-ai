from unittest.mock import patch
from tests.conftest import make_mock_llm_response


def test_unknown_session_returns_404(client):
    response = client.get("/sessions/nonexistent-session-id/messages")
    assert response.status_code == 404
    assert response.json() == {"detail": "Session 'nonexistent-session-id' not found"}


def test_session_history_retrieval_and_isolation(client):
    mock_resp_1 = make_mock_llm_response("Hello from session A", 12, 6)
    mock_resp_2 = make_mock_llm_response("Hello from session B", 14, 7)

    with patch("litellm.completion") as mock_comp:
        mock_comp.side_effect = [mock_resp_1, mock_resp_2]

        # Post to Session A
        client.post(
            "/chat",
            json={"session_id": "session-A", "message": "Message for A"},
        )

        # Post to Session B
        client.post(
            "/chat",
            json={"session_id": "session-B", "message": "Message for B"},
        )

        # Retrieve Session A history
        resp_a = client.get("/sessions/session-A/messages")
        assert resp_a.status_code == 200
        data_a = resp_a.json()
        assert data_a["session_id"] == "session-A"
        assert len(data_a["messages"]) == 2
        assert data_a["messages"][0]["role"] == "user"
        assert data_a["messages"][0]["content"] == "Message for A"
        assert data_a["messages"][1]["role"] == "assistant"
        assert data_a["messages"][1]["content"] == "Hello from session A"
        assert data_a["messages"][1]["metadata"]["resolution_source"] == "LIVE_INFERENCE"

        # Retrieve Session B history
        resp_b = client.get("/sessions/session-B/messages")
        assert resp_b.status_code == 200
        data_b = resp_b.json()
        assert data_b["session_id"] == "session-B"
        assert len(data_b["messages"]) == 2
        assert data_b["messages"][0]["role"] == "user"
        assert data_b["messages"][0]["content"] == "Message for B"
        assert data_b["messages"][1]["role"] == "assistant"
        assert data_b["messages"][1]["content"] == "Hello from session B"


def test_system_prompt_never_exposed_in_history(client):
    mock_resp = make_mock_llm_response("I am concise.", 15, 5)

    with patch("litellm.completion", return_value=mock_resp):
        client.post(
            "/chat",
            json={
                "session_id": "session-sys-test",
                "message": "Hi",
                "system_prompt": "You are a secret pirate assistant.",
            },
        )

        resp = client.get("/sessions/session-sys-test/messages")
        assert resp.status_code == 200
        messages = resp.json()["messages"]
        for msg in messages:
            assert msg["role"] != "system"
            assert "secret pirate assistant" not in msg["content"]
