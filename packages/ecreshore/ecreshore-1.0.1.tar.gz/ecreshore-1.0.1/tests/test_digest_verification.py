"""Tests for enhanced digest verification service."""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from src.ecreshore.services.digest_verification import (
    EnhancedDigestVerification,
    DigestResult,
    get_enhanced_digest
)
from src.ecreshore.services.cache_manager import reset_caches


@pytest.fixture(autouse=True)
async def reset_cache():
    """Reset cache state before and after each test."""
    reset_caches()
    yield
    reset_caches()


@pytest.fixture
def digest_verifier():
    """Create digest verifier instance for testing."""
    return EnhancedDigestVerification(max_retries=2, retry_delay=0.1)


@pytest.fixture
def mock_docker_client():
    """Create mock Docker client with async method support."""
    client = Mock()
    client.docker = Mock()
    client.docker.images = Mock()
    # Pre-configure get as AsyncMock since it's an async method
    client.docker.images.get = AsyncMock()
    return client


def test_select_best_repo_digest_exact_match(digest_verifier):
    """Test selection of exact repository match."""
    repo_digests = [
        "nginx@sha256:abc123",
        "my-nginx@sha256:def456",
        "registry.com/my-nginx@sha256:ghi789"
    ]

    result = digest_verifier._select_best_repo_digest(repo_digests, "my-nginx")
    assert result == "my-nginx@sha256:def456"


def test_select_best_repo_digest_full_path_match(digest_verifier):
    """Test selection with full repository path."""
    repo_digests = [
        "nginx@sha256:abc123",
        "registry.com/my-nginx@sha256:ghi789"
    ]

    result = digest_verifier._select_best_repo_digest(repo_digests, "registry.com/my-nginx")
    assert result == "registry.com/my-nginx@sha256:ghi789"


def test_select_best_repo_digest_ecr_priority(digest_verifier):
    """Test ECR digest priority for ECR repositories."""
    repo_digests = [
        "nginx@sha256:abc123",
        "123456789.dkr.ecr.us-east-1.amazonaws.com/my-app@sha256:def456"
    ]

    result = digest_verifier._select_best_repo_digest(repo_digests, "123456789.dkr.ecr.us-east-1.amazonaws.com/my-app")
    assert result == "123456789.dkr.ecr.us-east-1.amazonaws.com/my-app@sha256:def456"


def test_select_best_repo_digest_fallback(digest_verifier):
    """Test fallback to first digest when no match."""
    repo_digests = [
        "nginx@sha256:abc123",
        "postgres@sha256:def456"
    ]

    result = digest_verifier._select_best_repo_digest(repo_digests, "redis")
    assert result == "nginx@sha256:abc123"


def test_select_best_repo_digest_empty_list(digest_verifier):
    """Test handling of empty digest list."""
    result = digest_verifier._select_best_repo_digest([], "nginx")
    assert result is None


def test_extract_registry_from_digest(digest_verifier):
    """Test registry extraction from digest strings."""
    # Standard registry
    registry = digest_verifier._extract_registry_from_digest("registry.com/org/app@sha256:abc123")
    assert registry == "registry.com"

    # ECR registry
    registry = digest_verifier._extract_registry_from_digest("123456789.dkr.ecr.us-east-1.amazonaws.com/app@sha256:def456")
    assert registry == "123456789.dkr.ecr.us-east-1.amazonaws.com"

    # Docker Hub (no explicit registry)
    registry = digest_verifier._extract_registry_from_digest("nginx@sha256:ghi789")
    assert registry == "docker.io"

    # Invalid format
    registry = digest_verifier._extract_registry_from_digest("invalid-digest-format")
    assert registry is None


@pytest.mark.asyncio
async def test_get_digest_from_repo_digests_success(digest_verifier, mock_docker_client):
    """Test successful digest retrieval from RepoDigests."""
    # Mock image data with RepoDigests
    mock_image_data = {
        'Id': 'sha256:image123',
        'RepoDigests': ['nginx@sha256:content123']
    }
    mock_docker_client.docker.images.get = AsyncMock(return_value=mock_image_data)

    result = await digest_verifier._get_digest_from_repo_digests(
        mock_docker_client, "nginx:latest", "nginx"
    )

    assert result.success is True
    assert result.digest == "sha256:content123"
    assert result.method == "repo_digests"
    assert result.registry == "docker.io"


@pytest.mark.asyncio
async def test_get_digest_from_repo_digests_no_digests(digest_verifier, mock_docker_client):
    """Test handling when no RepoDigests available."""
    mock_image_data = {
        'Id': 'sha256:image123',
        'RepoDigests': []
    }
    mock_docker_client.docker.images.get = AsyncMock(return_value=mock_image_data)

    result = await digest_verifier._get_digest_from_repo_digests(
        mock_docker_client, "nginx:latest", "nginx"
    )

    assert result.success is False
    assert result.digest is None
    assert "No RepoDigests available" in result.error


@pytest.mark.asyncio
async def test_get_digest_from_image_id_success(digest_verifier, mock_docker_client):
    """Test successful digest retrieval from Image ID."""
    mock_image_data = {
        'Id': 'sha256:image123456',
        'RepoDigests': []
    }
    mock_docker_client.docker.images.get = AsyncMock(return_value=mock_image_data)

    result = await digest_verifier._get_digest_from_image_id(
        mock_docker_client, "nginx:latest"
    )

    assert result.success is True
    assert result.digest == "sha256:image123456"
    assert result.method == "image_id"


