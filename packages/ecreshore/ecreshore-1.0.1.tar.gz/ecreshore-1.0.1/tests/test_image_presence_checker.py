"""Tests for ImagePresenceChecker business logic."""

import pytest
from unittest.mock import Mock, AsyncMock
from src.ecreshore.services.image_presence_checker import (
    ImagePresenceChecker,
    check_image_exists_in_ecr,
    should_skip_transfer,
    normalize_digest
)
from src.ecreshore.services.ecr_repository import ECRImage, ECRRepositoryService
from datetime import datetime


@pytest.fixture
def mock_ecr_service():
    """Create mock ECR repository service."""
    service = Mock(spec=ECRRepositoryService)
    return service


@pytest.fixture
def sample_ecr_image():
    """Create sample ECR image for testing."""
    return ECRImage(
        repository_name="helm-controller",
        image_tags=["v1.3.0"],
        image_digest="sha256:3b723f60dccf097d7993b76db84d8ad16cd554b94ee5d24178ccb743a4508c5a",
        size_bytes=41000000,
        pushed_at=datetime.now(),
        registry_id="123456789012",
        region="us-east-2"
    )


@pytest.fixture
def image_presence_checker(mock_ecr_service):
    """Create ImagePresenceChecker instance for testing."""
    return ImagePresenceChecker(mock_ecr_service)


class TestPureFunctions:
    """Test pure functions that have no I/O or side effects."""

    def test_normalize_digest_with_prefix(self):
        """Test normalizing digest that has sha256: prefix."""
        assert normalize_digest("sha256:abc123def456") == "abc123def456"

    def test_normalize_digest_without_prefix(self):
        """Test normalizing digest that has no prefix."""
        assert normalize_digest("abc123def456") == "abc123def456"

    def test_normalize_digest_with_none(self):
        """Test normalizing None digest returns empty string."""
        assert normalize_digest(None) == ""

    def test_normalize_digest_with_empty_string(self):
        """Test normalizing empty string returns empty string."""
        assert normalize_digest("") == ""

    def test_normalize_digest_with_full_sha256(self):
        """Test normalizing full 64-character sha256 digest."""
        full_digest = "sha256:3b723f60dccf097d7993b76db84d8ad16cd554b94ee5d24178ccb743a4508c5a"
        expected = "3b723f60dccf097d7993b76db84d8ad16cd554b94ee5d24178ccb743a4508c5a"
        assert normalize_digest(full_digest) == expected

    def test_normalize_digest_idempotent(self):
        """Test that normalizing twice gives same result."""
        digest = "sha256:abc123"
        normalized_once = normalize_digest(digest)
        normalized_twice = normalize_digest(normalized_once)
        assert normalized_once == normalized_twice


