from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field, field_validator


class ChatRequest(BaseModel):
    session_id: str = Field(..., min_length=1, max_length=128)
    message: str = Field(..., min_length=1)
    system_prompt: Optional[str] = None

    @field_validator("session_id")
    @classmethod
    def validate_session_id(cls, v: str) -> str:
        s = v.strip()
        if not s or len(s) > 128:
            raise ValueError("session_id must be between 1 and 128 characters")
        return s

    @field_validator("message")
    @classmethod
    def validate_message(cls, v: str) -> str:
        s = v.strip()
        if not s:
            raise ValueError("Message cannot be empty")
        if len(s) > 4000:
            raise ValueError("Message cannot exceed 4000 characters after trimming")
        return s


class ChatMetadata(BaseModel):
    resolution_source: Literal["LIVE_INFERENCE", "LLM_CACHE"]
    model: str
    latency_ms: int
    input_tokens: int
    output_tokens: int
    key_id: Optional[str] = None
    fallback_attempts: int = 0


class ChatResponse(BaseModel):
    session_id: str
    reply: str
    metadata: ChatMetadata


class MessageHistoryMetadata(BaseModel):
    resolution_source: Optional[str] = None
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None


class MessageHistoryItem(BaseModel):
    role: str
    content: str
    metadata: Optional[Dict[str, Any]] = None


class SessionMessagesResponse(BaseModel):
    session_id: str
    messages: List[MessageHistoryItem]


class HealthResponse(BaseModel):
    status: str
    keys_configured: int
    cache_enabled: bool
