"""Tests for cache service and backends."""

import asyncio
import time
from pathlib import Path
from unittest.mock import Mock, patch
import pytest
import tempfile
import shutil

from src.ecreshore.services.cache_service import (
    CacheService,
    CacheStats,
    CacheEntry,
    make_cache_key,
    hash_params,
    cached,
    CACHE_VERSION,
)
from src.ecreshore.services.cache_backends import (
    MemoryBackend,
    DiskBackend,
    HybridBackend,
)


class TestCacheStats:
    """Test cache statistics."""

    def test_init_default_values(self):
        """Test CacheStats initialization with defaults."""
        stats = CacheStats()
        assert stats.hits == 0
        assert stats.misses == 0
        assert stats.sets == 0
        assert stats.deletes == 0
        assert stats.evictions == 0
        assert stats.errors == 0

    def test_hit_rate_calculation(self):
        """Test hit rate calculation."""
        stats = CacheStats(hits=75, misses=25)
        assert stats.hit_rate == 75.0
        assert stats.miss_rate == 25.0

    def test_hit_rate_no_requests(self):
        """Test hit rate with no requests."""
        stats = CacheStats()
        assert stats.hit_rate == 0.0
        assert stats.miss_rate == 100.0

    def test_to_dict(self):
        """Test dictionary serialization."""
        stats = CacheStats(hits=80, misses=20, sets=100, total_keys=50)
        result = stats.to_dict()
        assert result["hits"] == 80
        assert result["misses"] == 20
        assert result["hit_rate"] == 80.0
        assert result["miss_rate"] == 20.0
        assert result["total_keys"] == 50


class TestCacheEntry:
    """Test cache entry."""

    def test_init_default_values(self):
        """Test CacheEntry initialization with defaults."""
        entry = CacheEntry(value="test")
        assert entry.value == "test"
        assert entry.expires_at is None
        assert entry.created_at > 0
        assert entry.last_accessed > 0

    def test_is_expired_no_expiry(self):
        """Test expiration check with no expiry set."""
        entry = CacheEntry(value="test", expires_at=None)
        assert entry.is_expired() is False

    def test_is_expired_future(self):
        """Test expiration check with future expiry."""
        future_time = time.time() + 3600
        entry = CacheEntry(value="test", expires_at=future_time)
        assert entry.is_expired() is False

    def test_is_expired_past(self):
        """Test expiration check with past expiry."""
        past_time = time.time() - 1
        entry = CacheEntry(value="test", expires_at=past_time)
        assert entry.is_expired() is True


class TestMemoryBackend:
    """Test memory backend."""

    @pytest.mark.asyncio
    async def test_get_set_basic(self):
        """Test basic get and set operations."""
        backend = MemoryBackend()
        entry = CacheEntry(value="test-value")

        await backend.set("key1", entry)
        result = await backend.get("key1")

        assert result is not None
        assert result.value == "test-value"

    @pytest.mark.asyncio
    async def test_get_nonexistent(self):
        """Test get for nonexistent key."""
        backend = MemoryBackend()
        result = await backend.get("nonexistent")
        assert result is None

    @pytest.mark.asyncio
    async def test_delete_existing(self):
        """Test delete for existing key."""
        backend = MemoryBackend()
        entry = CacheEntry(value="test")

        await backend.set("key1", entry)
        deleted = await backend.delete("key1")

        assert deleted is True
        assert await backend.get("key1") is None

    @pytest.mark.asyncio
    async def test_delete_nonexistent(self):
        """Test delete for nonexistent key."""
        backend = MemoryBackend()
        deleted = await backend.delete("nonexistent")
        assert deleted is False

    @pytest.mark.asyncio
    async def test_clear(self):
        """Test clear operation."""
        backend = MemoryBackend()

        await backend.set("key1", CacheEntry(value="v1"))
        await backend.set("key2", CacheEntry(value="v2"))
        await backend.set("key3", CacheEntry(value="v3"))

        count = await backend.clear()

        assert count == 3
        assert await backend.size() == 0

    @pytest.mark.asyncio
    async def test_keys(self):
        """Test keys operation."""
        backend = MemoryBackend()

        await backend.set("key1", CacheEntry(value="v1"))
        await backend.set("key2", CacheEntry(value="v2"))

        keys = await backend.keys()

        assert len(keys) == 2
        assert "key1" in keys
        assert "key2" in keys

    @pytest.mark.asyncio
    async def test_size(self):
        """Test size operation."""
        backend = MemoryBackend()

        assert await backend.size() == 0

        await backend.set("key1", CacheEntry(value="v1"))
        assert await backend.size() == 1

        await backend.set("key2", CacheEntry(value="v2"))
        assert await backend.size() == 2

    @pytest.mark.asyncio
    async def test_lru_tracking(self):
        """Test LRU tracking with move_to_end."""
        backend = MemoryBackend()

        await backend.set("key1", CacheEntry(value="v1"))
        await backend.set("key2", CacheEntry(value="v2"))
        await backend.set("key3", CacheEntry(value="v3"))

        # Access key1 to move it to end (most recently used)
        await backend.get("key1")

        keys = await backend.keys()
        # key1 should be at the end now
        assert keys[-1] == "key1"


