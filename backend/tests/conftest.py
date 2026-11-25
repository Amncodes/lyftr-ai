import os
from unittest.mock import MagicMock
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import litellm

# Set test environment variables before importing app
os.environ["LLM_API_KEYS"] = "test_key_1,test_key_2"
os.environ["LLM_MODEL"] = "openai/gpt-4o-mini"
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["ENABLE_FAILURE_SIMULATION"] = "true"
os.environ["LITELLM_CACHE_ENABLED"] = "true"

from app.config import settings
from app.database import Base, get_db
from app.main import app

# Test SQLite in-memory engine with StaticPool
TEST_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def clear_cache():
    if litellm.cache and hasattr(litellm.cache, "cache"):
        if hasattr(litellm.cache.cache, "flush_cache"):
            try:
                litellm.cache.cache.flush_cache()
            except Exception:
                pass
        if hasattr(litellm.cache.cache, "cache_dict"):
            litellm.cache.cache.cache_dict.clear()


@pytest.fixture(autouse=True)
def setup_test_db():
    Base.metadata.create_all(bind=engine)
    clear_cache()
    yield
    Base.metadata.drop_all(bind=engine)
    clear_cache()


@pytest.fixture
def db_session():
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def make_mock_llm_response(content: str = "Test LLM reply", prompt_tokens: int = 15, completion_tokens: int = 8):
    mock_resp = MagicMock()
    mock_choice = MagicMock()
    mock_choice.message.content = content
    mock_resp.choices = [mock_choice]
    mock_usage = MagicMock()
    mock_usage.prompt_tokens = prompt_tokens
    mock_usage.completion_tokens = completion_tokens
    mock_resp.usage = mock_usage
    return mock_resp
