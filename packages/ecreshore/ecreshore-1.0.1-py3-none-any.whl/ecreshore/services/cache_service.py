"""Unified caching service with TTL, LRU eviction, and async support.

This module provides a flexible caching infrastructure for ECReshore operations,
supporting multiple backends (memory, disk, hybrid) with configurable TTLs and
automatic LRU eviction under memory pressure.

Design Principles:
- Graceful degradation: Cache failures never fail operations
- Conservative TTLs: Prefer correctness over performance
- Observable: Provide metrics and debugging capabilities
- Testable: Pure functions, mockable backends
"""

import asyncio
import hashlib
import logging
import time
from dataclasses import dataclass, field
from functools import wraps
from typing import Any, Callable, Dict, Optional, TypeVar, cast

logger = logging.getLogger(__name__)

# Global cache version - increment on schema changes to invalidate all caches
CACHE_VERSION = 1

T = TypeVar("T")


@dataclass
class CacheStats:
    """Cache performance statistics."""

    hits: int = 0
    misses: int = 0
    sets: int = 0
    deletes: int = 0
    evictions: int = 0
    errors: int = 0
    total_keys: int = 0

    @property
    def hit_rate(self) -> float:
        """Calculate cache hit rate as percentage."""
        total = self.hits + self.misses
        return (self.hits / total * 100) if total > 0 else 0.0

    @property
    def miss_rate(self) -> float:
        """Calculate cache miss rate as percentage."""
        return 100.0 - self.hit_rate

    def to_dict(self) -> Dict[str, Any]:
        """Convert stats to dictionary for JSON serialization."""
        return {
            "hits": self.hits,
            "misses": self.misses,
            "sets": self.sets,
            "deletes": self.deletes,
            "evictions": self.evictions,
            "errors": self.errors,
            "total_keys": self.total_keys,
            "hit_rate": round(self.hit_rate, 2),
            "miss_rate": round(self.miss_rate, 2),
        }


@dataclass
class CacheEntry:
    """Internal cache entry with metadata."""

    value: Any
    expires_at: Optional[float] = None
    created_at: float = field(default_factory=time.time)
    last_accessed: float = field(default_factory=time.time)

    def is_expired(self) -> bool:
        """Check if entry has expired."""
        if self.expires_at is None:
            return False
        return time.time() >= self.expires_at


class CacheBackend:
    """Abstract base class for cache storage backends."""

    async def get(self, key: str) -> Optional[CacheEntry]:
        """Retrieve entry from cache."""
        raise NotImplementedError

    async def set(self, key: str, entry: CacheEntry) -> None:
        """Store entry in cache."""
        raise NotImplementedError

    async def delete(self, key: str) -> bool:
        """Remove entry from cache. Returns True if key existed."""
        raise NotImplementedError

    async def clear(self) -> int:
        """Clear all entries. Returns number of keys cleared."""
        raise NotImplementedError

    async def keys(self) -> list[str]:
        """Get all cache keys."""
        raise NotImplementedError

    async def size(self) -> int:
        """Get number of entries in cache."""
        raise NotImplementedError


