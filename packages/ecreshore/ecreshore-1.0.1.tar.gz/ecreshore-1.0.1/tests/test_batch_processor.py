"""Tests for batch processor functionality."""

import asyncio
import time
from unittest.mock import Mock, patch, AsyncMock
import pytest

from src.ecreshore.services.batch_processor import (
    BatchProcessor,
    BatchResult,
    AsyncRateLimiter
)
from src.ecreshore.services.batch_config import BatchRequest, BatchTransferRequest, BatchSettings
from src.ecreshore.services.batch_progress import BatchProgressReporter
from src.ecreshore.services.transfer_service import TransferService, TransferRequest, TransferResult


@pytest.mark.asyncio
async def test_rate_limiter_basic_functionality():
    """Test basic async rate limiter functionality."""
    limiter = AsyncRateLimiter(max_concurrent=2, min_interval=0.01)
    
    # Should be able to acquire permits asynchronously
    async with limiter:
        # Inside context, permit is acquired
        pass
    
    # Test manual acquire/release
    await limiter.acquire()
    limiter.release()


@pytest.mark.asyncio
async def test_rate_limiter_minimum_interval():
    """Test async rate limiter enforces minimum interval."""
    limiter = AsyncRateLimiter(max_concurrent=1, min_interval=0.1)
    
    start_time = time.time()
    
    # First acquire should be immediate
    await limiter.acquire()
    first_acquire_time = time.time()
    limiter.release()
    
    # Second acquire should wait for minimum interval
    await limiter.acquire()
    second_acquire_time = time.time()
    limiter.release()
    
    # Should have waited at least the minimum interval
    interval = second_acquire_time - first_acquire_time
    assert interval >= 0.1, f"Interval was {interval}, expected >= 0.1"


def test_batch_processor_initialization():
    """Test batch processor initialization."""
    processor = BatchProcessor()
    assert processor.transfer_service is None
    
    transfer_service = Mock(spec=TransferService)
    processor_with_service = BatchProcessor(transfer_service)
    assert processor_with_service.transfer_service is transfer_service


def test_batch_processor_get_transfer_service():
    """Test batch processor creates transfer service with settings."""
    processor = BatchProcessor()
    
    settings = BatchSettings(
        region="us-west-2",
        registry_id="123456789012",
        retry_attempts=5
    )
    
    with patch('src.ecreshore.services.batch_processor.HybridTransferService') as mock_hybrid_transfer_service:
        service = processor._get_transfer_service(settings)

        mock_hybrid_transfer_service.assert_called_once_with(
            region_name="us-west-2",
            registry_id="123456789012"
        )


def test_batch_result_properties():
    """Test batch result properties."""
    transfers = [
        BatchTransferRequest(source="nginx", target="my-nginx"),
        BatchTransferRequest(source="redis", target="my-redis")
    ]
    batch_request = BatchRequest(transfers=transfers)
    
    results = [
        Mock(success=True),
        Mock(success=False)
    ]
    
    batch_result = BatchResult(
        batch_request=batch_request,
        transfer_results=results,
        success_count=1,
        failure_count=1,
        total_duration=30.0,
        total_retries=2
    )
    
    assert batch_result.success_rate == 50.0
    assert batch_result.overall_success is False
    
    # Test all successful
    batch_result_success = BatchResult(
        batch_request=batch_request,
        transfer_results=results,
        success_count=2,
        failure_count=0,
        total_duration=30.0,
        total_retries=0
    )
    
    assert batch_result_success.success_rate == 100.0
    assert batch_result_success.overall_success is True


def test_batch_processor_validate_prerequisites():
    """Test batch prerequisites validation."""
    processor = BatchProcessor()
    
    transfers = [BatchTransferRequest(source="nginx", target="my-nginx")]
    batch_request = BatchRequest(transfers=transfers)
    
    # Mock transfer service
    mock_service = Mock(spec=TransferService)
    mock_service.validate_prerequisites.return_value = True
    
    with patch.object(processor, '_get_transfer_service', return_value=mock_service):
        assert processor.validate_batch_prerequisites(batch_request) is True
        mock_service.validate_prerequisites.assert_called_once()


def test_batch_processor_validate_empty_batch():
    """Test validation fails for empty batch.""" 
    processor = BatchProcessor()
    
    # Create batch request with empty transfers list directly (bypassing validation)
    batch_request = Mock()
    batch_request.transfers = []
    
    assert processor.validate_batch_prerequisites(batch_request) is False


