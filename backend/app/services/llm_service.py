import logging
import time
from typing import Dict, List, Optional, Tuple
from fastapi import HTTPException
import litellm
from app.config import settings
from app.schemas import ChatMetadata
from app.services.cache_service import (
    generate_cache_key,
    get_cached_response,
    set_cached_response,
)

logger = logging.getLogger(__name__)


def parse_simulation_header(header_val: Optional[str]) -> Dict[str, int]:
    """
    Parses X-Simulate-Failure header.
    Examples:
    - 'key_1=429' -> {'key_1': 429}
    - 'key_1=429,key_2=500' -> {'key_1': 429, 'key_2': 500}
    - '*=429' -> {'*': 429}
    """
    if not header_val:
        return {}
    result = {}
    tokens = [t.strip() for t in header_val.split(",") if t.strip()]
    for token in tokens:
        if "=" in token:
            k, v = token.split("=", 1)
            try:
                result[k.strip()] = int(v.strip())
            except ValueError:
                pass
    return result


def execute_llm_request(
    messages: List[Dict[str, str]],
    simulate_failure_header: Optional[str] = None,
) -> Tuple[str, ChatMetadata]:
    """
    Executes an LLM request with:
    1. LiteLLM Response Caching
    2. Multi-key failover pool
    3. Failure simulation hook (X-Simulate-Failure)
    4. Per-request latency and token counting
    """
    model = settings.LLM_MODEL
    key_dict = settings.key_dict  # e.g. {"key_1": "sk-...", "key_2": "sk-..."}
    total_keys = len(key_dict)

    if total_keys == 0:
        logger.error("No LLM API keys configured in pool")
        raise HTTPException(status_code=503, detail="all providers unavailable")

    sim_dict = {}
    if settings.ENABLE_FAILURE_SIMULATION and simulate_failure_header:
        sim_dict = parse_simulation_header(simulate_failure_header)

    has_wildcard_fail = "*" in sim_dict
    cache_key = generate_cache_key(model, messages)

    # 1. Check LiteLLM cache if simulation is not forcing a failure
    # (Do not return cache if simulation header requests failure, nor allow simulated failures to be cached)
    if not sim_dict and settings.LITELLM_CACHE_ENABLED:
        start_cache_time = time.perf_counter()
        cached_entry = get_cached_response(cache_key)
        if cached_entry:
            latency_ms = max(1, int((time.perf_counter() - start_cache_time) * 1000))
            metadata = ChatMetadata(
                resolution_source="LLM_CACHE",
                model=model,
                latency_ms=latency_ms,
                input_tokens=cached_entry.get("input_tokens", 0),
                output_tokens=cached_entry.get("output_tokens", 0),
                key_id=None,
                fallback_attempts=0,
            )
            return cached_entry["reply"], metadata

    # 2. Iterate through key pool with failover
    fallback_attempts = 0
    start_time = time.perf_counter()

    for idx, (key_id, api_key) in enumerate(key_dict.items()):
        # Check simulation hook for this key
        simulated_status = sim_dict.get(key_id) or (sim_dict.get("*") if has_wildcard_fail else None)
        if simulated_status in (429, 500, 502, 503):
            logger.info(f"Simulating failure HTTP {simulated_status} for {key_id}")
            fallback_attempts += 1
            continue

        try:
            kwargs = {
                "model": model,
                "messages": messages,
                "api_key": api_key,
                "caching": False,  # Managed at service level to guarantee contract adherence
            }
            if settings.LLM_API_BASE:
                kwargs["api_base"] = settings.LLM_API_BASE

            response = litellm.completion(**kwargs)

            # Successfully received response
            reply_text = response.choices[0].message.content
            usage = getattr(response, "usage", None)
            input_tokens = getattr(usage, "prompt_tokens", 0) if usage else 0
            output_tokens = getattr(usage, "completion_tokens", 0) if usage else 0
            latency_ms = max(1, int((time.perf_counter() - start_time) * 1000))

            metadata = ChatMetadata(
                resolution_source="LIVE_INFERENCE",
                model=model,
                latency_ms=latency_ms,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                key_id=key_id,
                fallback_attempts=fallback_attempts,
            )

            # Cache the successful live response if no simulation was active
            if not sim_dict and settings.LITELLM_CACHE_ENABLED:
                set_cached_response(
                    cache_key,
                    {
                        "reply": reply_text,
                        "input_tokens": input_tokens,
                        "output_tokens": output_tokens,
                        "model": model,
                    },
                )

            return reply_text, metadata

        except Exception as e:
            logger.warning(
                f"Request failed with {key_id}: {type(e).__name__}. Retrying with next key if available."
            )
            fallback_attempts += 1
            continue

    # If all keys failed:
    logger.error("All configured LLM provider keys failed")
    raise HTTPException(status_code=503, detail="all providers unavailable")
