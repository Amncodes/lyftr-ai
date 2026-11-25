from unittest.mock import patch
from tests.conftest import make_mock_llm_response


def test_successful_chat_response(client):
    mock_resp = make_mock_llm_response("Paris is the capital of France.", 42, 9)
    with patch("litellm.completion", return_value=mock_resp):
        payload = {
            "session_id": "test-session-1",
            "message": "What is the capital of France?",
        }
        response = client.post("/chat", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["session_id"] == "test-session-1"
        assert data["reply"] == "Paris is the capital of France."
        meta = data["metadata"]
        assert meta["resolution_source"] == "LIVE_INFERENCE"
        assert meta["model"] == "openai/gpt-4o-mini"
        assert meta["latency_ms"] >= 0
        assert meta["input_tokens"] == 42
        assert meta["output_tokens"] == 9
        assert meta["key_id"] == "key_1"
        assert meta["fallback_attempts"] == 0


def test_missing_message_validation(client):
    payload = {"session_id": "test-session-2"}
    response = client.post("/chat", json=payload)
    assert response.status_code == 422


def test_empty_message_validation(client):
    payload = {"session_id": "test-session-3", "message": "   "}
    response = client.post("/chat", json=payload)
    assert response.status_code == 422


def test_message_exceeding_4000_chars(client):
    payload = {"session_id": "test-session-4", "message": "a" * 4001}
    response = client.post("/chat", json=payload)
    assert response.status_code == 422


def test_correct_per_request_token_metadata(client):
    mock_resp = make_mock_llm_response("Hello user", prompt_tokens=55, completion_tokens=12)
    with patch("litellm.completion", return_value=mock_resp):
        payload = {"session_id": "test-tokens-1", "message": "Hello"}
        response = client.post("/chat", json=payload)
        assert response.status_code == 200
        meta = response.json()["metadata"]
        assert meta["input_tokens"] == 55
        assert meta["output_tokens"] == 12


def test_multi_turn_conversation_context(client):
    mock_resp_1 = make_mock_llm_response("I am an AI assistant.", 10, 8)
    mock_resp_2 = make_mock_llm_response("Your name is Alice.", 25, 6)

    with patch("litellm.completion") as mock_completion:
        mock_completion.side_effect = [mock_resp_1, mock_resp_2]

        # First turn
        r1 = client.post("/chat", json={"session_id": "s-multi", "message": "My name is Alice."})
        assert r1.status_code == 200

        # Second turn
        r2 = client.post("/chat", json={"session_id": "s-multi", "message": "What is my name?"})
        assert r2.status_code == 200

        # Verify that mock_completion received past messages on the second turn
        call_args = mock_completion.call_args_list[1]
        sent_messages = call_args.kwargs["messages"]
        assert len(sent_messages) == 3
        assert sent_messages[0] == {"role": "user", "content": "My name is Alice."}
        assert sent_messages[1] == {"role": "assistant", "content": "I am an AI assistant."}
        assert sent_messages[2] == {"role": "user", "content": "What is my name?"}
