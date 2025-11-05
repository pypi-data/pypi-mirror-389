"""Integration tests for skip-if-present functionality using real digest retrieval.

Following the testing philosophy from doc/claude-test-brain.xml:
- Zero mocks for services we own (ImagePresenceChecker, ECRRepositoryService)
- Real digest retrieval using actual Docker/buildx calls
- Tests actual behavior with real ghcr.io/fluxcd/helm-controller:v1.3.0 image

Requirements:
- Docker or buildx must be available
- Internet connectivity to pull from ghcr.io
- Tests may be slower (1-5s) due to real network calls
"""

import pytest
import pytest_asyncio
from typing import List, Optional
from datetime import datetime
from src.ecreshore.services.image_presence_checker import ImagePresenceChecker
from src.ecreshore.services.ecr_repository import ECRRepositoryService, ECRImage
from src.ecreshore.services.cache_manager import reset_caches


@pytest_asyncio.fixture(autouse=True, scope="function")
async def reset_cache(monkeypatch):
    """Reset cache state before and after each test.

    This is critical for test isolation because:
    1. get_enhanced_digest() caches source image digests (with hybrid disk+memory backend)
    2. get_target_platform_specific_digest() caches ECR target digests
    3. Tests use fake ECR services with different digests
    4. Without clearing, tests see cached values from previous tests

    We disable caching entirely for these tests to ensure isolation.
    """
    import os
    from src.ecreshore.services.cache_manager import reset_caches
    from src.ecreshore.cache_config import CacheConfig

    # Disable caching for tests to ensure isolation
    monkeypatch.setenv("ECRESHORE_CACHE_ENABLED", "false")

    # Force cache config to reload
    CacheConfig._enabled = None

    # Reset cache instances
    reset_caches()

    yield

    # Reset cache instances after test
    reset_caches()

    # Reset cache config
    CacheConfig._enabled = None


# ============================================================================
# Fake Service Implementation (better than mocks for owned services)
# ============================================================================

class FakeECRRepositoryService:
    """Fake ECR service for testing - better than mocks per claude-test-brain.xml.

    Benefits over Mock:
    - Reusable across many tests
    - Type-safe with IDE autocomplete
    - Self-documenting - implements real interface
    - Less brittle to refactoring
    """

    def __init__(self, images: Optional[List[ECRImage]] = None):
        """Initialize fake ECR service.

        Args:
            images: Pre-configured ECR images to return from list_images
        """
        self.images = images or []
        self.registry_id = "123456789012"
        self.region_name = "us-east-2"

        # Create minimal ecr_auth object
        class FakeECRAuth:
            registry_id = "123456789012"

        self.ecr_auth = FakeECRAuth()

        # Track calls for verification
        self.list_images_calls = []

    def list_images(
        self,
        repository: str,
        tag_filter: Optional[str] = None,
        max_results: int = 100,
        tagged_only: bool = False
    ) -> List[ECRImage]:
        """Fake implementation of list_images."""
        self.list_images_calls.append({
            "repository": repository,
            "tag_filter": tag_filter,
            "max_results": max_results,
            "tagged_only": tagged_only
        })

        # Filter images by repository and tag
        # Note: tagged_only filtering not needed for our test data (all images have tags)
        return [
            img for img in self.images
            if img.repository_name == repository and
            (not tag_filter or tag_filter in img.image_tags)
        ]


# ============================================================================
# Pytest Fixtures
# ============================================================================

@pytest_asyncio.fixture
async def real_helm_controller_digest():
    """Async fixture providing the real digest for ghcr.io/fluxcd/helm-controller:v1.3.0.

    This fixture performs a real network call to retrieve the digest.
    Caching at module scope would reduce network calls but we keep it
    at function scope for test isolation.

    Note: Uses @pytest_asyncio.fixture for async fixture support.
    The fixture will be awaited before being injected into test functions.
    """
    from src.ecreshore.services.digest_verification import get_enhanced_digest

    digest = await get_enhanced_digest(
        None,  # buildx-only mode
        "ghcr.io/fluxcd/helm-controller",
        "v1.3.0"
    )

    assert digest is not None, "Failed to retrieve real source digest - is Docker/buildx available?"
    assert digest.startswith("sha256:"), f"Invalid digest format: {digest}"

    return digest


