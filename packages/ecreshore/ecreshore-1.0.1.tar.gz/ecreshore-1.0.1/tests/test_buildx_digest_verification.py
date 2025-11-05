"""Tests for buildx digest verification business logic."""

import pytest
from unittest.mock import Mock, AsyncMock
from src.ecreshore.services.digest_verification import EnhancedDigestVerification, DigestResult, get_enhanced_digest


def test_digest_result_creation():
    """Test DigestResult creation and validation."""
    # Successful result
    success_result = DigestResult(
        digest="sha256:3b723f60dccf097d7993b76db84d8ad16cd554b94ee5d24178ccb743a4508c5a",
        method="buildx_inspect",
        registry="ghcr.io",
        success=True
    )

    assert success_result.success is True
    assert success_result.digest.startswith("sha256:")
    assert success_result.method == "buildx_inspect"
    assert success_result.error is None

    # Failed result
    failed_result = DigestResult(
        digest=None,
        method="buildx_inspect",
        error="Registry authentication failed",
        success=False
    )

    assert failed_result.success is False
    assert failed_result.digest is None
    assert "authentication failed" in failed_result.error


@pytest.mark.asyncio
async def test_enhanced_digest_verification_fallback_chain():
    """Test that enhanced digest verification follows correct fallback priority."""
    verifier = EnhancedDigestVerification(max_retries=1, retry_delay=0.01)

    # Mock Docker client that returns no RepoDigests and fails Image ID
    mock_docker_client = Mock()
    mock_docker_client.docker.images.get = AsyncMock(return_value={
        'Id': 'invalid-format',  # This will cause image_id method to fail
        'RepoDigests': []  # This will cause repo_digests method to fail
    })

    # Mock buildx inspect method to succeed
    async def mock_buildx_success(repository, tag):
        return DigestResult(
            digest="sha256:buildx123456789",
            method="buildx_inspect",
            registry="ghcr.io",
            success=True
        )

    verifier._get_digest_from_buildx_inspect = mock_buildx_success

    # Test the fallback chain
    result = await verifier.get_content_digest_with_fallback(
        mock_docker_client, "ghcr.io/fluxcd/helm-controller", "v1.3.0"
    )

    assert result.success is True
    assert result.method == "buildx_inspect"
    assert result.digest == "sha256:buildx123456789"


@pytest.mark.asyncio
async def test_digest_verification_with_matching_digests():
    """Test digest verification when source and target digests match."""
    verifier = EnhancedDigestVerification()

    # Mock both digest retrievals to return matching digests
    matching_digest = "sha256:3b723f60dccf097d7993b76db84d8ad16cd554b94ee5d24178ccb743a4508c5a"

    async def mock_get_digest_success(client, repository, tag):
        return DigestResult(
            digest=matching_digest,
            method="buildx_inspect",
            registry="ghcr.io" if "ghcr.io" in repository else "ecr",
            success=True
        )

    verifier.get_content_digest_with_fallback = mock_get_digest_success

    result = await verifier.verify_digests_enhanced(
        None,  # No Docker client needed for buildx mode
        "ghcr.io/fluxcd/helm-controller", "v1.3.0",
        "572430232445.dkr.ecr.us-east-2.amazonaws.com/helm-controller", "v1.3.0"
    )

    assert result['verification_possible'] is True
    assert result['digests_match'] is True
    assert result['source_digest'] == matching_digest
    assert result['target_digest'] == matching_digest
    assert result['verification_quality'] == "high"  # Both using buildx_inspect (high quality method)
    assert len(result['warnings']) == 0


@pytest.mark.asyncio
async def test_get_enhanced_digest_buildx_mode(monkeypatch):
    """Test the convenience function in buildx-only mode."""
    # Mock the verifier's buildx inspect method
    expected_digest = "sha256:3b723f60dccf097d7993b76db84d8ad16cd554b94ee5d24178ccb743a4508c5a"

    # Create a mock verifier instance
    mock_verifier = Mock()
    mock_verifier._get_digest_from_buildx_inspect = AsyncMock(return_value=DigestResult(
        digest=expected_digest,
        method="buildx_inspect",
        success=True
    ))

    # Patch both the verifier creation and the cache (use pytest fixture for proper cleanup)
    monkeypatch.setattr("src.ecreshore.services.digest_verification.EnhancedDigestVerification", lambda: mock_verifier)
    monkeypatch.setattr("src.ecreshore.services.digest_verification.get_cache", lambda _: None)  # Disable cache

    # Test with docker_client=None (buildx-only mode)
    digest = await get_enhanced_digest(None, "ghcr.io/fluxcd/helm-controller", "v1.3.0")

    assert digest == expected_digest
    mock_verifier._get_digest_from_buildx_inspect.assert_called_once_with("ghcr.io/fluxcd/helm-controller", "v1.3.0")


@pytest.mark.asyncio
async def test_digest_verification_with_mismatch():
    """Test digest verification when source and target digests don't match."""
    verifier = EnhancedDigestVerification()

    # Mock digest retrievals to return different digests
    source_digest = "sha256:3b723f60dccf097d7993b76db84d8ad16cd554b94ee5d24178ccb743a4508c5a"
    target_digest = "sha256:different567890abcdef1234567890abcdef1234567890abcdef1234567890"

    call_count = 0

    async def mock_get_digest_mismatch(client, repository, tag):
        nonlocal call_count
        call_count += 1
        if call_count == 1:  # First call (source)
            return DigestResult(digest=source_digest, method="buildx_inspect", success=True)
        else:  # Second call (target)
            return DigestResult(digest=target_digest, method="buildx_inspect", success=True)

    verifier.get_content_digest_with_fallback = mock_get_digest_mismatch

    result = await verifier.verify_digests_enhanced(
        None,
        "ghcr.io/fluxcd/helm-controller", "v1.3.0",
        "572430232445.dkr.ecr.us-east-2.amazonaws.com/helm-controller", "v1.3.0"
    )

    assert result['verification_possible'] is True
    assert result['digests_match'] is False
    assert result['source_digest'] == source_digest
    assert result['target_digest'] == target_digest
    assert result['verification_quality'] == "high"  # Both using buildx_inspect (high quality method)


def test_registry_extraction_from_repository():
    """Test registry extraction helper function."""

    verifier = EnhancedDigestVerification()

    # Test various repository formats
    assert verifier._extract_registry_from_repository("ghcr.io/fluxcd/helm-controller") == "ghcr.io"
    assert verifier._extract_registry_from_repository("572430232445.dkr.ecr.us-east-2.amazonaws.com/helm-controller") == "572430232445.dkr.ecr.us-east-2.amazonaws.com"
    assert verifier._extract_registry_from_repository("nginx") == "docker.io"
    assert verifier._extract_registry_from_repository("library/nginx") == "docker.io"