def test_batch_processor_estimate_duration():
    """Test batch duration estimation."""
    processor = BatchProcessor()
    
    # Single transfer, single concurrent
    transfers = [BatchTransferRequest(source="nginx", target="my-nginx")]
    settings = BatchSettings(concurrent_transfers=1, retry_attempts=0)
    batch_request = BatchRequest(transfers=transfers, settings=settings)
    
    duration = processor.estimate_batch_duration(batch_request)
    assert duration > 30.0  # Should be base time + overhead
    
    # Multiple transfers, higher concurrency
    transfers = [
        BatchTransferRequest(source="nginx", target="my-nginx"),
        BatchTransferRequest(source="redis", target="my-redis"),
        BatchTransferRequest(source="postgres", target="my-postgres")
    ]
    settings = BatchSettings(concurrent_transfers=3, retry_attempts=2)
    batch_request = BatchRequest(transfers=transfers, settings=settings)
    
    duration_concurrent = processor.estimate_batch_duration(batch_request)
    
    # With higher concurrency, duration should account for parallelism
    assert duration_concurrent > 30.0
    # Should include retry overhead
    assert duration_concurrent > duration


def test_batch_processor_dry_run():
    """Test batch dry run functionality."""
    processor = BatchProcessor()
    
    transfers = [
        BatchTransferRequest(source="nginx", target="my-nginx"),
        BatchTransferRequest(source="redis", target="my-redis")
    ]
    settings = BatchSettings(concurrent_transfers=2, retry_attempts=3)
    batch_request = BatchRequest(transfers=transfers, settings=settings)
    
    with patch.object(processor, 'validate_batch_prerequisites', return_value=True):
        analysis = processor.dry_run_batch(batch_request)
    
    assert analysis['total_transfers'] == 2
    assert analysis['concurrent_transfers'] == 2
    assert analysis['retry_attempts'] == 3
    assert analysis['prerequisites_valid'] is True
    assert 'estimated_duration_seconds' in analysis
    assert len(analysis['transfers']) == 2
    
    # Check transfer analysis
    transfer_0 = analysis['transfers'][0]
    assert transfer_0['index'] == 0
    assert transfer_0['source'] == "nginx:latest"
    assert transfer_0['target'] == "my-nginx:latest"


@pytest.mark.asyncio
async def test_batch_processor_sequential_processing():
    """Test sequential batch processing."""
    from src.ecreshore.services.async_transfer_service import AsyncTransferService
    processor = BatchProcessor()
    
    # Create mock async transfer service
    mock_transfer_service = Mock(spec=AsyncTransferService)
    
    # Setup successful transfer results
    successful_result = TransferResult(
        request=Mock(),
        success=True,
        source_digest="sha256:abc123",
        target_digest="sha256:abc123"
    )
    successful_result.retry_count = 0
    # Mock async method to return awaitable result  
    from unittest.mock import AsyncMock
    mock_transfer_service.transfer_image = AsyncMock(return_value=successful_result)
    
    # Create batch request
    transfers = [
        BatchTransferRequest(source="nginx", target="my-nginx"),
        BatchTransferRequest(source="redis", target="my-redis")
    ]
    settings = BatchSettings(concurrent_transfers=1)  # Sequential
    batch_request = BatchRequest(transfers=transfers, settings=settings)
    
    # Mock progress reporter
    mock_progress = Mock(spec=BatchProgressReporter)
    from contextlib import nullcontext
    mock_progress.live_display = nullcontext
    
    with patch.object(processor, '_get_transfer_service', return_value=mock_transfer_service):
        result = await processor.process_batch(batch_request, mock_progress)
    
    # Verify results
    assert result.success_count == 2
    assert result.failure_count == 0
    assert result.overall_success is True
    assert len(result.transfer_results) == 2
    
    # Verify transfer service was called
    assert mock_transfer_service.transfer_image.call_count == 2
    
    # Verify progress reporting
    mock_progress.start_batch.assert_called_once_with(batch_request)
    mock_progress.finish_batch.assert_called_once()