@pytest.fixture
def create_ecr_image():
    """Factory fixture for creating ECRImage instances with sensible defaults.

    Returns a function that creates ECRImage objects with default values
    that can be overridden.
    """
    def _create(
        digest: str,
        tag: str = "v1.3.0",
        repository: str = "helm-controller",
        **overrides
    ) -> ECRImage:
        defaults = {
            "repository_name": repository,
            "image_tags": [tag],
            "image_digest": digest,
            "size_bytes": 41000000,
            "pushed_at": datetime.now(),
            "registry_id": "123456789012",
            "region": "us-east-2"
        }
        return ECRImage(**{**defaults, **overrides})

    return _create


@pytest.fixture
def fake_ecr_service():
    """Fixture providing a base FakeECRRepositoryService instance."""
    return FakeECRRepositoryService()



# ============================================================================
# Integration Tests
# ============================================================================

class TestSkipIfPresentIntegration:
    """Integration tests using real digest retrieval against ghcr.io/fluxcd/helm-controller:v1.3.0"""

    @pytest.mark.asyncio
    async def test_skip_decision_with_matching_digest(
        self,
        real_helm_controller_digest,
        create_ecr_image,
        fake_ecr_service
    ):
        """Test skip decision when target has matching digest.

        This integration test:
        - Uses fake ECR service (better than mocks per test-brain.xml)
        - Calls real Docker/buildx to get source image digest
        - Tests the complete skip decision flow
        """
        # Create ECR image that matches the real source digest
        existing_image = create_ecr_image(digest=real_helm_controller_digest)
        fake_ecr_service.images = [existing_image]

        # Initialize image presence checker with our fake ECR service
        presence_checker = ImagePresenceChecker(fake_ecr_service)

        # Test skip decision with REAL digest retrieval
        result = await presence_checker.should_skip_transfer(
            docker_client=None,  # Use buildx-only mode
            source_image="ghcr.io/fluxcd/helm-controller",
            source_tag="v1.3.0",
            target_repository="helm-controller",
            target_tag="v1.3.0"
        )

        # Verify skip decision
        assert result['should_skip'] is True, f"Expected skip but got proceed. Reason: {result['reason']}"
        assert "already exists" in result['reason'].lower(), f"Unexpected reason: {result['reason']}"
        assert result['digests_match'] is True
        assert result['source_digest'] == real_helm_controller_digest
        assert result['target_digest'] == real_helm_controller_digest
        assert result['existing_image'].repository_name == "helm-controller"

        # Verify ECR service was called correctly using fake's tracking
        assert len(fake_ecr_service.list_images_calls) == 1
        call = fake_ecr_service.list_images_calls[0]
        assert call["repository"] == "helm-controller"
        assert call["tag_filter"] == "v1.3.0"
        assert call["max_results"] == 100
        assert call["tagged_only"] is True

    @pytest.mark.asyncio
    async def test_no_skip_decision_with_different_digest(
        self,
        real_helm_controller_digest,
        create_ecr_image,
        fake_ecr_service
    ):
        """Test no skip decision when digests differ.

        Uses real source digest but simulates different target digest.
        """
        # Create ECR image with DIFFERENT digest
        different_digest = "sha256:0000000000000000000000000000000000000000000000000000000000000000"
        existing_image = create_ecr_image(digest=different_digest)
        fake_ecr_service.images = [existing_image]

        presence_checker = ImagePresenceChecker(fake_ecr_service)

        # Test skip decision with REAL source digest vs different target
        result = await presence_checker.should_skip_transfer(
            None,  # docker_client
            "ghcr.io/fluxcd/helm-controller",
            "v1.3.0",
            "helm-controller",
            "v1.3.0"
        )

        # Verify no skip decision
        assert result['should_skip'] is False, f"Expected proceed but got skip. Reason: {result['reason']}"
        assert "different content" in result['reason'].lower(), f"Unexpected reason: {result['reason']}"
        assert result['digests_match'] is False
        assert result['source_digest'] == real_helm_controller_digest
        assert result['target_digest'] == different_digest

    @pytest.mark.asyncio
    async def test_no_skip_decision_no_target_image(self, fake_ecr_service):
        """Test no skip decision when target image doesn't exist.

        Uses fake ECR service with no images configured.
        """
        # Fake service has no images by default
        presence_checker = ImagePresenceChecker(fake_ecr_service)

        # Test skip decision
        result = await presence_checker.should_skip_transfer(
            None,  # docker_client
            "ghcr.io/fluxcd/helm-controller",
            "v1.3.0",
            "helm-controller",
            "v1.3.0"
        )

        # Verify no skip decision
        assert result['should_skip'] is False
        assert "does not exist in ECR" in result['reason']
        assert result['existing_image'] is None
        assert result['digests_match'] is None

    @pytest.mark.asyncio
    async def test_repository_name_inference_consistency(self):
        """Test that repository name inference is consistent with skip-if-present logic."""
        from src.ecreshore.services.image_parser import infer_target_repository_name

        # Test the same image URL used in skip-if-present tests
        source_image = "ghcr.io/fluxcd/helm-controller"

        # Get inferred repository name
        inferred_name = infer_target_repository_name(source_image)

        # Verify consistency
        assert inferred_name == "helm-controller"

        # This ensures our skip-if-present logic uses the same repository naming
        # convention as the CLI parsing logic


