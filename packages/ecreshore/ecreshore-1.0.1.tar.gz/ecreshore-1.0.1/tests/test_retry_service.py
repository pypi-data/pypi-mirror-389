"""Tests for retry service functionality."""

import pytest
import time
from unittest.mock import Mock, patch, MagicMock
from tenacity import RetryError

pytestmark = pytest.mark.slow

from src.ecreshore.services.retry_service import (
    RetryService,
    create_transfer_retry_service,
    create_network_retry_service,
    create_rate_limit_retry_service,
    DEFAULT_MAX_ATTEMPTS,
    DEFAULT_MIN_WAIT_SECONDS,
    DEFAULT_MAX_WAIT_SECONDS,
    DEFAULT_MULTIPLIER
)
from src.ecreshore.services.transfer_service import TransferService, TransferRequest, TransferResult, DockerClientError
from src.ecreshore.services.error_handler import ErrorCategory, CategorizedError
from src.ecreshore.services.batch_config import BatchSettings
from src.ecreshore.ecr_auth import ECRAuthenticationError


def test_retry_service_initialization():
    """Test retry service initialization with default values."""
    retry_service = RetryService()
    
    assert retry_service.max_attempts == DEFAULT_MAX_ATTEMPTS
    assert retry_service.min_wait == DEFAULT_MIN_WAIT_SECONDS
    assert retry_service.max_wait == DEFAULT_MAX_WAIT_SECONDS
    assert retry_service.multiplier == DEFAULT_MULTIPLIER
    assert retry_service.jitter is True


def test_retry_service_custom_initialization():
    """Test retry service initialization with custom values."""
    retry_service = RetryService(
        max_attempts=5,
        min_wait=2.0,
        max_wait=120.0,
        multiplier=3.0,
        jitter=False
    )
    
    assert retry_service.max_attempts == 5
    assert retry_service.min_wait == 2.0
    assert retry_service.max_wait == 120.0
    assert retry_service.multiplier == 3.0
    assert retry_service.jitter is False


def test_should_retry_exception_retryable():
    """Test should_retry_exception returns True for retryable errors."""
    retry_service = RetryService()
    
    # Network timeout should be retryable
    network_error = DockerClientError("Docker operation timeout")
    assert retry_service.should_retry_exception(network_error) is True


def test_should_retry_exception_non_retryable():
    """Test should_retry_exception returns False for non-retryable errors."""
    retry_service = RetryService()
    
    # Authentication error should not be retryable  
    auth_error = ECRAuthenticationError("Invalid credentials")
    assert retry_service.should_retry_exception(auth_error) is False


def test_jitter_function():
    """Test jitter function adds appropriate randomness."""
    base_value = 10.0
    
    # Test multiple times to ensure jitter is applied
    jittered_values = [RetryService._jitter_func(base_value) for _ in range(10)]
    
    # All values should be different (with high probability)
    assert len(set(jittered_values)) > 5
    
    # All values should be within reasonable range (base ± 25%)
    for value in jittered_values:
        assert 7.5 <= value <= 12.5


def test_execute_with_retry_success():
    """Test execute_with_retry with successful function."""
    retry_service = RetryService(max_attempts=3)
    
    def success_func(x, y):
        return x + y
    
    result = retry_service.execute_with_retry(success_func, 2, 3)
    assert result == 5


def test_execute_with_retry_failure_then_success():
    """Test execute_with_retry with function that fails then succeeds."""
    retry_service = RetryService(max_attempts=3, min_wait=0.01, max_wait=0.1)
    
    call_count = 0
    
    def flaky_func():
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise DockerClientError("Docker operation timeout")
        return "success"
    
    result = retry_service.execute_with_retry(flaky_func)
    assert result == "success"
    assert call_count == 3


def test_execute_with_retry_all_attempts_fail():
    """Test execute_with_retry when all attempts fail."""
    retry_service = RetryService(max_attempts=2, min_wait=0.01, max_wait=0.1)
    
    def always_fail():
        raise DockerClientError("Docker operation timeout")
    
    with pytest.raises(DockerClientError):
        retry_service.execute_with_retry(always_fail)


def test_execute_with_retry_non_retryable_error():
    """Test execute_with_retry with non-retryable error fails immediately."""
    retry_service = RetryService(max_attempts=3, min_wait=0.01, max_wait=0.1)
    
    call_count = 0
    
    def non_retryable_error():
        nonlocal call_count
        call_count += 1
        raise ECRAuthenticationError("Invalid credentials")
    
    with pytest.raises(ECRAuthenticationError):
        retry_service.execute_with_retry(non_retryable_error)
    
    # Should fail immediately without retries
    assert call_count == 1


