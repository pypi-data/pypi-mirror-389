"""Tests for image presence and digest caching functionality."""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from src.ecreshore.services.image_presence_checker import ImagePresenceChecker
from src.ecreshore.services.ecr_repository import ECRImage, ECRRepositoryService
from src.ecreshore.services.digest_verification import (
    get_enhanced_digest,
    get_platform_digests,
    PlatformDigestResult,
)
from src.ecreshore.services.cache_service import CacheService
from src.ecreshore.services.cache_backends import MemoryBackend
from src.ecreshore.services.cache_manager import reset_caches


class TestImagePresenceCaching:
    """Test caching for check_image_exists_in_ecr."""

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
    def sample_image(self):
        """Create sample ECR image."""
        from datetime import datetime
        return ECRImage(
            repository_name="my-repo",
            image_tags=["latest"],
            image_digest="sha256:abc123def456",
            size_bytes=1024,
            pushed_at=datetime.now(),
            registry_id="123456789012",
            region="us-east-1",
        )

    @pytest.mark.asyncio
    async def test_check_image_exists_cache_hit_positive(
        self, checker, mock_ecr_service, sample_image
    ):
        """Test that second call hits cache for existing image."""
        # Setup mock to return image on first call
        mock_ecr_service.list_images = Mock(return_value=[sample_image])

        # First call - cache miss, queries ECR
        image1 = await checker.check_image_exists_in_ecr("my-repo", "latest")

        # Verify mock was called once
        assert mock_ecr_service.list_images.call_count == 1

        # Second call - cache hit, no ECR query
        image2 = await checker.check_image_exists_in_ecr("my-repo", "latest")

        # Verify mock was NOT called again (still 1 call)
        assert mock_ecr_service.list_images.call_count == 1

        # Verify same image returned
        assert image1 == image2
        assert image1.image_digest == "sha256:abc123def456"

    @pytest.mark.asyncio
    async def test_check_image_exists_cache_hit_negative(
        self, checker, mock_ecr_service
    ):
        """Test that 'not found' results are cached."""
        # Setup mock to return empty list
        mock_ecr_service.list_images = Mock(return_value=[])

        # First call - image not found
        result1 = await checker.check_image_exists_in_ecr("my-repo", "missing")

        # Verify result is None
        assert result1 is None
        assert mock_ecr_service.list_images.call_count == 1

        # Second call - cache hit (negative)
        result2 = await checker.check_image_exists_in_ecr("my-repo", "missing")

        # Verify mock was NOT called again
        assert mock_ecr_service.list_images.call_count == 1
        assert result2 is None

    @pytest.mark.asyncio
    async def test_check_image_exists_different_repos_different_cache_keys(
        self, checker, mock_ecr_service, sample_image
    ):
        """Test that different repos create separate cache entries."""
        # Setup mock to return image
        mock_ecr_service.list_images = Mock(return_value=[sample_image])

        # Call for repo1
        await checker.check_image_exists_in_ecr("repo1", "latest")

        # Call for repo2
        await checker.check_image_exists_in_ecr("repo2", "latest")

        # Should call ECR twice (different cache keys)
        assert mock_ecr_service.list_images.call_count == 2

    @pytest.mark.asyncio
    async def test_check_image_exists_different_tags_different_cache_keys(
        self, checker, mock_ecr_service, sample_image
    ):
        """Test that different tags create separate cache entries."""
        mock_ecr_service.list_images = Mock(return_value=[sample_image])

        # Call for tag1
        await checker.check_image_exists_in_ecr("repo", "tag1")

        # Call for tag2
        await checker.check_image_exists_in_ecr("repo", "tag2")

        # Should call ECR twice (different cache keys)
        assert mock_ecr_service.list_images.call_count == 2

    @pytest.mark.asyncio
    async def test_check_image_exists_graceful_degradation(
        self, checker, mock_ecr_service
    ):
        """Test that cache errors don't break functionality."""
        # Make list_images work normally
        from datetime import datetime
        sample_image = ECRImage(
            repository_name="repo",
            image_tags=["latest"],
            image_digest="sha256:test123",
            size_bytes=1024,
            pushed_at=datetime.now(),
            registry_id="123456789012",
            region="us-east-1",
        )
        mock_ecr_service.list_images = Mock(return_value=[sample_image])

        # Patch get_cache to return a cache that raises exceptions
        # We need to wrap exceptions in try/except which check_image_exists_in_ecr should do
        with patch("src.ecreshore.services.image_presence_checker.get_cache") as mock_get_cache:
            mock_cache = Mock()

            # Make the cache.get() raise an exception
            async def failing_get(key):
                raise Exception("Cache error")

            mock_cache.get = failing_get
            mock_get_cache.return_value = mock_cache

            # Should gracefully fall back to ECR and still work
            result = await checker.check_image_exists_in_ecr("repo", "latest")

            # The function should handle the exception and fall back to ECR
            assert result is not None
            assert result.image_digest == "sha256:test123"
            assert mock_ecr_service.list_images.called

    @pytest.mark.asyncio
    async def test_check_image_exists_no_cache_when_disabled(
        self, checker, mock_ecr_service, sample_image
    ):
        """Test that caching is skipped when cache is disabled."""
        mock_ecr_service.list_images = Mock(return_value=[sample_image])

        # Patch get_cache to return None (cache disabled)
        with patch("src.ecreshore.services.image_presence_checker.get_cache", return_value=None):
            # First call
            result1 = await checker.check_image_exists_in_ecr("repo", "latest")
            assert mock_ecr_service.list_images.call_count == 1

            # Second call - should query ECR again (no caching)
            result2 = await checker.check_image_exists_in_ecr("repo", "latest")
            assert mock_ecr_service.list_images.call_count == 2

            # Both should return the image
            assert result1 == result2


