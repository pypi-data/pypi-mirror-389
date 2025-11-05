"""Tests for @cached decorator."""

import asyncio
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from src.ecreshore.services.cache_service import cached, CacheService, make_cache_key
from src.ecreshore.services.cache_backends import MemoryBackend


class TestCachedDecorator:
    """Test the @cached decorator for transparent caching."""

    @pytest.mark.asyncio
    async def test_decorator_cache_miss_and_hit(self):
        """Test that decorator caches function results."""
        # Track function calls
        call_count = 0

        @cached(cache_name="test_category", ttl=300)
        async def expensive_operation(value: str) -> str:
            nonlocal call_count
            call_count += 1
            await asyncio.sleep(0.01)  # Simulate expensive operation
            return f"result_{value}"

        # Mock get_cache to return a real cache instance
        backend = MemoryBackend()
        cache = CacheService(backend=backend, enable_stats=True)

        with patch("src.ecreshore.services.cache_manager.get_cache", return_value=cache):
            # First call - cache miss
            result1 = await expensive_operation("test")
            assert result1 == "result_test"
            assert call_count == 1

            # Second call - cache hit
            result2 = await expensive_operation("test")
            assert result2 == "result_test"
            assert call_count == 1  # Function not called again

            # Verify cache stats
            stats = await cache.get_stats()
            assert stats.hits == 1
            assert stats.misses == 1
            assert stats.sets == 1

    @pytest.mark.asyncio
    async def test_decorator_custom_key_fn(self):
        """Test decorator with custom key function."""
        call_count = 0

        # Custom key function that uses specific parameters (ignores kwargs)
        @cached(
            cache_name="test_category",
            ttl=300,
            key_fn=lambda obj_id, name, ignore_me=None: f"{obj_id}:{name}"
        )
        async def fetch_data(obj_id: str, name: str, ignore_me: str = None) -> str:
            nonlocal call_count
            call_count += 1
            return f"data_{obj_id}_{name}"

        backend = MemoryBackend()
        cache = CacheService(backend=backend)

        with patch("src.ecreshore.services.cache_manager.get_cache", return_value=cache):
            # First call
            result1 = await fetch_data("123", "foo", ignore_me="bar")
            assert result1 == "data_123_foo"
            assert call_count == 1

            # Second call with same obj_id and name (ignore_me is different but ignored)
            result2 = await fetch_data("123", "foo", ignore_me="different")
            assert result2 == "data_123_foo"
            assert call_count == 1  # Cached!

            # Third call with different obj_id
            result3 = await fetch_data("456", "foo", ignore_me="bar")
            assert result3 == "data_456_foo"
            assert call_count == 2  # New cache key

    @pytest.mark.asyncio
    async def test_decorator_respects_ttl(self):
        """Test that decorator respects TTL parameter."""
        call_count = 0

        @cached(cache_name="test_category", ttl=1)  # 1 second TTL
        async def timed_operation(value: str) -> str:
            nonlocal call_count
            call_count += 1
            return f"result_{value}"

        backend = MemoryBackend()
        cache = CacheService(backend=backend)

        with patch("src.ecreshore.services.cache_manager.get_cache", return_value=cache):
            # First call
            result1 = await timed_operation("test")
            assert result1 == "result_test"
            assert call_count == 1

            # Immediate second call - cache hit
            result2 = await timed_operation("test")
            assert result2 == "result_test"
            assert call_count == 1

            # Wait for TTL expiration
            await asyncio.sleep(1.1)

            # Third call after expiration - cache miss
            result3 = await timed_operation("test")
            assert result3 == "result_test"
            assert call_count == 2  # Function called again

    @pytest.mark.asyncio
    async def test_decorator_cache_disabled(self):
        """Test decorator behavior when cache is disabled."""
        call_count = 0

        @cached(cache_name="test_category", ttl=300)
        async def uncached_operation(value: str) -> str:
            nonlocal call_count
            call_count += 1
            return f"result_{value}"

        # Mock get_cache to return None (cache disabled)
        with patch("src.ecreshore.services.cache_manager.get_cache", return_value=None):
            # All calls should execute the function
            result1 = await uncached_operation("test")
            assert result1 == "result_test"
            assert call_count == 1

            result2 = await uncached_operation("test")
            assert result2 == "result_test"
            assert call_count == 2  # Function called again (no caching)

    @pytest.mark.asyncio
    async def test_decorator_graceful_degradation_on_get_error(self):
        """Test that decorator gracefully handles cache get errors."""
        call_count = 0

        @cached(cache_name="test_category", ttl=300)
        async def resilient_operation(value: str) -> str:
            nonlocal call_count
            call_count += 1
            return f"result_{value}"

        # Create a mock cache that raises on get()
        mock_cache = AsyncMock(spec=CacheService)
        mock_cache.get.side_effect = Exception("Cache get error")
        mock_cache.set = AsyncMock()

        with patch("src.ecreshore.services.cache_manager.get_cache", return_value=mock_cache):
            # Should not raise, should execute function
            result = await resilient_operation("test")
            assert result == "result_test"
            assert call_count == 1

            # Should still attempt to cache the result
            mock_cache.set.assert_called_once()

    @pytest.mark.asyncio
    async def test_decorator_graceful_degradation_on_set_error(self):
        """Test that decorator gracefully handles cache set errors."""
        call_count = 0

        @cached(cache_name="test_category", ttl=300)
        async def resilient_operation(value: str) -> str:
            nonlocal call_count
            call_count += 1
            return f"result_{value}"

        # Create a mock cache that raises on set()
        mock_cache = AsyncMock(spec=CacheService)
        mock_cache.get.return_value = None  # Cache miss
        mock_cache.set.side_effect = Exception("Cache set error")

        with patch("src.ecreshore.services.cache_manager.get_cache", return_value=mock_cache):
            # Should not raise, should return result
            result = await resilient_operation("test")
            assert result == "result_test"
            assert call_count == 1

    @pytest.mark.asyncio
    async def test_decorator_different_kwargs_different_cache(self):
        """Test that different kwargs produce different cache keys."""
        call_count = 0

        @cached(cache_name="test_category", ttl=300)
        async def parameterized_operation(base: str, tag: str = "latest", filter: str = None) -> str:
            nonlocal call_count
            call_count += 1
            return f"{base}:{tag}:{filter}"

        backend = MemoryBackend()
        cache = CacheService(backend=backend)

        with patch("src.ecreshore.services.cache_manager.get_cache", return_value=cache):
            # First call with tag="latest"
            result1 = await parameterized_operation("repo", tag="latest")
            assert call_count == 1

            # Second call with tag="v1.0" - different cache key
            result2 = await parameterized_operation("repo", tag="v1.0")
            assert call_count == 2

            # Third call with tag="latest" again - cache hit
            result3 = await parameterized_operation("repo", tag="latest")
            assert call_count == 2  # Cached!

    @pytest.mark.asyncio
    async def test_decorator_returns_correct_type(self):
        """Test that decorator preserves return type."""
        @cached(cache_name="test_category", ttl=300)
        async def return_dict(key: str) -> dict:
            return {"key": key, "value": f"result_{key}"}

        @cached(cache_name="test_category", ttl=300)
        async def return_list(count: int) -> list:
            return [i for i in range(count)]

        backend = MemoryBackend()
        cache = CacheService(backend=backend)

        with patch("src.ecreshore.services.cache_manager.get_cache", return_value=cache):
            # Test dict return
            dict_result = await return_dict("test")
            assert isinstance(dict_result, dict)
            assert dict_result["key"] == "test"

            # Test list return
            list_result = await return_list(5)
            assert isinstance(list_result, list)
            assert len(list_result) == 5

            # Verify both are cached
            dict_result2 = await return_dict("test")
            list_result2 = await return_list(5)
            assert dict_result2 == dict_result
            assert list_result2 == list_result

    @pytest.mark.asyncio
    async def test_decorator_cache_key_generation(self):
        """Test that decorator generates correct cache keys."""
        @cached(cache_name="ecr_repos", ttl=300)
        async def list_repos(region: str, filter: str = None) -> list:
            return [f"{region}:repo1", f"{region}:repo2"]

        backend = MemoryBackend()
        cache = CacheService(backend=backend)

        with patch("src.ecreshore.services.cache_manager.get_cache", return_value=cache):
            # Call function
            await list_repos("us-east-1", filter="nginx")

            # Verify cache key was created correctly
            keys = await backend.keys()
            assert len(keys) == 1
            # Key should include cache_name and params hash
            assert keys[0].startswith("v1:ecr_repos:list_repos:")

    @pytest.mark.asyncio
    async def test_decorator_with_none_values(self):
        """Test decorator handles None return values correctly."""
        call_count = 0

        @cached(cache_name="test_category", ttl=300)
        async def may_return_none(value: str) -> str:
            nonlocal call_count
            call_count += 1
            if value == "none":
                return None
            return f"result_{value}"

        backend = MemoryBackend()
        cache = CacheService(backend=backend)

        with patch("src.ecreshore.services.cache_manager.get_cache", return_value=cache):
            # Call with "none" - returns None
            result1 = await may_return_none("none")
            assert result1 is None
            assert call_count == 1

            # Call again - None is not cached (by design, cache.get returns None for miss)
            result2 = await may_return_none("none")
            assert result2 is None
            assert call_count == 2  # Function called again

            # Call with normal value
            result3 = await may_return_none("test")
            assert result3 == "result_test"
            assert call_count == 3

            # Call again - this time it's cached
            result4 = await may_return_none("test")
            assert result4 == "result_test"
            assert call_count == 3  # Cached!

    @pytest.mark.asyncio
    async def test_decorator_concurrent_calls(self):
        """Test decorator behavior with concurrent calls (cache stampede scenario)."""
        call_count = 0
        call_times = []

        @cached(cache_name="test_category", ttl=300)
        async def slow_operation(value: str) -> str:
            nonlocal call_count
            call_count += 1
            call_times.append(asyncio.get_event_loop().time())
            await asyncio.sleep(0.1)  # Simulate slow operation
            return f"result_{value}"

        backend = MemoryBackend()
        cache = CacheService(backend=backend)

        with patch("src.ecreshore.services.cache_manager.get_cache", return_value=cache):
            # Launch 5 concurrent calls
            results = await asyncio.gather(*[
                slow_operation("test") for _ in range(5)
            ])

            # All should return the same result
            assert all(r == "result_test" for r in results)

            # Note: Without cache stampede protection, all 5 calls will execute
            # This is expected behavior - stampede protection would require locking
            # Current implementation is simple and fast
            # TODO: Future enhancement could add stampede protection