def test_get_retry_statistics():
    """Test get_retry_statistics returns correct information."""
    retry_service = RetryService(max_attempts=4, min_wait=2, max_wait=60, multiplier=2)
    
    network_error = DockerClientError("Docker operation timeout")
    stats = retry_service.get_retry_statistics(network_error)
    
    assert stats['category'] == ErrorCategory.NETWORK_TIMEOUT.value
    assert stats['is_retryable'] is True
    assert stats['max_attempts'] == 4
    assert stats['requires_user_action'] is False
    assert 'estimated_total_wait_seconds' in stats
    assert 'guidance' in stats
    
    # Estimated wait should be sum of exponential backoff delays
    # 2 * (2^0) + 2 * (2^1) + 2 * (2^2) = 2 + 4 + 8 = 14
    assert stats['estimated_total_wait_seconds'] == 14


def test_get_retry_statistics_non_retryable():
    """Test get_retry_statistics for non-retryable error."""
    retry_service = RetryService()
    
    auth_error = ECRAuthenticationError("Invalid credentials")
    stats = retry_service.get_retry_statistics(auth_error)
    
    assert stats['category'] == ErrorCategory.AUTHENTICATION.value
    assert stats['is_retryable'] is False
    assert stats['requires_user_action'] is True


def test_create_for_batch_settings():
    """Test creating retry service from batch settings."""
    settings = BatchSettings(retry_attempts=5)
    
    retry_service = RetryService.create_for_batch_settings(settings)
    
    # retry_attempts + 1 for initial attempt
    assert retry_service.max_attempts == 6
    assert retry_service.min_wait == DEFAULT_MIN_WAIT_SECONDS
    assert retry_service.max_wait == DEFAULT_MAX_WAIT_SECONDS
    assert retry_service.jitter is True


def test_create_for_batch_settings_invalid_input():
    """Test creating retry service with invalid batch settings."""
    with pytest.raises(ValueError, match="batch_settings must be a BatchSettings instance"):
        RetryService.create_for_batch_settings("invalid")


def test_transfer_image_with_retry_success():
    """Test transfer_image_with_retry with successful transfer."""
    retry_service = RetryService()
    
    # Mock transfer service
    mock_transfer_service = Mock(spec=TransferService)
    request = TransferRequest(
        source_image="nginx",
        source_tag="latest", 
        target_repository="my-nginx",
        target_tag="latest"
    )
    
    success_result = TransferResult(
        request=request,
        success=True,
        source_digest="sha256:abc123",
        target_digest="sha256:abc123"
    )
    mock_transfer_service._transfer_image_once.return_value = success_result
    
    result = retry_service.transfer_image_with_retry(mock_transfer_service, request)
    
    assert result.success is True
    assert result.source_digest == "sha256:abc123"
    mock_transfer_service._transfer_image_once.assert_called_once_with(request)


def test_transfer_image_with_retry_failure_then_success():
    """Test transfer_image_with_retry with failure then success."""
    retry_service = RetryService(max_attempts=3, min_wait=0.01, max_wait=0.1)
    
    mock_transfer_service = Mock(spec=TransferService)
    request = TransferRequest(
        source_image="nginx",
        source_tag="latest",
        target_repository="my-nginx", 
        target_tag="latest"
    )
    
    # First two attempts fail, third succeeds
    failure_result = TransferResult(
        request=request,
        success=False,
        error_message="Docker operation timeout"
    )
    success_result = TransferResult(
        request=request,
        success=True,
        source_digest="sha256:abc123",
        target_digest="sha256:abc123"
    )
    
    mock_transfer_service._transfer_image_once.side_effect = [
        failure_result,  # First attempt fails
        failure_result,  # Second attempt fails
        success_result   # Third attempt succeeds
    ]
    
    result = retry_service.transfer_image_with_retry(mock_transfer_service, request)
    
    assert result.success is True
    assert mock_transfer_service._transfer_image_once.call_count == 3


