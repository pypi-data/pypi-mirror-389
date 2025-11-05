"""Tests for HybridTransferService."""

import pytest
from unittest.mock import Mock, AsyncMock, patch

from src.ecreshore.services.hybrid_transfer_service import HybridTransferService
from src.ecreshore.services.transfer_service import TransferRequest, TransferResult
from src.ecreshore.services.platform_models import ImagePlatformInfo, Platform


class TestHybridTransferService:
    """Tests for HybridTransferService functionality."""

    def test_initialization(self):
        """Test HybridTransferService initialization."""
        service = HybridTransferService(region_name="us-west-2", registry_id="123456789012")

        assert service.buildx_service is not None
        assert service.async_service is not None
        assert service._buildx_available is None

    def test_initialization_default_values(self):
        """Test HybridTransferService initialization with default values."""
        service = HybridTransferService()

        assert service.buildx_service is not None
        assert service.async_service is not None

    def test_get_ecr_registry_url_delegates_to_async_service(self):
        """Test that get_ecr_registry_url delegates to async service."""
        service = HybridTransferService()

        with patch.object(service.async_service, 'get_ecr_registry_url', return_value="test-url") as mock_get_url:
            result = service.get_ecr_registry_url()

        mock_get_url.assert_called_once()
        assert result == "test-url"

    def test_validate_prerequisites_delegates_to_async_service(self):
        """Test that validate_prerequisites delegates to async service."""
        service = HybridTransferService()

        with patch.object(service.async_service, 'validate_prerequisites', return_value=True) as mock_validate:
            result = service.validate_prerequisites()

        mock_validate.assert_called_once()
        assert result is True

    @pytest.mark.asyncio
    async def test_buildx_availability_caching(self):
        """Test that buildx availability is cached properly."""
        service = HybridTransferService()

        with patch.object(service.buildx_service, 'has_buildx_support', return_value=True) as mock_has_buildx:
            # First call should check buildx
            result1 = await service._is_buildx_available()
            assert result1 is True
            assert mock_has_buildx.call_count == 1

            # Second call should use cache
            result2 = await service._is_buildx_available()
            assert result2 is True
            assert mock_has_buildx.call_count == 1  # Still 1, not called again

    @pytest.mark.asyncio
    async def test_buildx_availability_handles_exceptions(self):
        """Test that buildx availability check handles exceptions gracefully."""
        service = HybridTransferService()

        with patch.object(service.buildx_service, 'has_buildx_support', side_effect=Exception("Buildx failed")) as mock_has_buildx:
            result = await service._is_buildx_available()

        assert result is False
        assert service._buildx_available is False
        mock_has_buildx.assert_called_once()

    @pytest.mark.asyncio
    async def test_copy_image_enhanced_prerequisites_failure(self):
        """Test copy_image_enhanced with prerequisites validation failure."""
        service = HybridTransferService()
        request = TransferRequest("nginx", "latest", "my-nginx", "v1.0")

        with patch.object(service, 'validate_prerequisites', return_value=False):
            result = await service.copy_image_enhanced(request)

        assert result['prerequisites_valid'] is False
        assert result['error_message'] == "Prerequisites validation failed"
        assert result['ecr_registry_url'] is None
        assert result['platform_info'] is None
        assert result['transfer_result'] is None

    @pytest.mark.asyncio
    async def test_copy_image_enhanced_successful_basic_transfer(self):
        """Test copy_image_enhanced with successful basic transfer."""
        service = HybridTransferService()
        request = TransferRequest("nginx", "latest", "my-nginx", "v1.0", preserve_architectures=False)

        expected_transfer_result = TransferResult(request=request, success=True)

        with patch.object(service, 'validate_prerequisites', return_value=True):
            with patch.object(service, 'get_ecr_registry_url', return_value="123456789012.dkr.ecr.us-west-2.amazonaws.com"):
                with patch.object(service, 'transfer_image', return_value=expected_transfer_result) as mock_transfer:
                    result = await service.copy_image_enhanced(request)

        assert result['prerequisites_valid'] is True
        assert result['ecr_registry_url'] == "123456789012.dkr.ecr.us-west-2.amazonaws.com"
        assert result['platform_info'] is None  # Not requested
        assert result['transfer_result'] == expected_transfer_result
        assert result['error_message'] is None
        mock_transfer.assert_called_once_with(request)

    @pytest.mark.asyncio
    async def test_copy_image_enhanced_with_platform_inspection(self):
        """Test copy_image_enhanced with multi-arch platform inspection."""
        service = HybridTransferService()
        request = TransferRequest("nginx", "latest", "my-nginx", "v1.0", preserve_architectures=True)

        # Mock platform info
        mock_platform_info = ImagePlatformInfo(
            repository="nginx",
            tag="latest",
            platforms=[
                Platform(os="linux", architecture="amd64"),
                Platform(os="linux", architecture="arm64")
            ],
            manifest_digest="sha256:abcd1234"
        )

        expected_transfer_result = TransferResult(request=request, success=True)

        with patch.object(service, 'validate_prerequisites', return_value=True):
            with patch.object(service, 'get_ecr_registry_url', return_value="test-registry.com"):
                with patch.object(service, 'inspect_image_platforms', return_value=mock_platform_info) as mock_inspect:
                    with patch.object(service, 'transfer_image', return_value=expected_transfer_result):
                        result = await service.copy_image_enhanced(request)

        assert result['prerequisites_valid'] is True
        assert result['platform_info'] == mock_platform_info
        assert result['transfer_result'] == expected_transfer_result
        mock_inspect.assert_called_once_with("nginx", "latest")

    @pytest.mark.asyncio
    async def test_copy_image_enhanced_platform_inspection_failure(self):
        """Test copy_image_enhanced continues when platform inspection fails."""
        service = HybridTransferService()
        request = TransferRequest("nginx", "latest", "my-nginx", "v1.0", preserve_architectures=True)

        expected_transfer_result = TransferResult(request=request, success=True)

        with patch.object(service, 'validate_prerequisites', return_value=True):
            with patch.object(service, 'get_ecr_registry_url', return_value="test-registry.com"):
                with patch.object(service, 'inspect_image_platforms', side_effect=Exception("Platform inspection failed")):
                    with patch.object(service, 'transfer_image', return_value=expected_transfer_result) as mock_transfer:
                        result = await service.copy_image_enhanced(request)

        # Should continue despite platform inspection failure
        assert result['prerequisites_valid'] is True
        assert result['platform_info'] is None  # Failed to get platform info
        assert result['transfer_result'] == expected_transfer_result
        mock_transfer.assert_called_once_with(request)

    @pytest.mark.asyncio
    async def test_copy_image_enhanced_transfer_failure(self):
        """Test copy_image_enhanced with transfer failure."""
        service = HybridTransferService()
        request = TransferRequest("nginx", "latest", "my-nginx", "v1.0")

        failed_transfer_result = TransferResult(request=request, success=False, error_message="Network error")

        with patch.object(service, 'validate_prerequisites', return_value=True):
            with patch.object(service, 'get_ecr_registry_url', return_value="test-registry.com"):
                with patch.object(service, 'transfer_image', return_value=failed_transfer_result):
                    result = await service.copy_image_enhanced(request)

        assert result['prerequisites_valid'] is True
        assert result['transfer_result'] == failed_transfer_result
        assert result['transfer_result'].success is False
        assert "Network error" in result['transfer_result'].error_message

    @pytest.mark.asyncio
    async def test_copy_image_enhanced_return_structure(self):
        """Test that copy_image_enhanced returns the expected dictionary structure."""
        service = HybridTransferService()
        request = TransferRequest("nginx", "latest", "my-nginx", "v1.0")

        with patch.object(service, 'validate_prerequisites', return_value=False):
            result = await service.copy_image_enhanced(request)

        # Verify all expected keys are present
        expected_keys = {
            'prerequisites_valid', 'ecr_registry_url', 'platform_info',
            'transfer_result', 'error_message'
        }
        assert set(result.keys()) == expected_keys

    def test_service_composition(self):
        """Test that HybridTransferService properly composes other services."""
        service = HybridTransferService(region_name="us-east-1", registry_id="999999999999")

        # Should have created composed services with the same parameters
        assert service.buildx_service is not None
        assert service.async_service is not None

        # Both services should have the same region and registry configuration
        assert hasattr(service.buildx_service, 'region_name') or hasattr(service.buildx_service, '_region_name')
        assert hasattr(service.async_service, 'region_name')


def test_import_paths():
    """Test that all imports work correctly."""
    from src.ecreshore.services.hybrid_transfer_service import HybridTransferService

    assert HybridTransferService is not None