@pytest.mark.asyncio
async def test_batch_processor_concurrent_processing():
    """Test concurrent batch processing."""
    from src.ecreshore.services.async_transfer_service import AsyncTransferService
    processor = BatchProcessor()
    
    # Create mock async transfer service
    mock_transfer_service = Mock(spec=AsyncTransferService)
    
    # Setup transfer results
    successful_result = TransferResult(
        request=Mock(),
        success=True
    )
    successful_result.retry_count = 0
    # Mock async method
    from unittest.mock import AsyncMock
    mock_transfer_service.transfer_image = AsyncMock(return_value=successful_result)
    
    # Create batch request with concurrency
    transfers = [
        BatchTransferRequest(source="nginx", target="my-nginx"),
        BatchTransferRequest(source="redis", target="my-redis"),
        BatchTransferRequest(source="postgres", target="my-postgres")
    ]
    settings = BatchSettings(concurrent_transfers=3)  # Concurrent
    batch_request = BatchRequest(transfers=transfers, settings=settings)
    
    # Mock progress reporter
    mock_progress = Mock(spec=BatchProgressReporter)
    from contextlib import nullcontext
    mock_progress.live_display = nullcontext
    
    with patch.object(processor, '_get_transfer_service', return_value=mock_transfer_service):
        result = await processor.process_batch(batch_request, mock_progress)
    
    # Verify results
    assert result.success_count == 3
    assert result.failure_count == 0
    assert result.overall_success is True
    
    # All transfers should have been called
    assert mock_transfer_service.transfer_image.call_count == 3


@pytest.mark.asyncio
async def test_batch_processor_mixed_results():
    """Test batch processing with mixed success/failure results."""
    from src.ecreshore.services.async_transfer_service import AsyncTransferService
    processor = BatchProcessor()
    
    # Create mock transfer service with mixed results
    mock_transfer_service = Mock(spec=AsyncTransferService)
    
    # First transfer succeeds, second fails
    successful_result = TransferResult(request=Mock(), success=True)
    successful_result.retry_count = 0
    failed_result = TransferResult(request=Mock(), success=False, error_message="Network error")
    failed_result.retry_count = 0
    
    # Mock async method with side effects
    from unittest.mock import AsyncMock
    mock_transfer_service.transfer_image = AsyncMock(side_effect=[successful_result, failed_result])
    
    # Create batch request
    transfers = [
        BatchTransferRequest(source="nginx", target="my-nginx"),
        BatchTransferRequest(source="redis", target="my-redis")
    ]
    batch_request = BatchRequest(transfers=transfers)
    
    # Mock progress reporter
    mock_progress = Mock(spec=BatchProgressReporter)
    from contextlib import nullcontext
    mock_progress.live_display = nullcontext
    
    with patch.object(processor, '_get_transfer_service', return_value=mock_transfer_service):
        result = await processor.process_batch(batch_request, mock_progress)
    
    # Verify mixed results
    assert result.success_count == 1
    assert result.failure_count == 1
    assert result.overall_success is False
    assert result.success_rate == 50.0


@pytest.mark.asyncio
async def test_batch_processor_exception_handling():
    """Test batch processor handles exceptions gracefully."""
    processor = BatchProcessor()
    
    # Create mock transfer service that raises exception
    mock_transfer_service = Mock(spec=TransferService)
    mock_transfer_service.transfer_image.side_effect = Exception("Unexpected error")
    
    # Create batch request
    transfers = [BatchTransferRequest(source="nginx", target="my-nginx")]
    batch_request = BatchRequest(transfers=transfers)
    
    # Mock progress reporter
    mock_progress = Mock(spec=BatchProgressReporter)
    from contextlib import nullcontext
    mock_progress.live_display = nullcontext
    
    with patch.object(processor, '_get_transfer_service', return_value=mock_transfer_service):
        result = await processor.process_batch(batch_request, mock_progress)
    
    # Should handle exception and create failed result
    assert result.success_count == 0
    assert result.failure_count == 1
    assert result.overall_success is False
    assert len(result.transfer_results) == 1
    assert not result.transfer_results[0].success
    assert "Unexpected error" in result.transfer_results[0].error_message


def test_import_paths():
    """Test that all imports work correctly."""
    from src.ecreshore.services.batch_processor import BatchProcessor
    from src.ecreshore.services.batch_processor import BatchResult
    from src.ecreshore.services.batch_processor import AsyncRateLimiter
    
    assert BatchProcessor is not None
    assert BatchResult is not None
    assert AsyncRateLimiter is not None