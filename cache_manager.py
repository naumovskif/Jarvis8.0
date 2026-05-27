"""
Advanced caching layer for JARVIS with LRU eviction and TTL support.
Handles embeddings, API responses, and conversation caching.
"""

import json
import time
import hashlib
from pathlib import Path
from threading import Lock
from typing import Any, Optional, Callable
from collections import OrderedDict
import sys


def get_base_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent


BASE_DIR = get_base_dir()
CACHE_DIR = BASE_DIR / "cache"


class CacheEntry:
    def __init__(self, value: Any, ttl: Optional[float] = None):
        self.value = value
        self.created_at = time.time()
        self.ttl = ttl  # None = no expiration
        self.access_count = 0
        self.last_access = time.time()

    def is_expired(self) -> bool:
        if self.ttl is None:
            return False
        return time.time() - self.created_at > self.ttl

    def touch(self) -> None:
        self.last_access = time.time()
        self.access_count += 1


class LRUCache:
    """Thread-safe LRU cache with TTL support."""

    def __init__(self, max_size: int = 1000, default_ttl: Optional[float] = None):
        self.max_size = max_size
        self.default_ttl = default_ttl
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._lock = Lock()
        self._hits = 0
        self._misses = 0

    def _hash_key(self, key: str) -> str:
        """Generate consistent hash key."""
        if len(key) < 256:
            return key
        return hashlib.md5(key.encode()).hexdigest()

    def get(self, key: str, default: Any = None) -> Any:
        """Retrieve value from cache."""
        key = self._hash_key(key)
        with self._lock:
            if key not in self._cache:
                self._misses += 1
                return default

            entry = self._cache[key]
            if entry.is_expired():
                del self._cache[key]
                self._misses += 1
                return default

            entry.touch()
            self._cache.move_to_end(key)
            self._hits += 1
            return entry.value

    def set(self, key: str, value: Any, ttl: Optional[float] = None) -> None:
        """Store value in cache with optional TTL."""
        key = self._hash_key(key)
        ttl = ttl or self.default_ttl

        with self._lock:
            if key in self._cache:
                del self._cache[key]

            self._cache[key] = CacheEntry(value, ttl)
            self._cache.move_to_end(key)

            # Evict oldest if exceeds max size
            while len(self._cache) > self.max_size:
                self._cache.popitem(last=False)

    def delete(self, key: str) -> None:
        """Remove key from cache."""
        key = self._hash_key(key)
        with self._lock:
            self._cache.pop(key, None)

    def clear(self) -> None:
        """Clear all cache entries."""
        with self._lock:
            self._cache.clear()
            self._hits = 0
            self._misses = 0

    def stats(self) -> dict:
        """Get cache statistics."""
        with self._lock:
            total = self._hits + self._misses
            hit_rate = (self._hits / total * 100) if total > 0 else 0.0
            return {
                "size": len(self._cache),
                "max_size": self.max_size,
                "hits": self._hits,
                "misses": self._misses,
                "hit_rate": hit_rate,
            }


class PersistentCache:
    """Disk-based cache for embeddings and large responses."""

    def __init__(self, cache_dir: Optional[Path] = None):
        self.cache_dir = cache_dir or CACHE_DIR
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._lock = Lock()

    def _get_path(self, key: str) -> Path:
        """Get file path for cache key."""
        hash_key = hashlib.md5(key.encode()).hexdigest()
        return self.cache_dir / f"{hash_key}.json"

    def get(self, key: str, ttl: float = 86400) -> Optional[Any]:
        """Load from disk cache."""
        path = self._get_path(key)
        if not path.exists():
            return None

        with self._lock:
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                created = data.get("_created", 0)

                # Check expiration
                if time.time() - created > ttl:
                    path.unlink()
                    return None

                return data.get("value")
            except Exception:
                return None

    def set(self, key: str, value: Any) -> None:
        """Save to disk cache."""
        path = self._get_path(key)
        with self._lock:
            try:
                data = {
                    "_created": time.time(),
                    "value": value,
                }
                path.write_text(
                    json.dumps(data, ensure_ascii=False),
                    encoding="utf-8"
                )
            except Exception as e:
                print(f"[PersistentCache] ⚠️ Write failed: {e}")

    def delete(self, key: str) -> None:
        """Remove from disk cache."""
        path = self._get_path(key)
        with self._lock:
            path.unlink(missing_ok=True)

    def clear(self) -> None:
        """Clear all disk cache."""
        with self._lock:
            for f in self.cache_dir.glob("*.json"):
                f.unlink(missing_ok=True)

    def size_mb(self) -> float:
        """Get total cache size in MB."""
        with self._lock:
            total = sum(f.stat().st_size for f in self.cache_dir.glob("*.json"))
            return total / (1024 * 1024)


