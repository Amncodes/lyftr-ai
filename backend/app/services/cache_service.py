import hashlib
import json
import logging
from typing import Any, Dict, List, Optional
import litellm
from litellm.caching import Cache
from app.config import settings

logger = logging.getLogger(__name__)

# Suppress noisy external lookups in isolated environments
litellm.suppress_debug_info = True
litellm.turn_off_message_logging = True

# Initialize LiteLLM Cache (LiteLLM uses Cache(type="local") for in-process memory caching)
litellm_cache_instance: Optional[Cache] = None

if settings.LITELLM_CACHE_ENABLED:
    try:
        litellm_cache_instance = Cache(type="local")
        litellm.cache = litellm_cache_instance
        logger.info("LiteLLM local cache initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize LiteLLM cache: {e}")
        litellm.cache = None
else:
    litellm.cache = None


def generate_cache_key(model: str, messages: List[Dict[str, str]]) -> str:
    """
    Deterministic cache key that strictly distinguishes:
    - Model
    - System prompt (if included in messages)
    - Full message history
    - New user message
    """
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
        cache_obj = getattr(litellm.cache, "cache", litellm.cache)
        cached_val = None
        if hasattr(cache_obj, "get_cache"):
            cached_val = cache_obj.get_cache(cache_key)
        elif hasattr(cache_obj, "get"):
            cached_val = cache_obj.get(cache_key)

        if cached_val is not None:
            if isinstance(cached_val, str):
                return json.loads(cached_val)
            return cached_val
    except Exception as e:
        logger.warning(f"Error accessing cache: {e}")
    return None


def set_cached_response(cache_key: str, data: Dict[str, Any]) -> None:
    """Store response in LiteLLM cache."""
    if not settings.LITELLM_CACHE_ENABLED or not litellm.cache:
        return
    try:
        cache_obj = getattr(litellm.cache, "cache", litellm.cache)
        val_str = json.dumps(data)
        if hasattr(cache_obj, "set_cache"):
            cache_obj.set_cache(cache_key, val_str)
        elif hasattr(cache_obj, "set"):
            cache_obj.set(cache_key, val_str)
    except Exception as e:
        logger.warning(f"Error setting cache: {e}")