class TestEnhancedDigestCaching:
    """Test caching for get_enhanced_digest."""

    @pytest.fixture(autouse=True)
    async def reset_cache(self):
        """Reset cache state before each test."""
        reset_caches()
        yield
        reset_caches()

    @pytest.mark.asyncio
    async def test_get_enhanced_digest_graceful_degradation(self):
        """Test that cache errors don't break functionality."""
        async def mock_buildx_inspect(self, repository, tag):
            from src.ecreshore.services.digest_verification import DigestResult
            return DigestResult(
                digest="sha256:test123",
                method="buildx_inspect",
                success=True
            )

        with patch(
            "src.ecreshore.services.digest_verification.EnhancedDigestVerification._get_digest_from_buildx_inspect",
            mock_buildx_inspect
        ):
            # Patch cache to raise exception
            with patch("src.ecreshore.services.digest_verification.get_cache") as mock_cache:
                mock_cache_instance = Mock()
                mock_cache_instance.get = AsyncMock(side_effect=Exception("Cache error"))
                mock_cache.return_value = mock_cache_instance

                # Should still work and return the digest
                digest = await get_enhanced_digest(None, "nginx", "latest")
                assert digest == "sha256:test123"


class TestPlatformDigestsCaching:
    """Test caching for get_platform_digests."""

    @pytest.fixture(autouse=True)
    async def reset_cache(self):
        """Reset cache state before each test."""
        reset_caches()
        yield
        reset_caches()

    @pytest.mark.asyncio
    async def test_get_platform_digests_cache_returns_result_object(self):
        """Test that cached platform digests return proper PlatformDigestResult."""
        # Use unique repo name to avoid cache pollution from other tests
        unique_repo = "unique-test-repo-cache-result"

        async def mock_platform_digests(self, repository, tag):
            return PlatformDigestResult(
                platform_digests={
                    "linux/amd64": "sha256:cached_digest",
                },
                method="buildx_platform_inspect",
                success=True
            )

        with patch(
            "src.ecreshore.services.digest_verification.EnhancedDigestVerification.get_platform_digests_from_buildx",
            mock_platform_digests
        ):
            # First call - populate cache
            result1 = await get_platform_digests(None, unique_repo, "latest")

            # Second call - from cache
            result2 = await get_platform_digests(None, unique_repo, "latest")

            # Verify result is proper PlatformDigestResult with cache method
            assert isinstance(result2, PlatformDigestResult)
            assert result2.method == "cache"
            assert result2.success is True
            assert result2.platform_digests["linux/amd64"] == "sha256:cached_digest"


class TestCacheKeyUniqueness:
    """Test cache key uniqueness for proper cache isolation."""

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

    @pytest.mark.asyncio
    async def test_different_regions_different_cache_keys(self, mock_ecr_service):
        """Test that different regions create separate cache entries."""
        from datetime import datetime
        # Setup for us-east-1
        mock_ecr_service.region_name = "us-east-1"
        mock_ecr_service.list_images = Mock(return_value=[
            ECRImage(
                repository_name="repo",
                image_tags=["latest"],
                image_digest="sha256:east_digest",
                size_bytes=1024,
                pushed_at=datetime.now(),
                registry_id="123456789012",
                region="us-east-1",
            )
        ])

        checker_east = ImagePresenceChecker(mock_ecr_service)
        result_east = await checker_east.check_image_exists_in_ecr("repo", "latest")

        # Setup for us-west-2
        mock_ecr_service.region_name = "us-west-2"
        mock_ecr_service.list_images = Mock(return_value=[
            ECRImage(
                repository_name="repo",
                image_tags=["latest"],
                image_digest="sha256:west_digest",
                size_bytes=1024,
                pushed_at=datetime.now(),
                registry_id="123456789012",
                region="us-west-2",
            )
        ])

        checker_west = ImagePresenceChecker(mock_ecr_service)
        result_west = await checker_west.check_image_exists_in_ecr("repo", "latest")

        # Should have different digests (not from cache)
        assert result_east.image_digest == "sha256:east_digest"
        assert result_west.image_digest == "sha256:west_digest"

    @pytest.mark.asyncio
    async def test_different_registry_ids_different_cache_keys(self, mock_ecr_service):
        """Test that different registry IDs create separate cache entries."""
        from datetime import datetime
        # Setup for registry1
        mock_ecr_service.registry_id = "111111111111"
        mock_ecr_service.list_images = Mock(return_value=[
            ECRImage(
                repository_name="repo",
                image_tags=["latest"],
                image_digest="sha256:registry1_digest",
                size_bytes=1024,
                pushed_at=datetime.now(),
                registry_id="111111111111",
                region="us-east-1",
            )
        ])

        checker1 = ImagePresenceChecker(mock_ecr_service)
        result1 = await checker1.check_image_exists_in_ecr("repo", "latest")

        # Setup for registry2
        mock_ecr_service.registry_id = "222222222222"
        mock_ecr_service.list_images = Mock(return_value=[
            ECRImage(
                repository_name="repo",
                image_tags=["latest"],
                image_digest="sha256:registry2_digest",
                size_bytes=1024,
                pushed_at=datetime.now(),
                registry_id="222222222222",
                region="us-east-1",
            )
        ])

        checker2 = ImagePresenceChecker(mock_ecr_service)
        result2 = await checker2.check_image_exists_in_ecr("repo", "latest")

        # Should have different digests (not from cache)
        assert result1.image_digest == "sha256:registry1_digest"
        assert result2.image_digest == "sha256:registry2_digest"
