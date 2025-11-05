"""Global cache manager for ECReshore services.

Provides centralized cache instances for different categories (ECR repos, images,
digests, etc.) with lazy initialization and configuration management.

Usage:
    from ecreshore.services.cache_manager import get_cache

    cache = get_cache("ecr_repositories")
    await cache.set("key", "value")
    value = await cache.get("key")
"""

import logging
from typing import Dict, Optional

from ..cache_config import CacheConfig
from .cache_backends import DiskBackend, HybridBackend, MemoryBackend
from .cache_service import CacheService

logger = logging.getLogger(__name__)

# Global cache instances (lazy-initialized)
_cache_instances: Dict[str, CacheService] = {}
_initialized = False


def _create_backend(backend_type: str):
    """Create cache backend based on type.

    Args:
        backend_type: Backend type (memory, disk, hybrid, none)

    Returns:
        CacheBackend instance
    """
    if backend_type == "memory":
        return MemoryBackend()
    elif backend_type == "disk":
        cache_dir = CacheConfig.get_cache_dir()
        return DiskBackend(cache_dir=cache_dir)
    elif backend_type == "hybrid":
        cache_dir = CacheConfig.get_cache_dir()
        return HybridBackend(
            memory_backend=MemoryBackend(),
            disk_backend=DiskBackend(cache_dir=cache_dir)
        )
    else:
        # For "none" or invalid types, return MemoryBackend as fallback
        return MemoryBackend()


def initialize_caches() -> None:
    """Initialize all cache instances based on configuration.

    Creates cache services for each defined category in CacheConfig.
    This is called automatically by get_cache() but can be called
    explicitly for eager initialization.
    """
    global _cache_instances, _initialized

    if _initialized:
        return

    if not CacheConfig.is_cache_enabled():
        logger.info("Caching is disabled")
        _initialized = True
        return

    logger.info("Initializing cache services")

    for category_name, config in CacheConfig.CATEGORIES.items():
        try:
            backend = _create_backend(config.backend)
            cache_service = CacheService(
                backend=backend,
                default_ttl=config.ttl,
                max_size=config.max_size,
                enable_stats=True,
            )
            _cache_instances[category_name] = cache_service
            logger.debug(
                f"Initialized {category_name} cache: "
                f"backend={config.backend}, ttl={config.ttl}s, max_size={config.max_size}"
            )
        except Exception as e:
            logger.warning(f"Failed to initialize cache for {category_name}: {e}")
            # Create a minimal memory cache as fallback
            _cache_instances[category_name] = CacheService(
                backend=MemoryBackend(),
                default_ttl=config.ttl,
                max_size=100,
                enable_stats=False,
            )

    _initialized = True
    logger.info(f"Cache initialization complete ({len(_cache_instances)} categories)")


def get_cache(category: str) -> Optional[CacheService]:
    """Get cache instance for a specific category.

    Args:
        category: Cache category name (e.g., 'ecr_repositories', 'image_digests')

    Returns:
        CacheService instance or None if caching is disabled or category not found
    """
    if not _initialized:
        initialize_caches()

    if not CacheConfig.is_cache_enabled():
        return None

    return _cache_instances.get(category)


def clear_all_caches() -> Dict[str, int]:
    """Clear all cache instances.

    Returns:
        Dictionary mapping category names to number of entries cleared
    """
    import asyncio

    results = {}
    for category, cache in _cache_instances.items():
        try:
            # Run async clear in sync context
            count = asyncio.run(cache.clear())
            results[category] = count
        except Exception as e:
            logger.warning(f"Failed to clear cache for {category}: {e}")
            results[category] = 0

    return results


def get_all_cache_stats() -> Dict[str, Dict]:
    """Get statistics from all cache instances.

    Returns:
        Dictionary mapping category names to their stats
    """
    import asyncio

    stats = {}
    for category, cache in _cache_instances.items():
        try:
            cache_stats = asyncio.run(cache.get_stats())
            stats[category] = cache_stats.to_dict()
        except Exception as e:
            logger.warning(f"Failed to get stats for {category}: {e}")
            stats[category] = {"error": str(e)}

    return stats


def reset_caches() -> None:
    """Reset all caches (for testing purposes)."""
    global _cache_instances, _initialized
    _cache_instances.clear()
    _initialized = False
