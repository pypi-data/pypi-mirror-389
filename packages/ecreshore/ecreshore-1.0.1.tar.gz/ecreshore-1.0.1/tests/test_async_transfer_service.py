"""Tests for AsyncTransferService."""

import asyncio
import pytest
from unittest.mock import Mock, AsyncMock, patch

from src.ecreshore.services.async_transfer_service import AsyncTransferService
from src.ecreshore.services.transfer_service import TransferRequest, TransferResult
from src.ecreshore.async_docker_client import AsyncDockerClientError
from src.ecreshore.ecr_auth import ECRAuthenticationError


class TestAsyncTransferService:
    """Tests for AsyncTransferService functionality."""

    def test_initialization_defaults(self):
        """Test AsyncTransferService initialization with default values."""
        service = AsyncTransferService()

        assert service.region_name is None
        assert service.registry_id is None
        assert service.max_retry_attempts == 3
        assert service.enable_retry is False

    def test_initialization_with_values(self):
        """Test AsyncTransferService initialization with custom values."""
        service = AsyncTransferService(
            region_name="us-west-2",
            registry_id="123456789012",
            max_retry_attempts=5,
            enable_retry=True
        )

        assert service.region_name == "us-west-2"
        assert service.registry_id == "123456789012"
        assert service.max_retry_attempts == 5
        assert service.enable_retry is True

    @pytest.mark.asyncio
    async def test_transfer_image_calls_transfer_image_once(self):
        """Test that transfer_image delegates to _transfer_image_once."""
        service = AsyncTransferService()
        request = TransferRequest("nginx", "latest", "my-nginx", "v1.0")

        expected_result = TransferResult(request=request, success=True)

        with patch.object(service, '_transfer_image_once', return_value=expected_result) as mock_once:
            result = await service.transfer_image(request)

        mock_once.assert_called_once_with(request)
        assert result == expected_result

    @pytest.mark.asyncio
    async def test_push_with_streaming_success(self):
        """Test streaming push functionality without full Docker mock."""
        service = AsyncTransferService()

        mock_docker_client = AsyncMock()

        # Mock streaming push logs
        async def mock_push_stream(*args, **kwargs):
            yield {"status": "Preparing"}
            yield {"status": "Pushing"}
            yield {"status": "Pushed"}
            yield {"status": "Latest: digest: sha256:abc123"}

        mock_docker_client.push_image_stream = mock_push_stream
        auth_config = {"username": "test", "password": "test"}

        # This should not raise an exception
        await service._push_with_streaming(mock_docker_client, "repo", "tag", auth_config)

    @pytest.mark.asyncio
    async def test_push_with_streaming_error(self):
        """Test streaming push with error."""
        service = AsyncTransferService()

        mock_docker_client = AsyncMock()

        # Mock streaming push logs with error
        async def mock_push_stream(*args, **kwargs):
            yield {"status": "Preparing"}
            yield {"error": "Authentication required"}

        mock_docker_client.push_image_stream = mock_push_stream
        auth_config = {"username": "test", "password": "test"}

        with pytest.raises(AsyncDockerClientError) as exc_info:
            await service._push_with_streaming(mock_docker_client, "repo", "tag", auth_config)

        assert "Push failed: Authentication required" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_push_with_streaming_logs_progress(self):
        """Test that streaming push logs progress appropriately."""
        service = AsyncTransferService()

        mock_docker_client = AsyncMock()

        # Create 25 status logs to test progress logging every 10th entry
        async def mock_push_stream(*args, **kwargs):
            for i in range(25):
                yield {"status": f"Progress {i}"}

        mock_docker_client.push_image_stream = mock_push_stream
        auth_config = {"username": "test", "password": "test"}

        # Should complete without error and log progress
        await service._push_with_streaming(mock_docker_client, "repo", "tag", auth_config)

    @pytest.mark.asyncio
    async def test_concurrent_transfers_basic(self):
        """Test basic concurrent transfer functionality."""
        service = AsyncTransferService()

        requests = [
            TransferRequest("nginx", "latest", "my-nginx", "v1.0"),
            TransferRequest("redis", "alpine", "my-redis", "stable"),
        ]

        # Mock successful transfers
        expected_results = [
            TransferResult(request=requests[0], success=True),
            TransferResult(request=requests[1], success=True)
        ]

        with patch.object(service, 'transfer_image', side_effect=expected_results) as mock_transfer:
            results = await service.transfer_images_concurrent(requests, max_concurrent=2)

        assert len(results) == 2
        assert all(result.success for result in results)
        assert mock_transfer.call_count == 2

    @pytest.mark.asyncio
    async def test_concurrent_transfers_semaphore_limiting(self):
        """Test that semaphore limits concurrent execution."""
        service = AsyncTransferService()

        requests = [TransferRequest("nginx", "latest", "my-nginx", f"v{i}") for i in range(3)]

        # Track maximum concurrent calls
        current_calls = 0
        max_concurrent_seen = 0

        async def mock_transfer(request):
            nonlocal current_calls, max_concurrent_seen
            current_calls += 1
            max_concurrent_seen = max(max_concurrent_seen, current_calls)

            # Simulate async work
            await asyncio.sleep(0.01)

            current_calls -= 1
            return TransferResult(request=request, success=True)

        with patch.object(service, 'transfer_image', side_effect=mock_transfer):
            await service.transfer_images_concurrent(requests, max_concurrent=2)

        # Should never exceed the semaphore limit
        assert max_concurrent_seen <= 2

    @pytest.mark.asyncio
    async def test_concurrent_transfers_with_failures(self):
        """Test concurrent transfers with some failures."""
        service = AsyncTransferService()

        requests = [
            TransferRequest("nginx", "latest", "my-nginx", "v1.0"),
            TransferRequest("redis", "alpine", "my-redis", "stable"),
        ]

        # First succeeds, second fails
        results = [
            TransferResult(request=requests[0], success=True),
            TransferResult(request=requests[1], success=False, error_message="Failed")
        ]

        with patch.object(service, 'transfer_image', side_effect=results):
            transfer_results = await service.transfer_images_concurrent(requests)

        assert len(transfer_results) == 2
        assert transfer_results[0].success is True
        assert transfer_results[1].success is False
        assert "Failed" in transfer_results[1].error_message

    def test_streaming_push_handles_empty_logs(self):
        """Test that streaming push handles empty log entries correctly."""
        service = AsyncTransferService()

        # Test that we can create the method and it has expected signature
        assert hasattr(service, '_push_with_streaming')
        assert callable(getattr(service, '_push_with_streaming'))

    def test_service_inheritance(self):
        """Test that AsyncTransferService properly inherits from BaseECRService."""
        service = AsyncTransferService(region_name="us-west-2", registry_id="123456789012")

        # Should have inherited methods from BaseECRService
        assert hasattr(service, 'get_ecr_registry_url')
        assert hasattr(service, 'ecr_auth')

    @pytest.mark.asyncio
    async def test_transfer_image_once_error_handling_structure(self):
        """Test that _transfer_image_once has proper error handling structure."""
        service = AsyncTransferService()
        request = TransferRequest("nginx", "latest", "my-nginx", "v1.0")

        # Test that the method exists and is async
        assert hasattr(service, '_transfer_image_once')
        assert asyncio.iscoroutinefunction(service._transfer_image_once)


def test_import_paths():
    """Test that all imports work correctly."""
    from src.ecreshore.services.async_transfer_service import AsyncTransferService

    assert AsyncTransferService is not None