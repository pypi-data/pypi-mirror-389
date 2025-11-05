"""Cache configuration and defaults for ECReshore.

Provides configuration management for cache settings including TTLs,
backend selection, and cache category definitions. Supports environment
variable overrides for all settings.

Environment Variables:
    ECRESHORE_CACHE_BACKEND: Backend type (memory|disk|hybrid|none)
    ECRESHORE_CACHE_DIR: Directory for disk cache storage
    ECRESHORE_CACHE_TTL_REPOS: TTL for repository listings (seconds)
    ECRESHORE_CACHE_TTL_IMAGES: TTL for image listings (seconds)
    ECRESHORE_CACHE_TTL_DIGESTS: TTL for image digests (seconds)
    ECRESHORE_CACHE_MAX_SIZE: Maximum cache entries before eviction
    ECRESHORE_CACHE_DEBUG: Enable verbose cache logging
"""

import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class CacheCategoryConfig:
    """Configuration for a specific cache category."""

    name: str
    ttl: int  # Time-to-live in seconds
    max_size: int  # Maximum entries before LRU eviction
    backend: str  # Backend type: memory, disk, hybrid


class CacheConfig:
    """Global cache configuration with environment variable support."""

    # Default cache categories and their settings
    CATEGORIES = {
        "ecr_repositories": CacheCategoryConfig(
            name="ecr_repositories",
            ttl=600,  # 10 minutes
            max_size=100,
            backend="hybrid",
        ),
        "ecr_images": CacheCategoryConfig(
            name="ecr_images",
            ttl=300,  # 5 minutes
            max_size=1000,
            backend="hybrid",
        ),
        "image_digests": CacheCategoryConfig(
            name="image_digests",
            ttl=3600,  # 1 hour - digests are immutable
            max_size=5000,
            backend="hybrid",
        ),
        "image_presence": CacheCategoryConfig(
            name="image_presence",
            ttl=300,  # 5 minutes
            max_size=1000,
            backend="memory",
        ),
        "k8s_workloads": CacheCategoryConfig(
            name="k8s_workloads",
            ttl=120,  # 2 minutes - workloads change frequently
            max_size=500,
            backend="memory",
        ),
        "auth_tokens": CacheCategoryConfig(
            name="auth_tokens",
            ttl=3300,  # 55 minutes - ECR tokens valid for 12 hours
            max_size=10,
            backend="memory",
        ),
        "skip_decisions": CacheCategoryConfig(
            name="skip_decisions",
            ttl=120,  # 2 minutes - conservative TTL for skip decisions
            max_size=1000,  # Same as image_presence
            backend="memory",  # Fast memory-only cache for quick decisions
        ),
    }

    @classmethod
    def get_backend_type(cls) -> str:
        """Get cache backend type from environment or default.

        Returns:
            Backend type: memory, disk, hybrid, or none
        """
        backend = os.getenv("ECRESHORE_CACHE_BACKEND", "memory").lower()
        if backend not in ("memory", "disk", "hybrid", "none"):
            backend = "memory"
        return backend

    @classmethod
    def get_cache_dir(cls) -> str:
        """Get cache directory from environment or default.

        Returns:
            Path to cache directory
        """
        cache_dir = os.getenv("ECRESHORE_CACHE_DIR", "~/.ecreshore/cache")
        return os.path.expanduser(cache_dir)

    @classmethod
    def get_ttl_repos(cls) -> int:
        """Get TTL for repository listings."""
        return int(os.getenv("ECRESHORE_CACHE_TTL_REPOS", "600"))

    @classmethod
    def get_ttl_images(cls) -> int:
        """Get TTL for image listings."""
        return int(os.getenv("ECRESHORE_CACHE_TTL_IMAGES", "300"))

    @classmethod
    def get_ttl_digests(cls) -> int:
        """Get TTL for image digests."""
        return int(os.getenv("ECRESHORE_CACHE_TTL_DIGESTS", "3600"))

    @classmethod
    def get_max_size(cls) -> int:
        """Get maximum cache size."""
        return int(os.getenv("ECRESHORE_CACHE_MAX_SIZE", "1000"))

    @classmethod
    def is_debug_enabled(cls) -> bool:
        """Check if cache debug logging is enabled."""
        return os.getenv("ECRESHORE_CACHE_DEBUG", "false").lower() in (
            "true",
            "1",
            "yes",
        )

    @classmethod
    def is_cache_enabled(cls) -> bool:
        """Check if caching is enabled globally."""
        return cls.get_backend_type() != "none"

    @classmethod
    def get_category_config(cls, category: str) -> Optional[CacheCategoryConfig]:
        """Get configuration for a specific cache category.

        Args:
            category: Cache category name

        Returns:
            CacheCategoryConfig or None if category not found
        """
        return cls.CATEGORIES.get(category)


# Global flag to disable caching (set by CLI flags like --no-cache)
_cache_disabled = False


def disable_cache() -> None:
    """Disable caching globally (e.g., via --no-cache flag)."""
    global _cache_disabled
    _cache_disabled = True


def enable_cache() -> None:
    """Re-enable caching globally."""
    global _cache_disabled
    _cache_disabled = False


def is_cache_disabled() -> bool:
    """Check if caching is disabled globally."""
    return _cache_disabled
