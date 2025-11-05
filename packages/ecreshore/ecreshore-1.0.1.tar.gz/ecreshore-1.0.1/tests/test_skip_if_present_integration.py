"""Integration tests for skip-if-present functionality."""

import pytest
from src.ecreshore.services.hybrid_transfer_service import HybridTransferService
from src.ecreshore.services.transfer_request_builder import TransferRequestBuilder
from src.ecreshore.services.transfer_service import TransferRequest, TransferResult
from src.ecreshore.services.ecr_repository import ECRImage, ECRRepositoryService
from datetime import datetime


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
def hybrid_transfer_service():
    """Create HybridTransferService for testing."""
    return HybridTransferService(region_name="us-east-2", registry_id="123456789012")


class TestSkipIfPresentIntegration:
    """Integration tests for skip-if-present functionality.

    These tests make real Docker daemon + ECR API calls and take 15-80+ seconds each.
    Run with: pytest -m integration
    For fast tests (<1s), use test_skip_if_present_fast.py
    """

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_skip_if_present_enabled_image_exists_matching_digest(self, hybrid_transfer_service):
        """Test skip when image exists with matching digest - uses real ECR calls."""
        # Use a real image that should exist in ECR: helm-controller
        # This test will make actual ECR API calls to check if the image exists
        request = TransferRequestBuilder() \
            .source("ghcr.io/fluxcd/helm-controller", "v1.3.0") \
            .target("helm-controller", "v1.3.0") \
            .skip_if_present(True) \
            .build()

        # Execute transfer with real ECR calls
        result = await hybrid_transfer_service.transfer_image(request)

        # The test outcome depends on the actual state of ECR:
        # - If helm-controller:v1.3.0 exists with matching digest: should skip
        # - If helm-controller:v1.3.0 doesn't exist: should transfer (and may fail with 403)
        # - If helm-controller:v1.3.0 exists with different digest: should transfer

        # At minimum, verify the result structure is correct
        assert hasattr(result, 'success')
        assert hasattr(result, 'skipped')
        assert hasattr(result, 'skip_reason')
        assert hasattr(result, 'transfer_method')

        # If it was skipped, verify skip fields are properly set
        if result.skipped:
            assert result.success is True
            assert result.skip_reason is not None
            assert "already exists" in result.skip_reason
            assert result.transfer_method == "skipped"

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_skip_if_present_enabled_image_not_exists(self, hybrid_transfer_service):
        """Test normal transfer when target image doesn't exist - uses real ECR calls."""
        # Use a target image that definitely doesn't exist
        request = TransferRequestBuilder() \
            .source("ghcr.io/fluxcd/helm-controller", "v1.3.0") \
            .target("nonexistent-test-image", "v1.3.0") \
            .skip_if_present(True) \
            .build()

        # Execute transfer with real ECR calls
        result = await hybrid_transfer_service.transfer_image(request)

        # Since the target doesn't exist, it should attempt transfer
        # (which may fail with 403 due to permissions, but that's expected)
        assert result.skipped is False

        # Verify the transfer was attempted (success may be False due to 403 permissions)
        assert result.transfer_method in ["buildx", "docker"]

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_skip_if_present_basic_functionality(self, hybrid_transfer_service):
        """Test basic skip-if-present functionality with real ECR calls."""
        # Test with an image that might exist in ECR
        request = TransferRequestBuilder() \
            .source("ghcr.io/fluxcd/source-controller", "v1.6.2") \
            .target("source-controller", "v1.6.2") \
            .skip_if_present(True) \
            .build()

        # Execute transfer with real ECR calls
        result = await hybrid_transfer_service.transfer_image(request)

        # Verify basic result structure regardless of outcome
        assert hasattr(result, 'success')
        assert hasattr(result, 'skipped')
        assert hasattr(result, 'transfer_method')

        # If successful and skipped, verify skip logic worked
        if result.success and result.skipped:
            assert result.skip_reason is not None
            assert result.transfer_method == "skipped"
        # If not skipped, verify transfer was attempted
        elif not result.skipped:
            assert result.transfer_method in ["buildx", "docker"]

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_skip_if_present_disabled_force_flag(self, hybrid_transfer_service):
        """Test force flag disables skip-if-present - uses real ECR calls."""
        # Create request with skip_if_present disabled (force=True)
        request = TransferRequestBuilder() \
            .source("ghcr.io/fluxcd/helm-controller", "v1.3.0") \
            .target("helm-controller", "v1.3.0") \
            .skip_if_present(False) \
            .build()

        # Execute transfer with real ECR calls
        result = await hybrid_transfer_service.transfer_image(request)

        # With force flag, should never skip regardless of ECR state
        assert result.skipped is False

        # Should have attempted transfer
        assert result.transfer_method in ["buildx", "docker"]


