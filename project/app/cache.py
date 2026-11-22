"""아주 짧은 메모리 캐시. CACHE_TTL_MS가 0이면 항상 비활성화된다."""

import time
from typing import Any

from app.config import get_settings

_store: dict[str, tuple[float, Any]] = {}


def cache_get(key: str) -> Any | None:
    ttl_ms = get_settings().cache_ttl_ms
    if ttl_ms <= 0:
        return None
    found = _store.get(key)
    if found is None:
        return None
    saved_at, value = found
    if (time.monotonic() - saved_at) * 1000 > ttl_ms:
        _store.pop(key, None)
        return None
    return value


def cache_set(key: str, value: Any) -> None:
    if get_settings().cache_ttl_ms <= 0:
        return
    _store[key] = (time.monotonic(), value)


def cache_clear() -> None:
    _store.clear()
