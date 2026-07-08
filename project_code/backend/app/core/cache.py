"""缓存抽象层。"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any, Protocol

from app.config import settings

try:
    import diskcache
except ImportError:  # pragma: no cover - diskcache is installed in production deps
    diskcache = None


class CacheBackend(Protocol):
    async def get(self, key: str, default: Any = None) -> Any: ...

    async def set(self, key: str, value: Any, ttl: int | None = None) -> bool: ...

    async def delete(self, key: str) -> bool: ...

    async def clear(self) -> None: ...


class InMemoryCache:
    """轻量内存缓存，占位用于开发环境。"""

    def __init__(self) -> None:
        self._store: dict[str, tuple[Any, float | None]] = {}

    async def get(self, key: str, default: Any = None) -> Any:
        item = self._store.get(key)
        if item is None:
            return default
        value, expires_at = item
        if expires_at is not None:
            from time import time

            if time() >= expires_at:
                self._store.pop(key, None)
                return default
        return value

    async def set(self, key: str, value: Any, ttl: int | None = None) -> bool:
        expires_at = None
        if ttl is not None:
            from time import time

            expires_at = time() + ttl
        self._store[key] = (value, expires_at)
        return True

    async def delete(self, key: str) -> bool:
        return self._store.pop(key, None) is not None

    async def clear(self) -> None:
        self._store.clear()


@dataclass(slots=True)
class DiskCacheAdapter:
    """diskcache 异步适配器，面向小体量业务数据。"""

    cache: Any

    async def get(self, key: str, default: Any = None) -> Any:
        return await asyncio.to_thread(self.cache.get, key, default=default)

    async def set(self, key: str, value: Any, ttl: int | None = None) -> bool:
        return await asyncio.to_thread(self.cache.set, key, value, expire=ttl)

    async def delete(self, key: str) -> bool:
        return await asyncio.to_thread(self.cache.delete, key)

    async def clear(self) -> None:
        await asyncio.to_thread(self.cache.clear)


_cache_backend: CacheBackend | None = None


def _create_diskcache_backend() -> DiskCacheAdapter:
    if diskcache is None:
        raise RuntimeError("diskcache is not installed")

    cache_dir = settings.resolved_cache_dir
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache = diskcache.Cache(
        str(cache_dir),
        size_limit=settings.cache_size_limit_bytes,
        disk_min_file_size=settings.cache_max_item_size_bytes,
    )
    return DiskCacheAdapter(cache=cache)


def get_cache_backend() -> CacheBackend:
    """获取缓存后端实例。"""
    global _cache_backend
    if _cache_backend is not None:
        return _cache_backend

    backend = settings.effective_cache_backend
    if backend == "diskcache":
        _cache_backend = _create_diskcache_backend()
    else:
        _cache_backend = InMemoryCache()
    return _cache_backend


async def cache_get(key: str, default: Any = None) -> Any:
    return await get_cache_backend().get(key, default=default)


async def cache_set(key: str, value: Any, ttl: int | None = None) -> bool:
    effective_ttl = settings.cache_default_ttl_seconds if ttl is None else ttl
    return await get_cache_backend().set(key, value, ttl=effective_ttl)


async def cache_delete(key: str) -> bool:
    return await get_cache_backend().delete(key)


async def cache_clear() -> None:
    return await get_cache_backend().clear()