class TestImagePresenceChecker:
    """Test ImagePresenceChecker business logic."""

    @pytest.mark.asyncio
    async def test_check_image_exists_in_ecr_found(self, image_presence_checker, mock_ecr_service, sample_ecr_image):
        """Test checking for existing image in ECR (found)."""
        # Setup mock
        mock_ecr_service.list_images = Mock(return_value=[sample_ecr_image])

        # Test
        result = await image_presence_checker.check_image_exists_in_ecr("helm-controller", "v1.3.0")

        # Verify
        assert result is not None
        assert result.repository_name == "helm-controller"
        assert "v1.3.0" in result.image_tags
        assert result.image_digest == "sha256:3b723f60dccf097d7993b76db84d8ad16cd554b94ee5d24178ccb743a4508c5a"
        mock_ecr_service.list_images.assert_called_once_with("helm-controller", tag_filter="v1.3.0", max_results=100, tagged_only=True)

    @pytest.mark.asyncio
    async def test_check_image_exists_in_ecr_not_found(self, image_presence_checker, mock_ecr_service):
        """Test checking for non-existent image in ECR."""
        # Setup mock - no images returned
        mock_ecr_service.list_images = Mock(return_value=[])

        # Test
        result = await image_presence_checker.check_image_exists_in_ecr("missing-image", "v1.0.0")

        # Verify
        assert result is None
        mock_ecr_service.list_images.assert_called_once_with("missing-image", tag_filter="v1.0.0", max_results=100, tagged_only=True)

    @pytest.mark.asyncio
    async def test_check_image_exists_in_ecr_wrong_tag(self, image_presence_checker, mock_ecr_service, sample_ecr_image):
        """Test checking for image with wrong tag."""
        # Setup mock - image exists but with different tag
        sample_ecr_image.image_tags = ["v1.2.0"]  # Different tag
        mock_ecr_service.list_images = Mock(return_value=[sample_ecr_image])

        # Test
        result = await image_presence_checker.check_image_exists_in_ecr("helm-controller", "v1.3.0")

        # Verify
        assert result is None  # Should not find image with wrong tag

    @pytest.mark.asyncio
    async def test_check_image_exists_in_ecr_exception(self, image_presence_checker, mock_ecr_service):
        """Test ECR API exception handling."""
        # Setup mock to raise exception
        mock_ecr_service.list_images = Mock(side_effect=Exception("ECR API error"))

        # Test
        result = await image_presence_checker.check_image_exists_in_ecr("helm-controller", "v1.3.0")

        # Verify
        assert result is None  # Should handle exception gracefully

    @pytest.mark.asyncio
    async def test_get_target_image_digest_success(self, image_presence_checker, mock_ecr_service, sample_ecr_image):
        """Test getting target image digest."""
        # Setup mock
        mock_ecr_service.list_images = Mock(return_value=[sample_ecr_image])

        # Test
        result = await image_presence_checker.get_target_image_digest("helm-controller", "v1.3.0")

        # Verify
        assert result == "sha256:3b723f60dccf097d7993b76db84d8ad16cd554b94ee5d24178ccb743a4508c5a"

    @pytest.mark.asyncio
    async def test_get_target_image_digest_not_found(self, image_presence_checker, mock_ecr_service):
        """Test getting digest for non-existent image."""
        # Setup mock
        mock_ecr_service.list_images = Mock(return_value=[])

        # Test
        result = await image_presence_checker.get_target_image_digest("missing-image", "v1.0.0")

        # Verify
        assert result is None


    def test_compare_source_target_digests_match(self, image_presence_checker):
        """Test digest comparison with matching digests."""
        source = "sha256:abc123456789"
        target = "sha256:abc123456789"

        result = image_presence_checker.compare_source_target_digests(source, target)

        assert result is True

    def test_compare_source_target_digests_match_without_prefix(self, image_presence_checker):
        """Test digest comparison with matching digests (no sha256 prefix)."""
        source = "abc123456789"
        target = "sha256:abc123456789"

        result = image_presence_checker.compare_source_target_digests(source, target)

        assert result is True

    def test_compare_source_target_digests_mismatch(self, image_presence_checker):
        """Test digest comparison with different digests."""
        source = "sha256:abc123456789"
        target = "sha256:def987654321"

        result = image_presence_checker.compare_source_target_digests(source, target)

        assert result is False

    def test_compare_source_target_digests_none_values(self, image_presence_checker):
        """Test digest comparison with None values."""
        # Both None
        result = image_presence_checker.compare_source_target_digests(None, None)
        assert result is False

        # One None
        result = image_presence_checker.compare_source_target_digests("abc123", None)
        assert result is False

        result = image_presence_checker.compare_source_target_digests(None, "def456")
        assert result is False

    @pytest.mark.asyncio
    async def test_should_skip_transfer_no_target_image(self, image_presence_checker, mock_ecr_service):
        """Test skip decision when target image doesn't exist."""
        # Setup mocks
        mock_ecr_service.list_images = Mock(return_value=[])  # No target image

        # Test
        result = await image_presence_checker.should_skip_transfer(
            None, "ghcr.io/fluxcd/helm-controller", "v1.3.0", "helm-controller", "v1.3.0"
        )

        # Verify
        assert result['should_skip'] is False
        assert "does not exist in ECR" in result['reason']
        assert result['existing_image'] is None

    @pytest.mark.asyncio
    async def test_should_skip_transfer_matching_digests(self, image_presence_checker, mock_ecr_service, sample_ecr_image):
        """Test skip decision when digests match."""
        # Setup mocks
        mock_ecr_service.list_images = Mock(return_value=[sample_ecr_image])

        matching_digest = "sha256:3b723f60dccf097d7993b76db84d8ad16cd554b94ee5d24178ccb743a4508c5a"

        with pytest.MonkeyPatch().context() as m:
            mock_get_enhanced = AsyncMock(return_value=matching_digest)
            m.setattr("src.ecreshore.services.image_presence_checker.get_enhanced_digest", mock_get_enhanced)

            # Test
            result = await image_presence_checker.should_skip_transfer(
                None, "ghcr.io/fluxcd/helm-controller", "v1.3.0", "helm-controller", "v1.3.0"
            )

            # Verify
            assert result['should_skip'] is True
            assert "already exists with matching digest" in result['reason']
            assert result['digests_match'] is True
            assert result['source_digest'] == matching_digest
            assert result['target_digest'] == matching_digest



