"""Integration tests for ECR service caching functionality.

Tests the caching behavior of ECRRepositoryService methods to ensure:
1. Cache hits return cached data without API calls
2. Cache misses trigger API calls and store results
3. Cache invalidation works correctly
4. Cache errors don't break functionality (graceful degradation)
"""

import asyncio
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock

import pytest

from ecreshore.services.ecr_repository import ECRRepository, ECRImage, ECRRepositoryService
from ecreshore.services.cache_manager import get_cache, clear_all_caches


@pytest.fixture(autouse=True)
def clear_cache():
    """Clear all caches before each test."""
    clear_all_caches()
    yield
    clear_all_caches()


@pytest.fixture
def mock_ecr_client():
    """Create a mock ECR client."""
    client = MagicMock()
    return client


@pytest.fixture
def ecr_service(mock_ecr_client):
    """Create ECRRepositoryService with mocked client."""
    with patch('boto3.client', return_value=mock_ecr_client):
        service = ECRRepositoryService(region_name="us-west-2", registry_id="123456789012")
        service._ecr_client = mock_ecr_client
        return service


class TestListRepositoriesCaching:
    """Test caching behavior of list_repositories method."""

    def test_cache_miss_triggers_api_call(self, ecr_service, mock_ecr_client):
        """First call should miss cache and call ECR API."""
        # Setup mock paginator
        mock_paginator = MagicMock()
        mock_ecr_client.get_paginator.return_value = mock_paginator

        mock_page = {
            "repositories": [
                {
                    "repositoryName": "test-repo",
                    "repositoryUri": "123456789012.dkr.ecr.us-west-2.amazonaws.com/test-repo",
                    "createdAt": datetime(2024, 1, 1),
                    "registryId": "123456789012",
                }
            ]
        }
        mock_paginator.paginate.return_value = [mock_page]

        # Mock the _get_repository_statistics method
        with patch.object(ecr_service, '_get_repository_statistics', return_value=(5, 1000000, "latest")):
            with patch.object(ecr_service, '_get_repository_tags', return_value={}):
                # First call - should hit API
                repos = ecr_service.list_repositories()

                assert len(repos) == 1
                assert repos[0].name == "test-repo"
                assert mock_paginator.paginate.call_count == 1

    def test_cache_hit_avoids_api_call(self, ecr_service, mock_ecr_client):
        """Second call with same parameters should use cache."""
        # Setup mock paginator
        mock_paginator = MagicMock()
        mock_ecr_client.get_paginator.return_value = mock_paginator

        mock_page = {
            "repositories": [
                {
                    "repositoryName": "test-repo",
                    "repositoryUri": "123456789012.dkr.ecr.us-west-2.amazonaws.com/test-repo",
                    "createdAt": datetime(2024, 1, 1),
                    "registryId": "123456789012",
                }
            ]
        }
        mock_paginator.paginate.return_value = [mock_page]

        # Mock the helper methods
        with patch.object(ecr_service, '_get_repository_statistics', return_value=(5, 1000000, "latest")):
            with patch.object(ecr_service, '_get_repository_tags', return_value={}):
                # First call - populates cache
                repos1 = ecr_service.list_repositories()

                # Second call - should use cache
                repos2 = ecr_service.list_repositories()

                assert len(repos1) == len(repos2)
                assert repos1[0].name == repos2[0].name
                # API should only be called once (first call)
                assert mock_paginator.paginate.call_count == 1

    def test_different_filters_create_separate_cache_entries(self, ecr_service, mock_ecr_client):
        """Different filter parameters should create separate cache entries."""
        mock_paginator = MagicMock()
        mock_ecr_client.get_paginator.return_value = mock_paginator

        mock_page1 = {
            "repositories": [
                {
                    "repositoryName": "prod-app",
                    "repositoryUri": "123456789012.dkr.ecr.us-west-2.amazonaws.com/prod-app",
                    "createdAt": datetime(2024, 1, 1),
                    "registryId": "123456789012",
                }
            ]
        }

        mock_page2 = {
            "repositories": [
                {
                    "repositoryName": "dev-app",
                    "repositoryUri": "123456789012.dkr.ecr.us-west-2.amazonaws.com/dev-app",
                    "createdAt": datetime(2024, 1, 1),
                    "registryId": "123456789012",
                }
            ]
        }

        # Return different results based on call count - wrap in lists for iteration
        mock_paginator.paginate.side_effect = [[mock_page1], [mock_page2]]

        with patch.object(ecr_service, '_get_repository_statistics', return_value=(5, 1000000, "latest")):
            with patch.object(ecr_service, '_get_repository_tags', return_value={}):
                # Two different filters
                repos1 = ecr_service.list_repositories(name_filter="prod")
                repos2 = ecr_service.list_repositories(name_filter="dev")

                # Both should trigger API calls (different cache keys)
                assert mock_paginator.paginate.call_count == 2


