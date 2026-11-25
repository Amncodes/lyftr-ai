import hashlib
import json
import logging
from typing import Any, Dict, List, Optional
import litellm
from litellm.caching import Cache
from app.config import settings

logger = logging.getLogger(__name__)

# Suppress external model cost map fetching in isolated/offline environments
litellm.suppress_debug_info = True
litellm.turn_off_message_logging = True

# Initialize LiteLLM Cache
litellm_cache_instance: Optional[Cache] = None

if settings.LITELLM_CACHE_ENABLED:
    try:
        litellm_cache_instance = Cache(type="local")
        litellm.cache = litellm_cache_instance
        logger.info("LiteLLM Cache (local) initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize LiteLLM cache: {e}")
        litellm.cache = None
else:
    litellm.cache = None


def generate_cache_key(model: str, messages: List[Dict[str, str]]) -> str:
    """
    Generates a deterministic cache key using LiteLLM's native cache key generator
    which strictly distinguishes:
    - Model
    - System prompt (if included in messages)
    - Full prior message history
    - Current new user message
    """
    if litellm.cache and hasattr(litellm.cache, "get_cache_key"):
        try:
            return litellm.cache.get_cache_key(model=model, messages=messages)
        except Exception:
            pass

    # Deterministic fallback hashing canonical payload
    canonical_payload = {
        "model": model,
        "messages": [
            {"role": m.get("role"), "content": m.get("content")} for m in messages
        ],
    }
    dumped = json.dumps(canonical_payload, sort_keys=True)
    return hashlib.sha256(dumped.encode("utf-8")).hexdigest()


def get_cached_response(cache_key: str) -> Optional[Dict[str, Any]]:
    """Retrieve response from LiteLLM cache if present."""
    if not settings.LITELLM_CACHE_ENABLED or not litellm.cache:
        return None
    try:
        # Native LiteLLM Cache method
        val = litellm.cache.get_cache(cache_key=cache_key)
        if val is not None:
            if isinstance(val, str):
                return json.loads(val)
            return val
    except Exception as e:
        logger.warning(f"Error accessing LiteLLM cache: {e}")
    return None


def set_cached_response(cache_key: str, data: Dict[str, Any]) -> None:
    """Store response in LiteLLM cache."""
    if not settings.LITELLM_CACHE_ENABLED or not litellm.cache:
        return
    try:
        # Native LiteLLM Cache method
        litellm.cache.add_cache(result=data, cache_key=cache_key)
    except Exception as e:
        logger.warning(f"Error setting LiteLLM cache: {e}")