@pytest.mark.asyncio
async def test_get_digest_from_image_id_invalid_format(digest_verifier, mock_docker_client):
    """Test handling of invalid Image ID format."""
    mock_image_data = {
        'Id': 'invalid-format-123',
        'RepoDigests': []
    }
    mock_docker_client.docker.images.get = AsyncMock(return_value=mock_image_data)

    result = await digest_verifier._get_digest_from_image_id(
        mock_docker_client, "nginx:latest"
    )

    assert result.success is False
    assert result.digest is None
    assert "not in expected format" in result.error


@pytest.mark.asyncio
async def test_get_content_digest_with_fallback_success(digest_verifier, mock_docker_client):
    """Test successful digest retrieval with fallback strategy."""
    # First call (RepoDigests) succeeds
    mock_image_data = {
        'Id': 'sha256:image123',
        'RepoDigests': ['nginx@sha256:content123']
    }
    mock_docker_client.docker.images.get = AsyncMock(return_value=mock_image_data)

    result = await digest_verifier.get_content_digest_with_fallback(
        mock_docker_client, "nginx", "latest"
    )

    assert result.success is True
    assert result.digest == "sha256:content123"
    assert result.method == "repo_digests"


@pytest.mark.asyncio
async def test_get_content_digest_with_fallback_to_image_id(digest_verifier, mock_docker_client):
    """Test fallback to Image ID when RepoDigests fails."""
    call_count = 0

    def mock_get_side_effect(image_name):
        nonlocal call_count
        call_count += 1
        if call_count <= digest_verifier.max_retries:  # RepoDigests attempts
            return {
                'Id': 'sha256:image123',
                'RepoDigests': []  # No RepoDigests
            }
        else:  # Image ID attempt
            return {
                'Id': 'sha256:image123',
                'RepoDigests': []
            }

    mock_docker_client.docker.images.get = AsyncMock(side_effect=mock_get_side_effect)

    result = await digest_verifier.get_content_digest_with_fallback(
        mock_docker_client, "nginx", "latest"
    )

    assert result.success is True
    assert result.digest == "sha256:image123"
    assert result.method == "image_id"


@pytest.mark.asyncio
async def test_verify_digests_enhanced_match(digest_verifier, mock_docker_client):
    """Test enhanced digest verification with matching digests."""
    # Mock both source and target to return same digest
    mock_image_data = {
        'Id': 'sha256:image123',
        'RepoDigests': ['test@sha256:content123']
    }
    mock_docker_client.docker.images.get = AsyncMock(return_value=mock_image_data)

    result = await digest_verifier.verify_digests_enhanced(
        mock_docker_client,
        "source-repo", "latest",
        "target-repo", "latest"
    )

    assert result['verification_possible'] is True
    assert result['digests_match'] is True
    assert result['verification_quality'] == "high"
    assert result['source_digest'] == "sha256:content123"
    assert result['target_digest'] == "sha256:content123"


@pytest.mark.asyncio
async def test_verify_digests_enhanced_mismatch(digest_verifier, mock_docker_client):
    """Test enhanced digest verification with mismatched digests."""
    call_count = 0

    def mock_get_side_effect(image_name):
        nonlocal call_count
        call_count += 1
        if "source" in image_name:
            return {
                'Id': 'sha256:image123',
                'RepoDigests': ['source@sha256:content123']
            }
        else:
            return {
                'Id': 'sha256:image456',
                'RepoDigests': ['target@sha256:content456']
            }

    mock_docker_client.docker.images.get = AsyncMock(side_effect=mock_get_side_effect)

    result = await digest_verifier.verify_digests_enhanced(
        mock_docker_client,
        "source-repo", "latest",
        "target-repo", "latest"
    )

    assert result['verification_possible'] is True
    assert result['digests_match'] is False
    assert result['source_digest'] == "sha256:content123"
    assert result['target_digest'] == "sha256:content456"


@pytest.mark.asyncio
async def test_verify_digests_enhanced_unavailable(digest_verifier, mock_docker_client):
    """Test enhanced digest verification when digests unavailable."""
    # Mock both calls to fail
    mock_docker_client.docker.images.get = AsyncMock(
        side_effect=Exception("Image not found")
    )

    result = await digest_verifier.verify_digests_enhanced(
        mock_docker_client,
        "source-repo", "latest",
        "target-repo", "latest"
    )

    assert result['verification_possible'] is False
    assert result['digests_match'] is None
    assert result['source_digest'] is None
    assert result['target_digest'] is None
    assert len(result['warnings']) >= 2


@pytest.mark.asyncio
async def test_get_enhanced_digest_convenience_function(mock_docker_client):
    """Test the convenience function for backward compatibility."""
    mock_image_data = {
        'Id': 'sha256:image123',
        'RepoDigests': ['nginx@sha256:content123']
    }
    mock_docker_client.docker.images.get = AsyncMock(return_value=mock_image_data)

    # Mock cache to bypass caching for this test
    with patch('src.ecreshore.services.digest_verification.get_cache', return_value=None):
        digest = await get_enhanced_digest(mock_docker_client, "nginx", "latest")

    assert digest == "sha256:content123"


def test_digest_result_dataclass():
    """Test DigestResult dataclass functionality."""
    result = DigestResult(
        digest="sha256:abc123",
        method="repo_digests",
        registry="docker.io",
        success=True
    )

    assert result.digest == "sha256:abc123"
    assert result.method == "repo_digests"
    assert result.registry == "docker.io"
    assert result.success is True
    assert result.error is None