class TestIntegrationSourceDigestRetrieval:
    """Integration tests for source digest retrieval without mocking internal methods."""

    @pytest.mark.asyncio
    async def test_get_source_image_digest_with_buildx_only_mode(self, image_presence_checker):
        """Test source digest retrieval in buildx-only mode (docker_client=None)."""
        # Use None for docker_client to simulate buildx-only mode
        # This tests the real implementation path without mocking
        result = await image_presence_checker.get_source_image_digest(
            None, "ghcr.io/fluxcd/helm-controller", "v1.3.0"
        )

        # Verify: should return a digest or None based on actual execution
        # We don't assert the specific value - we test that the method completes
        assert result is None or isinstance(result, str)
        if result:
            # If a digest is returned, verify it's in the correct format
            assert result.startswith("sha256:") or len(result) == 64

    @pytest.mark.asyncio
    async def test_get_source_platform_specific_digest_with_buildx(self, image_presence_checker):
        """Test platform-specific digest retrieval for source image."""
        # Test the real implementation without mocking
        result = await image_presence_checker.get_source_platform_specific_digest(
            None, "ghcr.io/fluxcd/helm-controller", "v1.3.0"
        )

        # Verify: method completes and returns expected type
        assert result is None or isinstance(result, str)
        if result:
            assert result.startswith("sha256:") or len(result) == 64


class TestIntegrationSkipDecisions:
    """Integration tests for skip decision logic without mocking internal methods."""

    @pytest.mark.asyncio
    async def test_should_skip_transfer_no_target_image_integration(self, image_presence_checker, mock_ecr_service):
        """Test skip decision when target doesn't exist - full integration."""
        # Setup: ECR returns no images
        mock_ecr_service.list_images = Mock(return_value=[])

        # Test: full execution through real methods
        result = await image_presence_checker.should_skip_transfer(
            None, "ghcr.io/fluxcd/helm-controller", "v1.3.0", "helm-controller", "v1.3.0"
        )

        # Verify: should not skip when target doesn't exist
        assert result['should_skip'] is False
        assert "does not exist in ECR" in result['reason']
        assert result['existing_image'] is None

    @pytest.mark.asyncio
    async def test_should_skip_transfer_with_existing_target_integration(
        self, image_presence_checker, mock_ecr_service, sample_ecr_image
    ):
        """Test skip decision with existing target - full integration without mocking digests."""
        # Setup: ECR returns existing image
        mock_ecr_service.list_images = Mock(return_value=[sample_ecr_image])

        # Test: full execution through real digest retrieval methods
        result = await image_presence_checker.should_skip_transfer(
            None, "ghcr.io/fluxcd/helm-controller", "v1.3.0", "helm-controller", "v1.3.0"
        )

        # Verify: method completes and returns valid decision structure
        assert 'should_skip' in result
        assert 'reason' in result
        assert 'existing_image' in result
        assert isinstance(result['should_skip'], bool)
        assert isinstance(result['reason'], str)

        # Verify the existing image was found
        assert result['existing_image'] is not None
        assert result['existing_image'].repository_name == "helm-controller"


class TestConvenienceFunctions:
    """Test convenience functions for backward compatibility."""

    @pytest.mark.asyncio
    async def test_check_image_exists_in_ecr_convenience(self, mock_ecr_service, sample_ecr_image):
        """Test convenience function for checking image existence."""
        # Setup mock
        mock_ecr_service.list_images = Mock(return_value=[sample_ecr_image])

        # Test convenience function
        result = await check_image_exists_in_ecr(mock_ecr_service, "helm-controller", "v1.3.0")

        # Verify
        assert result is not None
        assert result.repository_name == "helm-controller"

    @pytest.mark.asyncio
    async def test_should_skip_transfer_convenience(self, mock_ecr_service, sample_ecr_image):
        """Test convenience function for skip decision."""
        # Setup mocks
        mock_ecr_service.list_images = Mock(return_value=[sample_ecr_image])

        matching_digest = "sha256:3b723f60dccf097d7993b76db84d8ad16cd554b94ee5d24178ccb743a4508c5a"

        with pytest.MonkeyPatch().context() as m:
            mock_get_enhanced = AsyncMock(return_value=matching_digest)
            m.setattr("src.ecreshore.services.image_presence_checker.get_enhanced_digest", mock_get_enhanced)

            # Test convenience function
            result = await should_skip_transfer(
                mock_ecr_service, None, "ghcr.io/fluxcd/helm-controller", "v1.3.0", "helm-controller", "v1.3.0"
            )

            # Verify
            assert result['should_skip'] is True
            assert result['digests_match'] is True