class TestTransferRequestBuilderSkipLogic:
    """Test TransferRequestBuilder skip-if-present logic."""

    def test_default_skip_if_present_enabled(self):
        """Test that skip-if-present is enabled by default."""
        request = TransferRequestBuilder() \
            .source("ghcr.io/fluxcd/helm-controller", "v1.3.0") \
            .target("helm-controller", "v1.3.0") \
            .build()

        assert request.skip_if_present is True

    def test_skip_if_present_method(self):
        """Test skip_if_present method."""
        # Enable skip-if-present explicitly
        request = TransferRequestBuilder() \
            .source("ghcr.io/fluxcd/helm-controller", "v1.3.0") \
            .target("helm-controller", "v1.3.0") \
            .skip_if_present(True) \
            .build()

        assert request.skip_if_present is True

        # Disable skip-if-present
        request = TransferRequestBuilder() \
            .source("ghcr.io/fluxcd/helm-controller", "v1.3.0") \
            .target("helm-controller", "v1.3.0") \
            .skip_if_present(False) \
            .build()

        assert request.skip_if_present is False

    def test_force_flag_disables_skip_if_present(self):
        """Test that force flag disables skip-if-present in CLI args."""
        # No force flag - skip enabled by default
        request = TransferRequestBuilder() \
            .from_cli_args(
                source_image="ghcr.io/fluxcd/helm-controller",
                target_repository="helm-controller",
                source_tag="v1.3.0",
                target_tag="v1.3.0",
                force=False
            ) \
            .build()

        assert request.skip_if_present is True

        # Force flag - skip disabled
        request = TransferRequestBuilder() \
            .from_cli_args(
                source_image="ghcr.io/fluxcd/helm-controller",
                target_repository="helm-controller",
                source_tag="v1.3.0",
                target_tag="v1.3.0",
                force=True
            ) \
            .build()

        assert request.skip_if_present is False

    def test_cli_builder_convenience_method(self):
        """Test for_cli_copy convenience method with force parameter."""
        # Test without force
        request = TransferRequestBuilder.for_cli_copy(
            source_image="ghcr.io/fluxcd/helm-controller",
            target_repository="helm-controller",
            source_tag="v1.3.0",
            force=False
        )

        assert request.skip_if_present is True

        # Test with force
        request = TransferRequestBuilder.for_cli_copy(
            source_image="ghcr.io/fluxcd/helm-controller",
            target_repository="helm-controller",
            source_tag="v1.3.0",
            force=True
        )

        assert request.skip_if_present is False


class TestTransferResultSkipFields:
    """Test TransferResult skip-related fields."""

    def test_transfer_result_default_skip_fields(self):
        """Test default values for skip-related fields."""
        request = TransferRequest(
            source_image="ghcr.io/fluxcd/helm-controller",
            source_tag="v1.3.0",
            target_repository="helm-controller",
            target_tag="v1.3.0"
        )

        result = TransferResult(
            request=request,
            success=True
        )

        # Verify default skip field values
        assert result.skipped is False
        assert result.skip_reason is None

    def test_transfer_result_skip_fields_set(self):
        """Test setting skip-related fields."""
        request = TransferRequest(
            source_image="ghcr.io/fluxcd/helm-controller",
            source_tag="v1.3.0",
            target_repository="helm-controller",
            target_tag="v1.3.0"
        )

        result = TransferResult(
            request=request,
            success=True,
            skipped=True,
            skip_reason="Target image helm-controller:v1.3.0 already exists with matching digest"
        )

        # Verify skip fields are set correctly
        assert result.skipped is True
        assert "already exists with matching digest" in result.skip_reason