class TestDiskBackend:
    """Test disk backend."""

    @pytest.fixture
    def temp_cache_dir(self):
        """Create temporary cache directory."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir, ignore_errors=True)

    @pytest.mark.asyncio
    async def test_init_creates_directory(self, temp_cache_dir):
        """Test that backend creates cache directory."""
        cache_path = Path(temp_cache_dir) / "test_cache"
        backend = DiskBackend(cache_dir=str(cache_path))

        # Trigger connection
        await backend.size()

        assert cache_path.exists()
        assert (cache_path / "cache.db").exists()

    @pytest.mark.asyncio
    async def test_get_set_basic(self, temp_cache_dir):
        """Test basic get and set operations."""
        backend = DiskBackend(cache_dir=temp_cache_dir)
        entry = CacheEntry(value="test-value")

        await backend.set("key1", entry)
        result = await backend.get("key1")

        assert result is not None
        assert result.value == "test-value"

    @pytest.mark.asyncio
    async def test_persistence_across_instances(self, temp_cache_dir):
        """Test that data persists across backend instances."""
        # Write with first instance
        backend1 = DiskBackend(cache_dir=temp_cache_dir)
        entry = CacheEntry(value="persistent-value")
        await backend1.set("persist-key", entry)
        backend1.close()

        # Read with second instance
        backend2 = DiskBackend(cache_dir=temp_cache_dir)
        result = await backend2.get("persist-key")

        assert result is not None
        assert result.value == "persistent-value"
        backend2.close()

    @pytest.mark.asyncio
    async def test_delete_existing(self, temp_cache_dir):
        """Test delete for existing key."""
        backend = DiskBackend(cache_dir=temp_cache_dir)
        entry = CacheEntry(value="test")

        await backend.set("key1", entry)
        deleted = await backend.delete("key1")

        assert deleted is True
        assert await backend.get("key1") is None

    @pytest.mark.asyncio
    async def test_clear(self, temp_cache_dir):
        """Test clear operation."""
        backend = DiskBackend(cache_dir=temp_cache_dir)

        await backend.set("key1", CacheEntry(value="v1"))
        await backend.set("key2", CacheEntry(value="v2"))

        count = await backend.clear()

        assert count == 2
        assert await backend.size() == 0

    @pytest.mark.asyncio
    async def test_keys(self, temp_cache_dir):
        """Test keys operation."""
        backend = DiskBackend(cache_dir=temp_cache_dir)

        await backend.set("key1", CacheEntry(value="v1"))
        await backend.set("key2", CacheEntry(value="v2"))

        keys = await backend.keys()

        assert len(keys) == 2
        assert "key1" in keys
        assert "key2" in keys


class TestHybridBackend:
    """Test hybrid backend."""

    @pytest.fixture
    def temp_cache_dir(self):
        """Create temporary cache directory."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir, ignore_errors=True)

    @pytest.mark.asyncio
    async def test_write_through(self, temp_cache_dir):
        """Test that writes go to both L1 and L2."""
        memory_backend = MemoryBackend()
        disk_backend = DiskBackend(cache_dir=temp_cache_dir)
        hybrid = HybridBackend(memory_backend, disk_backend)

        entry = CacheEntry(value="test-value")
        await hybrid.set("key1", entry)

        # Check both backends have the value
        l1_result = await memory_backend.get("key1")
        l2_result = await disk_backend.get("key1")

        assert l1_result is not None
        assert l2_result is not None
        assert l1_result.value == "test-value"
        assert l2_result.value == "test-value"

    @pytest.mark.asyncio
    async def test_l1_hit(self, temp_cache_dir):
        """Test L1 cache hit."""
        memory_backend = MemoryBackend()
        disk_backend = DiskBackend(cache_dir=temp_cache_dir)
        hybrid = HybridBackend(memory_backend, disk_backend)

        entry = CacheEntry(value="l1-value")
        await memory_backend.set("key1", entry)

        result = await hybrid.get("key1")

        assert result is not None
        assert result.value == "l1-value"

    @pytest.mark.asyncio
    async def test_l2_hit_promotes_to_l1(self, temp_cache_dir):
        """Test that L2 hit promotes entry to L1."""
        memory_backend = MemoryBackend()
        disk_backend = DiskBackend(cache_dir=temp_cache_dir)
        hybrid = HybridBackend(memory_backend, disk_backend)

        # Set only in L2
        entry = CacheEntry(value="l2-value")
        await disk_backend.set("key1", entry)

        # Get from hybrid (should hit L2 and promote to L1)
        result = await hybrid.get("key1")

        assert result is not None
        assert result.value == "l2-value"

        # Verify it's now in L1
        l1_result = await memory_backend.get("key1")
        assert l1_result is not None
        assert l1_result.value == "l2-value"

    @pytest.mark.asyncio
    async def test_delete_from_both(self, temp_cache_dir):
        """Test that delete removes from both L1 and L2."""
        memory_backend = MemoryBackend()
        disk_backend = DiskBackend(cache_dir=temp_cache_dir)
        hybrid = HybridBackend(memory_backend, disk_backend)

        entry = CacheEntry(value="test")
        await hybrid.set("key1", entry)

        deleted = await hybrid.delete("key1")

        assert deleted is True
        assert await memory_backend.get("key1") is None
        assert await disk_backend.get("key1") is None