class CacheManager:
    """
    Unified cache manager for embeddings, API responses, and conversation data.
    Combines in-memory (fast, small) with disk storage (persistent, large).
    """

    def __init__(
        self,
        memory_max_size: int = 1000,
        memory_ttl: Optional[float] = None,
        disk_ttl: float = 86400,  # 24 hours
    ):
        self.memory_cache = LRUCache(max_size=memory_max_size, default_ttl=memory_ttl)
        self.disk_cache = PersistentCache()
        self.disk_ttl = disk_ttl
        self._request_dedup: dict[str, (time.time(), Any)] = {}
        self._dedup_lock = Lock()

    def cache_embedding(self, text: str, embedding: list[float]) -> None:
        """Cache embedding with key = hash(text)."""
        key = f"emb:{hashlib.md5(text.encode()).hexdigest()}"
        self.memory_cache.set(key, embedding, ttl=3600)  # 1 hour
        # Also persist to disk
        self.disk_cache.set(key, embedding)

    def get_embedding(self, text: str) -> Optional[list[float]]:
        """Retrieve cached embedding."""
        key = f"emb:{hashlib.md5(text.encode()).hexdigest()}"
        # Check memory first (fast)
        result = self.memory_cache.get(key)
        if result is not None:
            return result
        # Fall back to disk
        return self.disk_cache.get(key, ttl=self.disk_ttl)

    def cache_api_response(
        self,
        method: str,
        url: str,
        params: dict,
        response: str,
        ttl: float = 3600,  # 1 hour
    ) -> None:
        """Cache API response."""
        key = self._api_cache_key(method, url, params)
        self.memory_cache.set(key, response, ttl=ttl)
        self.disk_cache.set(key, response)

    def get_api_response(
        self,
        method: str,
        url: str,
        params: dict,
    ) -> Optional[str]:
        """Retrieve cached API response."""
        key = self._api_cache_key(method, url, params)
        result = self.memory_cache.get(key)
        if result is not None:
            return result
        return self.disk_cache.get(key, ttl=self.disk_ttl)

    @staticmethod
    def _api_cache_key(method: str, url: str, params: dict) -> str:
        """Generate cache key for API call."""
        key_str = f"{method}:{url}:{json.dumps(params, sort_keys=True)}"
        return f"api:{hashlib.md5(key_str.encode()).hexdigest()}"

    def deduplicate_request(
        self,
        key: str,
        executor: Callable,
        ttl: float = 60,
    ) -> Any:
        """
        Deduplicate concurrent identical requests.
        If same request arrives within ttl, return cached result instead of re-executing.
        """
        with self._dedup_lock:
            if key in self._request_dedup:
                created, result = self._request_dedup[key]
                if time.time() - created < ttl:
                    return result

            result = executor()
            self._request_dedup[key] = (time.time(), result)
            return result

    def cleanup_dedup(self, ttl: float = 300) -> None:
        """Remove stale deduplication entries."""
        with self._dedup_lock:
            now = time.time()
            self._request_dedup = {
                k: v for k, v in self._request_dedup.items()
                if now - v[0] < ttl
            }

    def get_stats(self) -> dict:
        """Get comprehensive cache statistics."""
        mem_stats = self.memory_cache.stats()
        return {
            "memory": mem_stats,
            "disk": {
                "size_mb": self.disk_cache.size_mb(),
            },
            "dedup_pending": len(self._request_dedup),
        }

    def clear_all(self) -> None:
        """Clear all caches."""
        self.memory_cache.clear()
        self.disk_cache.clear()
        with self._dedup_lock:
            self._request_dedup.clear()


# Global instance
_manager: Optional[CacheManager] = None
_manager_lock = Lock()


def get_cache_manager() -> CacheManager:
    """Get or create global cache manager."""
    global _manager
    if _manager is None:
        with _manager_lock:
            if _manager is None:
                _manager = CacheManager()
    return _manager