# ============================================================================
# Unit Tests - Pure Business Logic
# ============================================================================

class TestDigestComparison:
    """Unit tests for digest comparison logic (no I/O, <0.1s per test)"""

    @pytest.mark.parametrize("source_digest,target_digest,expected,test_id", [
        ("sha256:abc123", "sha256:abc123", True, "identical_digests"),
        ("sha256:abc123", "sha256:def456", False, "different_digests"),
        ("abc123", "sha256:abc123", True, "digest_normalization_source"),
        ("sha256:abc123", "abc123", True, "digest_normalization_target"),
        (None, "sha256:abc123", False, "none_source"),
        ("sha256:abc123", None, False, "none_target"),
        (None, None, False, "both_none"),
        ("", "sha256:abc123", False, "empty_source"),
        ("sha256:abc123", "", False, "empty_target"),
    ], ids=lambda x: x if isinstance(x, str) and not x.startswith("sha256:") else None)
    def test_digest_comparison_logic(self, fake_ecr_service, source_digest, target_digest, expected, test_id):
        """Test digest comparison logic (pure business logic, no I/O).

        Parameterized test covering all digest comparison cases including:
        - Identical digests
        - Different digests
        - Digest normalization (with/without sha256: prefix)
        - None and empty string handling
        """
        checker = ImagePresenceChecker(fake_ecr_service)
        result = checker.compare_source_target_digests(source_digest, target_digest)
        assert result is expected, f"Failed for test case: {test_id}"

    def test_skip_if_present_cli_integration_simulation(self):
        """Test CLI integration points for skip-if-present functionality."""
        from src.ecreshore.services.transfer_request_builder import TransferRequestBuilder

        # Test default behavior (skip-if-present enabled)
        request_default = TransferRequestBuilder.for_cli_copy(
            source_image="ghcr.io/fluxcd/helm-controller",
            target_repository="helm-controller",
            source_tag="v1.3.0",
            target_tag="v1.3.0"
        )

        assert request_default.skip_if_present is True

        # Test force flag behavior (skip-if-present disabled)
        request_forced = TransferRequestBuilder.for_cli_copy(
            source_image="ghcr.io/fluxcd/helm-controller",
            target_repository="helm-controller",
            source_tag="v1.3.0",
            target_tag="v1.3.0",
            force=True
        )

        assert request_forced.skip_if_present is False

        # Verify all other parameters are preserved
        assert request_default.source_image == request_forced.source_image
        assert request_default.source_tag == request_forced.source_tag
        assert request_default.target_repository == request_forced.target_repository
        assert request_default.target_tag == request_forced.target_tag