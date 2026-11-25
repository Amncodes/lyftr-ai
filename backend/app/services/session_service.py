import json
from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy.orm import Session
from app.models import Message


def session_exists(db: Session, session_id: str) -> bool:
    return db.query(Message).filter(Message.session_id == session_id).first() is not None


def get_session_messages(db: Session, session_id: str) -> List[Message]:
    return (
        db.query(Message)
        .filter(Message.session_id == session_id)
        .order_by(Message.id.asc())
        .all()
    )


def save_chat_turn(
    db: Session,
    session_id: str,
    user_content: str,
    assistant_content: str,
    assistant_metadata: dict,
) -> None:
    now_iso = datetime.now(timezone.utc).isoformat()

    # User message
    user_msg = Message(
        session_id=session_id,
        role="user",
        content=user_content,
        metadata_json=None,
        created_at=now_iso,
    )
    db.add(user_msg)

    # Assistant message
    assistant_msg = Message(
        session_id=session_id,
        role="assistant",
        content=assistant_content,
        metadata_json=json.dumps(assistant_metadata),
        created_at=now_iso,
    )
    db.add(assistant_msg)
    db.commit()