class TestCacheService:
    """Test cache service."""

    @pytest.mark.asyncio
    async def test_get_miss(self):
        """Test cache miss."""
        backend = MemoryBackend()
        cache = CacheService(backend=backend)

        result = await cache.get("nonexistent")

        assert result is None
        stats = await cache.get_stats()
        assert stats.misses == 1
        assert stats.hits == 0

    @pytest.mark.asyncio
    async def test_set_and_get_hit(self):
        """Test cache set and hit."""
        backend = MemoryBackend()
        cache = CacheService(backend=backend)

        await cache.set("key1", "value1", ttl=60)
        result = await cache.get("key1")

        assert result == "value1"
        stats = await cache.get_stats()
        assert stats.hits == 1
        assert stats.sets == 1

    @pytest.mark.asyncio
    async def test_ttl_expiration(self):
        """Test TTL expiration."""
        backend = MemoryBackend()
        cache = CacheService(backend=backend, default_ttl=1)

        await cache.set("key1", "value1", ttl=1)

        # Should be available immediately
        result = await cache.get("key1")
        assert result == "value1"

        # Wait for expiration
        await asyncio.sleep(1.1)

        # Should be expired now
        result = await cache.get("key1")
        assert result is None

    @pytest.mark.asyncio
    async def test_delete(self):
        """Test cache delete."""
        backend = MemoryBackend()
        cache = CacheService(backend=backend)

        await cache.set("key1", "value1")
        deleted = await cache.delete("key1")

        assert deleted is True
        assert await cache.get("key1") is None

    @pytest.mark.asyncio
    async def test_clear_all(self):
        """Test clearing all cache entries."""
        backend = MemoryBackend()
        cache = CacheService(backend=backend)

        await cache.set("key1", "value1")
        await cache.set("key2", "value2")
        await cache.set("key3", "value3")

        count = await cache.clear()

        assert count == 3
        assert await cache.get("key1") is None
        assert await cache.get("key2") is None

    @pytest.mark.asyncio
    async def test_clear_with_pattern(self):
        """Test clearing cache entries with pattern."""
        backend = MemoryBackend()
        cache = CacheService(backend=backend)

        await cache.set("app:key1", "value1")
        await cache.set("app:key2", "value2")
        await cache.set("other:key3", "value3")

        count = await cache.clear(pattern="app:")

        assert count == 2
        assert await cache.get("app:key1") is None
        assert await cache.get("app:key2") is None
        assert await cache.get("other:key3") == "value3"

    @pytest.mark.asyncio
    async def test_lru_eviction(self):
        """Test LRU eviction under memory pressure."""
        backend = MemoryBackend()
        cache = CacheService(backend=backend, max_size=5)

        # Fill cache to max_size
        for i in range(5):
            await cache.set(f"key{i}", f"value{i}")

        # Adding one more should trigger eviction
        await cache.set("key5", "value5")

        stats = await cache.get_stats()
        assert stats.evictions > 0
        assert await backend.size() <= 5

    @pytest.mark.asyncio
    async def test_stats_tracking(self):
        """Test statistics tracking."""
        backend = MemoryBackend()
        cache = CacheService(backend=backend, enable_stats=True)

        await cache.set("key1", "value1")
        await cache.get("key1")  # hit
        await cache.get("key2")  # miss
        await cache.delete("key1")

        stats = await cache.get_stats()

        assert stats.sets == 1
        assert stats.hits == 1
        assert stats.misses == 1
        assert stats.deletes == 1

    @pytest.mark.asyncio
    async def test_warmup(self):
        """Test cache warmup."""
        backend = MemoryBackend()
        cache = CacheService(backend=backend)

        async def loader(key: str) -> str:
            return f"loaded-{key}"

        keys = ["key1", "key2", "key3"]
        count = await cache.warmup(keys, loader)

        assert count == 3
        assert await cache.get("key1") == "loaded-key1"
        assert await cache.get("key2") == "loaded-key2"
        assert await cache.get("key3") == "loaded-key3"

    @pytest.mark.asyncio
    async def test_graceful_degradation(self):
        """Test graceful degradation on backend errors."""
        # Create a mock backend that raises errors
        backend = Mock()

        async def mock_get(key):
            raise Exception("Backend error")

        async def mock_size():
            return 0

        backend.get = mock_get
        backend.size = mock_size

        cache = CacheService(backend=backend, enable_stats=True)

        # Should not raise, should return None
        result = await cache.get("key1")
        assert result is None

        stats = await cache.get_stats()
        assert stats.errors == 1