def test_transfer_image_with_retry_all_attempts_fail():
    """Test transfer_image_with_retry when all attempts fail."""
    retry_service = RetryService(max_attempts=2, min_wait=0.01, max_wait=0.1)
    
    mock_transfer_service = Mock(spec=TransferService)
    request = TransferRequest(
        source_image="nginx",
        source_tag="latest",
        target_repository="my-nginx",
        target_tag="latest"
    )
    
    failure_result = TransferResult(
        request=request,
        success=False,
        error_message="Docker operation timeout"
    )
    mock_transfer_service._transfer_image_once.return_value = failure_result
    
    result = retry_service.transfer_image_with_retry(mock_transfer_service, request)
    
    assert result.success is False
    assert "Transfer failed" in result.error_message
    assert mock_transfer_service._transfer_image_once.call_count == 2


def test_create_transfer_retry_service():
    """Test create_transfer_retry_service convenience function."""
    retry_service = create_transfer_retry_service(max_attempts=5)
    
    assert retry_service.max_attempts == 5
    assert retry_service.min_wait == 2  # Transfer-optimized settings
    assert retry_service.max_wait == 120
    assert retry_service.multiplier == 2
    assert retry_service.jitter is True


def test_create_network_retry_service():
    """Test create_network_retry_service convenience function."""
    retry_service = create_network_retry_service(max_attempts=7)
    
    assert retry_service.max_attempts == 7
    assert retry_service.min_wait == 1  # Network-optimized settings
    assert retry_service.max_wait == 30
    assert retry_service.multiplier == 1.5
    assert retry_service.jitter is True


def test_create_rate_limit_retry_service():
    """Test create_rate_limit_retry_service convenience function."""
    retry_service = create_rate_limit_retry_service(max_attempts=10)
    
    assert retry_service.max_attempts == 10
    assert retry_service.min_wait == 5  # Rate-limit-optimized settings
    assert retry_service.max_wait == 300
    assert retry_service.multiplier == 2
    assert retry_service.jitter is True


def test_retry_decorator_integration():
    """Test that retry decorator is properly configured and works."""
    retry_service = RetryService(max_attempts=3, min_wait=0.01, max_wait=0.1)
    
    call_count = 0
    
    def flaky_function():
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise DockerClientError("Docker operation timeout")
        return "success"
    
    # Test decorator creation and execution
    decorator = retry_service.create_retry_decorator()
    decorated_func = decorator(flaky_function)
    
    result = decorated_func()
    assert result == "success"
    assert call_count == 3


def test_custom_max_attempts_override():
    """Test that custom max attempts properly overrides default."""
    retry_service = RetryService(max_attempts=3)
    
    mock_transfer_service = Mock(spec=TransferService)
    request = TransferRequest(
        source_image="nginx",
        source_tag="latest",
        target_repository="my-nginx",
        target_tag="latest"
    )
    
    failure_result = TransferResult(
        request=request,
        success=False,
        error_message="Docker operation timeout"
    )
    mock_transfer_service._transfer_image_once.return_value = failure_result
    
    # Override to 5 attempts
    result = retry_service.transfer_image_with_retry(
        mock_transfer_service, 
        request, 
        custom_max_attempts=5
    )
    
    assert result.success is False  
    assert "Transfer failed" in result.error_message
    assert mock_transfer_service._transfer_image_once.call_count == 5


def test_retry_statistics_wait_time_calculation():
    """Test that retry statistics calculate wait times correctly."""
    retry_service = RetryService(max_attempts=4, min_wait=1, max_wait=100, multiplier=2)
    
    error = DockerClientError("Docker operation timeout")
    stats = retry_service.get_retry_statistics(error)
    
    # Expected: 1*(2^0) + 1*(2^1) + 1*(2^2) = 1 + 2 + 4 = 7 seconds
    assert stats['estimated_total_wait_seconds'] == 7
    
    # Test with max_wait cap
    retry_service_capped = RetryService(max_attempts=10, min_wait=50, max_wait=100, multiplier=2)
    stats_capped = retry_service_capped.get_retry_statistics(error)
    
    # With capping, later attempts should be limited to max_wait
    # 50 + 100 + 100 + ... (capped values)
    expected_capped = 50 + 100 + 100 + 100 + 100 + 100 + 100 + 100 + 100  # 9 retry waits
    assert stats_capped['estimated_total_wait_seconds'] == expected_capped


def test_import_paths():
    """Test that all imports work correctly."""
    from src.ecreshore.services.retry_service import RetryService
    from src.ecreshore.services.retry_service import create_transfer_retry_service
    
    assert RetryService is not None
    assert create_transfer_retry_service is not None