class CacheService:
    """Unified cache service with TTL, LRU, and async support.

    Provides a high-level caching API with automatic expiration, LRU eviction,
    and pluggable storage backends. Thread-safe for async operations.

    Example:
        >>> cache = CacheService(backend=MemoryBackend(), default_ttl=300)
        >>> await cache.set("key", "value", ttl=60)
        >>> value = await cache.get("key")
        >>> stats = await cache.get_stats()
        >>> print(f"Hit rate: {stats.hit_rate}%")
    """

    def __init__(
        self,
        backend: CacheBackend,
        default_ttl: Optional[int] = None,
        max_size: Optional[int] = 1000,
        enable_stats: bool = True,
    ):
        """Initialize cache service.

        Args:
            backend: Storage backend (Memory, Disk, or Hybrid)
            default_ttl: Default time-to-live in seconds (None = no expiration)
            max_size: Maximum entries before LRU eviction (None = unlimited)
            enable_stats: Whether to collect performance statistics
        """
        self.backend = backend
        self.default_ttl = default_ttl
        self.max_size = max_size
        self.enable_stats = enable_stats
        self._stats = CacheStats() if enable_stats else None
        self._lock = asyncio.Lock()

    async def get(self, key: str) -> Optional[Any]:
        """Retrieve value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found/expired
        """
        try:
            async with self._lock:
                entry = await self.backend.get(key)

                if entry is None:
                    if self._stats:
                        self._stats.misses += 1
                    logger.debug(f"Cache miss: {key}")
                    return None

                # Check expiration
                if entry.is_expired():
                    await self.backend.delete(key)
                    if self._stats:
                        self._stats.misses += 1
                        self._stats.deletes += 1
                    logger.debug(f"Cache expired: {key}")
                    return None

                # Update access time for LRU
                entry.last_accessed = time.time()
                await self.backend.set(key, entry)

                if self._stats:
                    self._stats.hits += 1
                logger.debug(f"Cache hit: {key}")
                return entry.value

        except Exception as e:
            if self._stats:
                self._stats.errors += 1
            logger.warning(f"Cache get error for {key}: {e}", exc_info=True)
            return None

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Store value in cache.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live in seconds (overrides default_ttl, None = no expiration)
        """
        try:
            async with self._lock:
                # Calculate expiration
                effective_ttl = ttl if ttl is not None else self.default_ttl
                expires_at = (
                    time.time() + effective_ttl if effective_ttl is not None else None
                )

                entry = CacheEntry(value=value, expires_at=expires_at)
                await self.backend.set(key, entry)

                if self._stats:
                    self._stats.sets += 1
                    self._stats.total_keys = await self.backend.size()

                # Check if we need to evict entries (LRU)
                if self.max_size and await self.backend.size() > self.max_size:
                    await self._evict_lru()

                logger.debug(f"Cache set: {key} (ttl={effective_ttl}s)")

        except Exception as e:
            if self._stats:
                self._stats.errors += 1
            logger.warning(f"Cache set error for {key}: {e}", exc_info=True)

    async def delete(self, key: str) -> bool:
        """Remove key from cache.

        Args:
            key: Cache key to remove

        Returns:
            True if key was present and removed, False otherwise
        """
        try:
            async with self._lock:
                existed = await self.backend.delete(key)
                if existed and self._stats:
                    self._stats.deletes += 1
                    self._stats.total_keys = await self.backend.size()
                logger.debug(f"Cache delete: {key} (existed={existed})")
                return existed
        except Exception as e:
            if self._stats:
                self._stats.errors += 1
            logger.warning(f"Cache delete error for {key}: {e}", exc_info=True)
            return False

    async def clear(self, pattern: Optional[str] = None) -> int:
        """Clear cache entries.

        Args:
            pattern: Optional key prefix to clear (None = clear all)

        Returns:
            Number of entries cleared
        """
        try:
            async with self._lock:
                if pattern is None:
                    count = await self.backend.clear()
                else:
                    # Clear keys matching pattern
                    keys = await self.backend.keys()
                    matching_keys = [k for k in keys if k.startswith(pattern)]
                    count = 0
                    for key in matching_keys:
                        if await self.backend.delete(key):
                            count += 1

                if self._stats:
                    self._stats.total_keys = await self.backend.size()

                logger.info(f"Cache cleared: {count} entries (pattern={pattern})")
                return count

        except Exception as e:
            if self._stats:
                self._stats.errors += 1
            logger.warning(f"Cache clear error (pattern={pattern}): {e}", exc_info=True)
            return 0

    async def get_stats(self) -> CacheStats:
        """Get cache performance statistics.

        Returns:
            CacheStats with current metrics
        """
        if self._stats is None:
            return CacheStats()

        async with self._lock:
            self._stats.total_keys = await self.backend.size()
            return self._stats

    async def _evict_lru(self) -> None:
        """Evict least recently used entries to enforce max_size."""
        try:
            keys = await self.backend.keys()
            entries_with_access: list[tuple[str, float]] = []

            for key in keys:
                entry = await self.backend.get(key)
                if entry:
                    entries_with_access.append((key, entry.last_accessed))

            # Sort by last accessed (oldest first)
            entries_with_access.sort(key=lambda x: x[1])

            # Evict oldest 10% or at least 1 entry
            num_to_evict = max(1, len(entries_with_access) // 10)
            for key, _ in entries_with_access[:num_to_evict]:
                await self.backend.delete(key)
                if self._stats:
                    self._stats.evictions += 1

            logger.debug(f"LRU eviction: removed {num_to_evict} entries")

        except Exception as e:
            logger.warning(f"LRU eviction error: {e}", exc_info=True)

    async def warmup(self, keys: list[str], loader: Callable[[str], Any]) -> int:
        """Pre-populate cache with data.

        Args:
            keys: List of keys to warm up
            loader: Async function to load value for each key

        Returns:
            Number of keys successfully warmed
        """
        count = 0
        for key in keys:
            try:
                value = await loader(key) if asyncio.iscoroutinefunction(loader) else loader(key)
                await self.set(key, value)
                count += 1
            except Exception as e:
                logger.warning(f"Cache warmup error for {key}: {e}")
        logger.info(f"Cache warmup: loaded {count}/{len(keys)} keys")
        return count


def make_cache_key(*parts: Any, version: int = CACHE_VERSION) -> str:
    """Generate consistent cache key from components.

    Args:
        *parts: Key components (will be converted to strings)
        version: Cache schema version (default: CACHE_VERSION)

    Returns:
        Hierarchical cache key with version prefix

    Example:
        >>> make_cache_key("ecr", "us-east-1", "123456", "repos")
        'v1:ecr:us-east-1:123456:repos'
    """
    # Convert all parts to strings and filter out None
    str_parts = [str(p) for p in parts if p is not None]
    key = f"v{version}:" + ":".join(str_parts)
    return key


def hash_params(**params: Any) -> str:
    """Generate deterministic hash from parameters.

    Args:
        **params: Parameters to hash

    Returns:
        SHA256 hash (first 16 chars) of sorted parameters

    Example:
        >>> hash_params(tag="latest", filter="nginx")
        'a1b2c3d4e5f6g7h8'
    """
    # Sort params for consistency
    sorted_params = sorted(params.items())
    param_str = str(sorted_params)
    return hashlib.sha256(param_str.encode()).hexdigest()[:16]


def cached(
    cache_name: str,
    ttl: Optional[int] = None,
    key_fn: Optional[Callable[..., str]] = None,
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Decorator for transparent method caching.

    Args:
        cache_name: Cache category name
        ttl: Time-to-live in seconds (None = use cache default)
        key_fn: Function to generate cache key from method args
                Default: uses cache_name + first arg (typically 'self')

    Example:
        @cached(cache_name='ecr_repos', ttl=600,
                key_fn=lambda self: f"{self.region}:{self.registry_id}")
        async def list_repositories(self, name_filter=None):
            # expensive operation
            return repos

    Note:
        Uses get_cache() from cache_manager for cache instance retrieval.
        This decorator is applied to async methods.
        Cache failures gracefully degrade to executing the original function.
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Import here to avoid circular dependency
            from .cache_manager import get_cache

            # Generate cache key
            if key_fn:
                # Use custom key function
                key_suffix = key_fn(*args, **kwargs)
            else:
                # Default: use function name and params hash
                params_hash = hash_params(**kwargs)
                key_suffix = f"{func.__name__}:{params_hash}"

            cache_key = make_cache_key(cache_name, key_suffix)

            # Try to get cache instance
            cache = get_cache(cache_name)
            if cache:
                try:
                    cached_value = await cache.get(cache_key)
                    if cached_value is not None:
                        logger.debug(f"Cache hit for {cache_key}")
                        return cached_value
                except Exception as e:
                    # Cache errors should not break functionality - graceful degradation
                    logger.debug(f"Cache get error for {cache_key}: {e}")

            # Cache miss or cache unavailable - call original function
            result = await func(*args, **kwargs)

            # Store in cache (if available)
            if cache:
                try:
                    await cache.set(cache_key, result, ttl=ttl)
                    logger.debug(f"Cache miss for {cache_key}, stored result (ttl={ttl})")
                except Exception as e:
                    # Cache errors should not break functionality - graceful degradation
                    logger.debug(f"Cache set error for {cache_key}: {e}")

            return result

        return cast(Callable[..., T], wrapper)

    return decorator
