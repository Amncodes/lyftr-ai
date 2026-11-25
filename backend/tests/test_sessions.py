import json
import tempfile
from pathlib import Path
from unittest.mock import patch
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app.models import Message
from app.services.session_service import get_session_messages, save_chat_turn
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


def test_sqlite_persistence_across_connection_restarts():
    """
    8. The Docker named volume must preserve SQLite history.
    Verifies that SQLite data written to a file persists when connections close and reopen.
    """
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = tmp.name

    try:
        engine1 = create_engine(f"sqlite:///{db_path}")
        Base.metadata.create_all(bind=engine1)
        Session1 = sessionmaker(bind=engine1)

        # Write data in session 1
        with Session1() as s1:
            save_chat_turn(
                db=s1,
                session_id="persistent-session-123",
                user_content="Persist this message",
                assistant_content="This message will persist",
                assistant_metadata={"resolution_source": "LIVE_INFERENCE", "input_tokens": 5, "output_tokens": 5},
            )

        # Completely close and dispose engine 1 (simulating process/container restart)
        engine1.dispose()

        # Reopen database with a new engine
        engine2 = create_engine(f"sqlite:///{db_path}")
        Session2 = sessionmaker(bind=engine2)

        with Session2() as s2:
            messages = get_session_messages(s2, "persistent-session-123")
            assert len(messages) == 2
            assert messages[0].role == "user"
            assert messages[0].content == "Persist this message"
            assert messages[1].role == "assistant"
            assert messages[1].content == "This message will persist"
            meta = json.loads(messages[1].metadata_json)
            assert meta["resolution_source"] == "LIVE_INFERENCE"

        engine2.dispose()
    finally:
        Path(db_path).unlink(missing_ok=True)