class TestCacheKeyGeneration:
    """Test cache key generation utilities."""

    def test_make_cache_key_basic(self):
        """Test basic cache key generation."""
        key = make_cache_key("ecr", "us-east-1", "repos")
        assert key == f"v{CACHE_VERSION}:ecr:us-east-1:repos"

    def test_make_cache_key_filters_none(self):
        """Test that None values are filtered out."""
        key = make_cache_key("ecr", None, "repos")
        assert key == f"v{CACHE_VERSION}:ecr:repos"

    def test_make_cache_key_custom_version(self):
        """Test cache key with custom version."""
        key = make_cache_key("ecr", "repos", version=2)
        assert key == "v2:ecr:repos"

    def test_hash_params_consistency(self):
        """Test that hash_params generates consistent hashes."""
        hash1 = hash_params(tag="latest", filter="nginx")
        hash2 = hash_params(tag="latest", filter="nginx")
        assert hash1 == hash2

    def test_hash_params_order_independent(self):
        """Test that parameter order doesn't affect hash."""
        hash1 = hash_params(tag="latest", filter="nginx")
        hash2 = hash_params(filter="nginx", tag="latest")
        assert hash1 == hash2

    def test_hash_params_different_values(self):
        """Test that different values generate different hashes."""
        hash1 = hash_params(tag="latest")
        hash2 = hash_params(tag="v1.0")
        assert hash1 != hash2
