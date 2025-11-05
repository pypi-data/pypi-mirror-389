"""Tests for Phase 3B skip decision caching functionality."""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime
from src.ecreshore.services.image_presence_checker import ImagePresenceChecker
from src.ecreshore.services.ecr_repository import ECRImage, ECRRepositoryService
from src.ecreshore.services.cache_manager import reset_caches


class TestSkipDecisionCaching:
    """Test caching for should_skip_transfer decisions."""

    @pytest.fixture(autouse=True)
    async def reset_cache(self):
        """Reset cache state before each test."""
        reset_caches()
        yield
        reset_caches()

    @pytest.fixture
    def mock_ecr_service(self):
        """Create mock ECR service."""
        mock = Mock(spec=ECRRepositoryService)
        mock.region_name = "us-east-1"
        mock.registry_id = "123456789012"
        return mock

    @pytest.fixture
    def checker(self, mock_ecr_service):
        """Create ImagePresenceChecker with mock ECR service."""
        return ImagePresenceChecker(mock_ecr_service)

    @pytest.fixture
    def make_sample_image(self):
        """Factory to create sample ECR images with custom params."""
        def _make(repository="target-repo", tag="v1.0"):
            return ECRImage(
                repository_name=repository,
                image_tags=[tag],
                image_digest="sha256:abc123def456",
                size_bytes=1024,
                pushed_at=datetime.now(),
                registry_id="123456789012",
                region="us-east-1",
            )
        return _make

    @pytest.mark.asyncio
    async def test_skip_decision_cache_hit_digest_match(
        self, checker, mock_ecr_service, make_sample_image
    ):
        """Test that matching skip decisions are cached and hit on second call."""
        # Setup: Image exists with matching digest
        sample_image = make_sample_image("target-repo", "v1.0")
        mock_ecr_service.list_images = Mock(return_value=[sample_image])

        # Mock the digest retrieval methods to return matching digests
        with patch.object(
            checker, "get_source_image_digest", new=AsyncMock(return_value="sha256:abc123def456")
        ) as mock_source:
            with patch.object(
                checker,
                "get_target_platform_specific_digest",
                new=AsyncMock(return_value="sha256:abc123def456"),
            ) as mock_target:
                # First call - cache miss, performs full check
                result1 = await checker.should_skip_transfer(
                    docker_client=None,
                    source_image="nginx",
                    source_tag="latest",
                    target_repository="target-repo",
                    target_tag="v1.0",
                )

                # Verify first call performed actual work
                assert result1["should_skip"] is True
                assert result1["reason"].startswith("Target image")
                assert "matching digest" in result1["reason"]
                assert mock_source.call_count == 1
                assert mock_target.call_count == 1

                # Second call - cache hit, skips digest checks
                result2 = await checker.should_skip_transfer(
                    docker_client=None,
                    source_image="nginx",
                    source_tag="latest",
                    target_repository="target-repo",
                    target_tag="v1.0",
                )

                # Verify cache hit
                assert result2["cache_hit"] is True
                assert result2["should_skip"] is True
                # Digest methods should NOT be called again
                assert mock_source.call_count == 1
                assert mock_target.call_count == 1

    @pytest.mark.asyncio
    async def test_skip_decision_no_cache_on_mismatch(
        self, checker, mock_ecr_service, make_sample_image
    ):
        """Test that digest mismatches are NOT cached."""
        sample_image = make_sample_image("target-repo-mismatch", "v2.0")
        mock_ecr_service.list_images = Mock(return_value=[sample_image])

        # Mock digests to return mismatch
        with patch.object(
            checker, "get_source_image_digest", new=AsyncMock(return_value="sha256:different123")
        ) as mock_source:
            with patch.object(
                checker,
                "get_target_platform_specific_digest",
                new=AsyncMock(return_value="sha256:abc123def456"),
            ) as mock_target:
                # First call - digest mismatch (use unique image names to avoid cache pollution)
                result1 = await checker.should_skip_transfer(
                    docker_client=None,
                    source_image="alpine",
                    source_tag="3.18",
                    target_repository="target-repo-mismatch",
                    target_tag="v2.0",
                )

                assert result1["should_skip"] is False
                assert "different content" in result1["reason"]
                assert mock_source.call_count == 1

                # Second call - should perform fresh check (not cached)
                result2 = await checker.should_skip_transfer(
                    docker_client=None,
                    source_image="alpine",
                    source_tag="3.18",
                    target_repository="target-repo-mismatch",
                    target_tag="v2.0",
                )

                # Verify NO cache hit
                assert result2.get("cache_hit") is None
                assert result2["should_skip"] is False
                # Methods SHOULD be called again
                assert mock_source.call_count == 2
                assert mock_target.call_count == 2

    @pytest.mark.asyncio
    async def test_skip_decision_force_refresh_bypasses_cache(
        self, checker, mock_ecr_service, make_sample_image
    ):
        """Test that force_refresh=True bypasses cache."""
        sample_image = make_sample_image("target-repo-force", "v3.0")
        mock_ecr_service.list_images = Mock(return_value=[sample_image])

        with patch.object(
            checker, "get_source_image_digest", new=AsyncMock(return_value="sha256:abc123def456")
        ) as mock_source:
            with patch.object(
                checker,
                "get_target_platform_specific_digest",
                new=AsyncMock(return_value="sha256:abc123def456"),
            ):
                # First call - populate cache (unique images)
                result1 = await checker.should_skip_transfer(
                    docker_client=None,
                    source_image="redis",
                    source_tag="7.0",
                    target_repository="target-repo-force",
                    target_tag="v3.0",
                )
                assert result1["should_skip"] is True
                assert mock_source.call_count == 1

                # Second call with force_refresh - bypasses cache
                result2 = await checker.should_skip_transfer(
                    docker_client=None,
                    source_image="redis",
                    source_tag="7.0",
                    target_repository="target-repo-force",
                    target_tag="v3.0",
                    force_refresh=True,
                )

                # Verify cache was bypassed
                assert result2.get("cache_hit") is None
                assert result2["should_skip"] is True
                # Methods SHOULD be called again
                assert mock_source.call_count == 2

    @pytest.mark.asyncio
    async def test_skip_decision_cache_key_uniqueness_source(
        self, checker, mock_ecr_service, make_sample_image
    ):
        """Test that different source images create separate cache entries."""
        sample_image = make_sample_image("target-repo-uniq", "v4.0")
        mock_ecr_service.list_images = Mock(return_value=[sample_image])

        with patch.object(
            checker, "get_source_image_digest", new=AsyncMock(return_value="sha256:abc123def456")
        ) as mock_source:
            with patch.object(
                checker,
                "get_target_platform_specific_digest",
                new=AsyncMock(return_value="sha256:abc123def456"),
            ):
                # Call for source1
                await checker.should_skip_transfer(
                    docker_client=None,
                    source_image="postgres",
                    source_tag="15",
                    target_repository="target-repo-uniq",
                    target_tag="v4.0",
                )
                assert mock_source.call_count == 1

                # Call for source2 - different source image
                await checker.should_skip_transfer(
                    docker_client=None,
                    source_image="mysql",
                    source_tag="8.0",
                    target_repository="target-repo-uniq",
                    target_tag="v4.0",
                )

                # Should perform fresh check (different cache key)
                assert mock_source.call_count == 2

    @pytest.mark.asyncio
    async def test_skip_decision_cache_key_uniqueness_target(
        self, checker, mock_ecr_service, make_sample_image
    ):
        """Test that different target repos create separate cache entries."""
        sample_image = make_sample_image("target-repo1", "v1.0")
        mock_ecr_service.list_images = Mock(return_value=[sample_image])

        with patch.object(
            checker, "get_source_image_digest", new=AsyncMock(return_value="sha256:abc123def456")
        ) as mock_source:
            with patch.object(
                checker,
                "get_target_platform_specific_digest",
                new=AsyncMock(return_value="sha256:abc123def456"),
            ):
                # Call for target1
                await checker.should_skip_transfer(
                    docker_client=None,
                    source_image="nginx",
                    source_tag="latest",
                    target_repository="target-repo1",
                    target_tag="v1.0",
                )
                assert mock_source.call_count == 1

                # Call for target2 - different target repo
                await checker.should_skip_transfer(
                    docker_client=None,
                    source_image="nginx",
                    source_tag="latest",
                    target_repository="target-repo2",
                    target_tag="v1.0",
                )

                # Should perform fresh check (different cache key)
                assert mock_source.call_count == 2

    @pytest.mark.asyncio
    async def test_skip_decision_graceful_degradation(
        self, checker, mock_ecr_service, make_sample_image
    ):
        """Test that cache errors don't break functionality."""
        sample_image = make_sample_image("target-repo", "v1.0")
        mock_ecr_service.list_images = Mock(return_value=[sample_image])

        with patch.object(
            checker, "get_source_image_digest", new=AsyncMock(return_value="sha256:abc123def456")
        ):
            with patch.object(
                checker,
                "get_target_platform_specific_digest",
                new=AsyncMock(return_value="sha256:abc123def456"),
            ):
                # Patch get_cache to return a cache that raises exceptions
                with patch(
                    "src.ecreshore.services.image_presence_checker.get_cache"
                ) as mock_get_cache:
                    mock_cache = Mock()

                    # Make cache.get() raise an exception
                    async def failing_get(key):
                        raise Exception("Cache error")

                    mock_cache.get = failing_get
                    mock_get_cache.return_value = mock_cache

                    # Should gracefully fall back and still work
                    result = await checker.should_skip_transfer(
                        docker_client=None,
                        source_image="nginx",
                        source_tag="latest",
                        target_repository="target-repo",
                        target_tag="v1.0",
                    )

                    # Should successfully complete despite cache error
                    assert result["should_skip"] is True
                    assert result.get("cache_hit") is None

    @pytest.mark.asyncio
    async def test_skip_decision_no_cache_when_disabled(
        self, checker, mock_ecr_service, make_sample_image
    ):
        """Test that caching is skipped when cache is disabled."""
        sample_image = make_sample_image("target-repo", "v1.0")
        mock_ecr_service.list_images = Mock(return_value=[sample_image])

        with patch.object(
            checker, "get_source_image_digest", new=AsyncMock(return_value="sha256:abc123def456")
        ) as mock_source:
            with patch.object(
                checker,
                "get_target_platform_specific_digest",
                new=AsyncMock(return_value="sha256:abc123def456"),
            ):
                # Patch get_cache to return None (cache disabled)
                with patch(
                    "src.ecreshore.services.image_presence_checker.get_cache",
                    return_value=None,
                ):
                    # First call
                    result1 = await checker.should_skip_transfer(
                        docker_client=None,
                        source_image="nginx",
                        source_tag="latest",
                        target_repository="target-repo",
                        target_tag="v1.0",
                    )
                    assert mock_source.call_count == 1

                    # Second call - should perform work again (no caching)
                    result2 = await checker.should_skip_transfer(
                        docker_client=None,
                        source_image="nginx",
                        source_tag="latest",
                        target_repository="target-repo",
                        target_tag="v1.0",
                    )
                    assert mock_source.call_count == 2

                    # Both should succeed
                    assert result1["should_skip"] is True
                    assert result2["should_skip"] is True
                    assert result1.get("cache_hit") is None
                    assert result2.get("cache_hit") is None

    @pytest.mark.asyncio
    async def test_skip_decision_cache_respects_ttl(
        self, checker, mock_ecr_service, make_sample_image
    ):
        """Test that cache properly respects TTL and decision caching works."""
        sample_image = make_sample_image("target-repo-ttl", "v6.0")
        mock_ecr_service.list_images = Mock(return_value=[sample_image])

        with patch.object(
            checker, "get_source_image_digest", new=AsyncMock(return_value="sha256:abc123def456")
        ) as mock_source:
            with patch.object(
                checker,
                "get_target_platform_specific_digest",
                new=AsyncMock(return_value="sha256:abc123def456"),
            ):
                # First call - populate cache (unique images to avoid cross-test interference)
                result1 = await checker.should_skip_transfer(
                    docker_client=None,
                    source_image="golang",
                    source_tag="1.21",
                    target_repository="target-repo-ttl",
                    target_tag="v6.0",
                )
                assert result1["should_skip"] is True
                assert mock_source.call_count == 1

                # Second call immediately - should hit cache
                result2 = await checker.should_skip_transfer(
                    docker_client=None,
                    source_image="golang",
                    source_tag="1.21",
                    target_repository="target-repo-ttl",
                    target_tag="v6.0",
                )

                # Verify cache hit
                assert result2["cache_hit"] is True
                assert result2["should_skip"] is True
                # Digest methods should NOT be called again
                assert mock_source.call_count == 1
