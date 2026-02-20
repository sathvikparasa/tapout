"""
Redis cache service.

Thin async wrapper around redis.asyncio. All cache misses (Redis down,
key missing, decode error) return None so callers can fall back to DB.
"""

import json
import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)

_redis = None  # redis.asyncio.Redis instance, set in init_cache()

# TTLs (seconds)
TTL_LOTS_LIST = 600       # 10 min  — lot list is nearly static
TTL_LOT_STATS = 60        # 1 min   — active parkers + recent sightings
TTL_VOTE_COUNTS = 30      # 30 sec  — invalidated on every vote
TTL_PREDICTION = 300      # 5 min   — prediction per lot


def init_cache(host: str, port: int = 6379) -> None:
    global _redis
    try:
        import redis.asyncio as redis
        _redis = redis.Redis(host=host, port=port, decode_responses=True)
        logger.info(f"Redis cache connected at {host}:{port}")
    except Exception as e:
        logger.error(f"Failed to init Redis cache: {e}")


async def close_cache() -> None:
    global _redis
    if _redis:
        await _redis.aclose()
        _redis = None


# ── primitives ──────────────────────────────────────────────────────────────

async def cache_get(key: str) -> Optional[Any]:
    if _redis is None:
        return None
    try:
        raw = await _redis.get(key)
        return json.loads(raw) if raw is not None else None
    except Exception as e:
        logger.warning(f"cache_get({key}): {e}")
        return None


async def cache_set(key: str, value: Any, ttl: int) -> None:
    if _redis is None:
        return
    try:
        await _redis.setex(key, ttl, json.dumps(value))
    except Exception as e:
        logger.warning(f"cache_set({key}): {e}")


async def cache_delete(*keys: str) -> None:
    if _redis is None or not keys:
        return
    try:
        await _redis.delete(*keys)
    except Exception as e:
        logger.warning(f"cache_delete({keys}): {e}")


async def cache_delete_pattern(pattern: str) -> None:
    if _redis is None:
        return
    try:
        keys = await _redis.keys(pattern)
        if keys:
            await _redis.delete(*keys)
    except Exception as e:
        logger.warning(f"cache_delete_pattern({pattern}): {e}")
