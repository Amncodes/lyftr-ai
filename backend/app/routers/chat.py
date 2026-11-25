import json
from typing import Optional
from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.config import settings
from app.database import get_db
from app.schemas import (
    ChatMetadata,
    ChatRequest,
    ChatResponse,
    HealthResponse,
    MessageHistoryItem,
    SessionMessagesResponse,
)
from app.services.llm_service import execute_llm_request
from app.services.session_service import (
    get_session_messages,
    save_chat_turn,
    session_exists,
)

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
def get_health(db: Session = Depends(get_db)):
    """
    Health check endpoint:
    Returns status: "ok" only when database is reachable and key pool is loaded.
    """
    keys_configured = len(settings.key_pool)
    if keys_configured == 0:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="No LLM API keys configured",
        )

    try:
        db.execute(text("SELECT 1"))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database connection error: {str(e)}",
        )

    return HealthResponse(
        status="ok",
        keys_configured=keys_configured,
        cache_enabled=settings.LITELLM_CACHE_ENABLED,
    )


@router.post("/chat", response_model=ChatResponse)
def post_chat(
    request: ChatRequest,
    x_simulate_failure: Optional[str] = Header(None, alias="X-Simulate-Failure"),
    db: Session = Depends(get_db),
):
    """
    Chat endpoint with multi-key failover and LiteLLM response caching.
    """
    session_id = request.session_id
    user_content = request.message

    # 1. Fetch message history for session context (oldest first)
    past_messages = get_session_messages(db, session_id)

    # 2. Build LLM prompt messages
    llm_messages = []
    if request.system_prompt:
        llm_messages.append({"role": "system", "content": request.system_prompt})

    for pm in past_messages:
        llm_messages.append({"role": pm.role, "content": pm.content})

    llm_messages.append({"role": "user", "content": user_content})

    # 3. Execute LLM request (handles caching, failover, simulation)
    reply_text, metadata = execute_llm_request(
        llm_messages,
        simulate_failure_header=x_simulate_failure,
    )

    # 4. Save turn to database only on success
    assistant_meta_dict = metadata.model_dump()
    save_chat_turn(
        db=db,
        session_id=session_id,
        user_content=user_content,
        assistant_content=reply_text,
        assistant_metadata=assistant_meta_dict,
    )

    return ChatResponse(
        session_id=session_id,
        reply=reply_text,
        metadata=metadata,
    )


@router.get("/sessions/{session_id}/messages", response_model=SessionMessagesResponse)
def get_session_history(session_id: str, db: Session = Depends(get_db)):
    """
    Retrieves full chat history for a session (oldest first).
    Returns 404 if session not found.
    Never exposes system prompts.
    """
    if not session_exists(db, session_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session '{session_id}' not found",
        )

    messages = get_session_messages(db, session_id)
    history_items = []

    for msg in messages:
        meta_dict = None
        if msg.metadata_json:
            try:
                full_meta = json.loads(msg.metadata_json)
                meta_dict = {
                    "resolution_source": full_meta.get("resolution_source"),
                    "input_tokens": full_meta.get("input_tokens"),
                    "output_tokens": full_meta.get("output_tokens"),
                }
            except Exception:
                meta_dict = None

        history_items.append(
            MessageHistoryItem(
                role=msg.role,
                content=msg.content,
                metadata=meta_dict,
            )
        )

    return SessionMessagesResponse(
        session_id=session_id,
        messages=history_items,
    )