class TestListImagesCaching:
    """Test caching behavior of list_images method."""

    def test_cache_miss_triggers_api_call(self, ecr_service, mock_ecr_client):
        """First call should miss cache and call ECR API."""
        mock_paginator = MagicMock()
        mock_ecr_client.get_paginator.return_value = mock_paginator

        mock_page = {
            "imageIds": [
                {"imageTag": "latest", "imageDigest": "sha256:abc123"}
            ]
        }
        mock_paginator.paginate.return_value = [mock_page]

        # Mock describe_images
        with patch.object(ecr_service, '_describe_images', return_value=[
            {
                "imageTags": ["latest"],
                "imageDigest": "sha256:abc123",
                "imageSizeInBytes": 100 * 1024 * 1024,
                "imagePushedAt": datetime(2024, 1, 1),
            }
        ]):
            images = ecr_service.list_images("test-repo")

            assert len(images) == 1
            assert images[0].image_tags == ["latest"]
            assert mock_paginator.paginate.call_count == 1

    def test_cache_hit_avoids_api_call(self, ecr_service, mock_ecr_client):
        """Second call with same parameters should use cache."""
        mock_paginator = MagicMock()
        mock_ecr_client.get_paginator.return_value = mock_paginator

        mock_page = {
            "imageIds": [
                {"imageTag": "latest", "imageDigest": "sha256:abc123"}
            ]
        }
        mock_paginator.paginate.return_value = [mock_page]

        with patch.object(ecr_service, '_describe_images', return_value=[
            {
                "imageTags": ["latest"],
                "imageDigest": "sha256:abc123",
                "imageSizeInBytes": 100 * 1024 * 1024,
                "imagePushedAt": datetime(2024, 1, 1),
            }
        ]):
            # First call - populates cache
            images1 = ecr_service.list_images("test-repo")

            # Second call - should use cache
            images2 = ecr_service.list_images("test-repo")

            assert len(images1) == len(images2)
            assert images1[0].image_digest == images2[0].image_digest
            # API should only be called once
            assert mock_paginator.paginate.call_count == 1

    def test_different_tag_filters_create_separate_entries(self, ecr_service, mock_ecr_client):
        """Different tag filters should create separate cache entries."""
        mock_paginator = MagicMock()
        mock_ecr_client.get_paginator.return_value = mock_paginator

        mock_page = {
            "imageIds": [
                {"imageTag": "v1.0", "imageDigest": "sha256:abc123"}
            ]
        }
        mock_paginator.paginate.return_value = [mock_page]

        with patch.object(ecr_service, '_describe_images', return_value=[
            {
                "imageTags": ["v1.0"],
                "imageDigest": "sha256:abc123",
                "imageSizeInBytes": 100 * 1024 * 1024,
                "imagePushedAt": datetime(2024, 1, 1),
            }
        ]):
            # Two different filters
            images1 = ecr_service.list_images("test-repo", tag_filter="v1")
            images2 = ecr_service.list_images("test-repo", tag_filter="v2")

            # Both should trigger API calls (different cache keys)
            assert mock_paginator.paginate.call_count == 2