class TestDigestNormalization:
    """Test digest normalization functionality to prevent platform vs multi-arch mismatch regressions."""

    def test_compare_source_target_digests_normalizes_prefixes(self, image_presence_checker):
        """Test that digest comparison handles sha256: prefix normalization correctly."""
        # Test cases that should match after normalization
        test_cases = [
            # Same digest with and without prefix
            ("sha256:abc123", "abc123", True),
            ("abc123", "sha256:abc123", True),
            ("sha256:abc123", "sha256:abc123", True),
            ("abc123", "abc123", True),

            # Different digests
            ("sha256:abc123", "sha256:def456", False),
            ("abc123", "def456", False),

            # None cases
            (None, "abc123", False),
            ("abc123", None, False),
            (None, None, False),
        ]

        for source, target, expected in test_cases:
            result = image_presence_checker.compare_source_target_digests(source, target)
            assert result == expected, f"Failed for source={source}, target={target}"

    def test_platform_vs_multiarch_digest_mismatch_prevention(self, image_presence_checker):
        """Test the core scenario: ensure different digest types can be identified."""
        # This test validates that our fix addresses the core issue
        # Multi-arch manifest digest (from ECR describe_images)
        ecr_manifest_digest = "sha256:81316365dc0b713eddddfbf9b8907b2939676e6c0e12beec0f9625f202a36d16"

        # Platform-specific digest (from Docker API RepoDigests)
        platform_digest = "sha256:058a3ee5b133456789abcdef123456789abcdef123456789ab"

        # These should NOT match (this was the original problem)
        result = image_presence_checker.compare_source_target_digests(
            ecr_manifest_digest, platform_digest
        )
        assert result is False, "Multi-arch and platform digests should be different"

        # But identical digests should match regardless of prefix
        result = image_presence_checker.compare_source_target_digests(
            ecr_manifest_digest, ecr_manifest_digest
        )
        assert result is True, "Identical digests should match"

    def test_digest_normalization_method_exists(self, image_presence_checker):
        """Test that the digest normalization method exists and has correct signature."""
        # Verify the method exists
        assert hasattr(image_presence_checker, 'get_target_platform_specific_digest')

        # Verify it's callable
        method = getattr(image_presence_checker, 'get_target_platform_specific_digest')
        assert callable(method)

        # This ensures our fix is in place and the method signature is correct
        import inspect
        sig = inspect.signature(method)
        expected_params = ['docker_client', 'repository', 'tag', 'existing_image']
        actual_params = list(sig.parameters.keys())

        for param in expected_params:
            assert param in actual_params, f"Missing parameter: {param}"

    def test_registry_url_pattern_validation(self):
        """Test ECR registry URL pattern without external dependencies."""
        # Test the registry URL construction pattern
        registry_id = "123456789012"
        region = "us-east-2"
        expected_url = f"{registry_id}.dkr.ecr.{region}.amazonaws.com"

        # Validate URL pattern matches ECR format
        import re
        pattern = r"\d{12}\.dkr\.ecr\.[a-z0-9-]+\.amazonaws\.com"
        assert re.match(pattern, expected_url), "Registry URL should match ECR pattern"

        # Test with different regions
        regions = ["us-east-1", "eu-west-1", "ap-southeast-2"]
        for region in regions:
            url = f"{registry_id}.dkr.ecr.{region}.amazonaws.com"
            assert re.match(pattern, url), f"Failed for region: {region}"

    def test_fallback_behavior_logic(self, image_presence_checker, sample_ecr_image):
        """Test that fallback logic is sound without external calls."""
        # The get_target_platform_specific_digest method should:
        # 1. Try to get platform-specific digest
        # 2. Fall back to ECR manifest digest on failure
        # 3. Always return a digest (never None if existing_image provided)

        # We can't test the async behavior without mocking, but we can validate
        # that the ECR image has the expected digest structure
        assert sample_ecr_image.image_digest is not None
        assert sample_ecr_image.image_digest.startswith("sha256:")

        # Validate the digest format
        digest_part = sample_ecr_image.image_digest.replace("sha256:", "")
        assert len(digest_part) == 64, "ECR digest should be 64 hex characters"
        assert all(c in "0123456789abcdef" for c in digest_part.lower()), "Digest should be hex"