class TestRepositoryStatisticsCaching:
    """Test caching behavior of _get_repository_statistics method."""

    def test_cache_miss_triggers_api_call(self, ecr_service, mock_ecr_client):
        """First call should miss cache and call ECR API."""
        mock_paginator = MagicMock()
        mock_ecr_client.get_paginator.return_value = mock_paginator

        mock_page = {
            "imageIds": [
                {"imageTag": "latest", "imageDigest": "sha256:abc123"}
            ]
        }
        mock_paginator.paginate.return_value = [mock_page]

        with patch.object(ecr_service, '_describe_images', return_value=[
            {
                "imageTags": ["latest"],
                "imageDigest": "sha256:abc123",
                "imageSizeInBytes": 100 * 1024 * 1024,
                "imagePushedAt": datetime(2024, 1, 1),
            }
        ]):
            count, size, tag = ecr_service._get_repository_statistics("test-repo")

            assert count == 1
            assert size == 100 * 1024 * 1024
            assert tag == "latest"
            assert mock_paginator.paginate.call_count == 1

    def test_cache_hit_avoids_api_call(self, ecr_service, mock_ecr_client):
        """Second call should use cache."""
        mock_paginator = MagicMock()
        mock_ecr_client.get_paginator.return_value = mock_paginator

        mock_page = {
            "imageIds": [
                {"imageTag": "latest", "imageDigest": "sha256:abc123"}
            ]
        }
        mock_paginator.paginate.return_value = [mock_page]

        with patch.object(ecr_service, '_describe_images', return_value=[
            {
                "imageTags": ["latest"],
                "imageDigest": "sha256:abc123",
                "imageSizeInBytes": 100 * 1024 * 1024,
                "imagePushedAt": datetime(2024, 1, 1),
            }
        ]):
            # First call - populates cache
            stats1 = ecr_service._get_repository_statistics("test-repo")

            # Second call - should use cache
            stats2 = ecr_service._get_repository_statistics("test-repo")

            assert stats1 == stats2
            # API should only be called once
            assert mock_paginator.paginate.call_count == 1


class TestCacheGracefulDegradation:
    """Test that cache errors don't break functionality."""

    def test_cache_get_error_falls_back_to_api(self, ecr_service, mock_ecr_client):
        """If cache.get() fails, should fall back to API call."""
        mock_paginator = MagicMock()
        mock_ecr_client.get_paginator.return_value = mock_paginator

        mock_page = {
            "imageIds": [
                {"imageTag": "latest", "imageDigest": "sha256:abc123"}
            ]
        }
        mock_paginator.paginate.return_value = [mock_page]

        # Mock cache to raise error on get()
        cache = get_cache("ecr_images")
        original_get = cache.get

        async def failing_get(*args, **kwargs):
            raise RuntimeError("Cache error!")

        with patch.object(cache, 'get', side_effect=failing_get):
            with patch.object(ecr_service, '_describe_images', return_value=[
                {
                    "imageTags": ["latest"],
                    "imageDigest": "sha256:abc123",
                    "imageSizeInBytes": 100 * 1024 * 1024,
                    "imagePushedAt": datetime(2024, 1, 1),
                }
            ]):
                # Should still work despite cache error
                images = ecr_service.list_images("test-repo")

                assert len(images) == 1
                assert images[0].image_tags == ["latest"]

    def test_cache_set_error_doesnt_break_operation(self, ecr_service, mock_ecr_client):
        """If cache.set() fails, operation should still succeed."""
        mock_paginator = MagicMock()
        mock_ecr_client.get_paginator.return_value = mock_paginator

        mock_page = {
            "imageIds": [
                {"imageTag": "latest", "imageDigest": "sha256:abc123"}
            ]
        }
        mock_paginator.paginate.return_value = [mock_page]

        # Mock cache to raise error on set()
        cache = get_cache("ecr_images")

        async def failing_set(*args, **kwargs):
            raise RuntimeError("Cache write error!")

        with patch.object(cache, 'set', side_effect=failing_set):
            with patch.object(ecr_service, '_describe_images', return_value=[
                {
                    "imageTags": ["latest"],
                    "imageDigest": "sha256:abc123",
                    "imageSizeInBytes": 100 * 1024 * 1024,
                    "imagePushedAt": datetime(2024, 1, 1),
                }
            ]):
                # Should still work despite cache error
                images = ecr_service.list_images("test-repo")

                assert len(images) == 1
                assert images[0].image_tags == ["latest"]
