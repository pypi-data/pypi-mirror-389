"""Retry service with exponential backoff using tenacity."""

import logging
import random
from typing import Any, Callable, Optional

from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception,
    before_sleep_log,
    after_log,
    RetryError,
)

from .error_handler import ErrorCategorizer
from .transfer_service import TransferService, TransferRequest, TransferResult

logger = logging.getLogger(__name__)

# Default retry settings
DEFAULT_MAX_ATTEMPTS = 3
DEFAULT_MIN_WAIT_SECONDS = 1
DEFAULT_MAX_WAIT_SECONDS = 60
DEFAULT_MULTIPLIER = 2


class RetryService:
    """Service for handling retries with exponential backoff."""

    def __init__(
        self,
        max_attempts: int = DEFAULT_MAX_ATTEMPTS,
        min_wait: float = DEFAULT_MIN_WAIT_SECONDS,
        max_wait: float = DEFAULT_MAX_WAIT_SECONDS,
        multiplier: float = DEFAULT_MULTIPLIER,
        jitter: bool = True,
    ):
        """Initialize retry service.

        Args:
            max_attempts: Maximum number of retry attempts
            min_wait: Minimum wait time between retries in seconds
            max_wait: Maximum wait time between retries in seconds
            multiplier: Exponential backoff multiplier
            jitter: Whether to add random jitter to wait times
        """
        self.max_attempts = max_attempts
        self.min_wait = min_wait
        self.max_wait = max_wait
        self.multiplier = multiplier
        self.jitter = jitter

    def should_retry_exception(self, exception: Exception) -> bool:
        """Determine if an exception should be retried.

        Args:
            exception: Exception to check

        Returns:
            True if the exception should be retried
        """
        categorized_error = ErrorCategorizer.categorize_error(exception)
        return categorized_error.is_retryable

    def create_retry_decorator(self, custom_max_attempts: Optional[int] = None):
        """Create a tenacity retry decorator with configured settings.

        Args:
            custom_max_attempts: Override default max attempts for this decorator

        Returns:
            Configured tenacity retry decorator
        """
        max_attempts = custom_max_attempts or self.max_attempts

        # Create wait strategy
        wait_strategy = wait_exponential(
            multiplier=self.multiplier, min=self.min_wait, max=self.max_wait
        )

        return retry(
            stop=stop_after_attempt(max_attempts),
            wait=wait_strategy,
            retry=retry_if_exception(self.should_retry_exception),
            before_sleep=before_sleep_log(logger, logging.WARNING),
            after=after_log(logger, logging.INFO),
            reraise=True,
        )

    def transfer_image_with_retry(
        self,
        transfer_service: TransferService,
        request: TransferRequest,
        custom_max_attempts: Optional[int] = None,
    ) -> TransferResult:
        """Transfer image with automatic retry logic.

        Args:
            transfer_service: Transfer service instance
            request: Transfer request
            custom_max_attempts: Override default max attempts

        Returns:
            Transfer result
        """
        retry_decorator = self.create_retry_decorator(custom_max_attempts)

        @retry_decorator
        def _do_transfer():
            """Internal function with retry decoration."""
            result = transfer_service._transfer_image_once(request)

            # If transfer failed, raise the error to trigger retry logic
            if not result.success and result.error_message:
                # Try to find the original exception in the error message
                # For now, create a generic exception
                raise Exception(result.error_message)

            return result

        try:
            return _do_transfer()
        except RetryError as e:
            # All retry attempts failed
            logger.error(f"Transfer failed after {self.max_attempts} attempts: {e}")
            return TransferResult(
                request=request,
                success=False,
                error_message=f"Transfer failed after {self.max_attempts} retry attempts: {str(e.last_attempt.exception())}",
            )
        except Exception as e:
            # Unexpected error that bypassed retry logic
            categorized_error = ErrorCategorizer.categorize_error(e)
            logger.error(f"Transfer failed with non-retryable error: {e}")
            return TransferResult(
                request=request,
                success=False,
                error_message=f"Transfer failed ({categorized_error.category.value}): {str(e)}",
            )

    def execute_with_retry(
        self,
        func: Callable[..., Any],
        *args,
        custom_max_attempts: Optional[int] = None,
        **kwargs,
    ) -> Any:
        """Execute any function with retry logic.

        Args:
            func: Function to execute
            *args: Positional arguments for function
            custom_max_attempts: Override default max attempts
            **kwargs: Keyword arguments for function

        Returns:
            Function result

        Raises:
            Exception: If all retry attempts fail
        """
        retry_decorator = self.create_retry_decorator(custom_max_attempts)

        @retry_decorator
        def _execute():
            return func(*args, **kwargs)

        return _execute()

    def get_retry_statistics(self, exception: Exception) -> dict:
        """Get retry statistics and recommendations for an exception.

        Args:
            exception: Exception to analyze

        Returns:
            Dictionary with retry statistics and recommendations
        """
        categorized_error = ErrorCategorizer.categorize_error(exception)

        # Calculate expected total time for all retries
        total_wait_time = 0
        for attempt in range(1, self.max_attempts):
            wait_time = min(
                self.min_wait * (self.multiplier ** (attempt - 1)), self.max_wait
            )
            total_wait_time += wait_time

        return {
            "category": categorized_error.category.value,
            "is_retryable": categorized_error.is_retryable,
            "max_attempts": self.max_attempts,
            "estimated_total_wait_seconds": total_wait_time,
            "requires_user_action": categorized_error.requires_user_action,
            "guidance": ErrorCategorizer.get_user_guidance(categorized_error.category),
        }

    @staticmethod
    def _jitter_func(value: float) -> float:
        """Add jitter to wait time to avoid thundering herd.

        Args:
            value: Base wait time

        Returns:
            Wait time with jitter applied
        """
        # Add up to 25% random jitter
        jitter_range = value * 0.25
        return value + random.uniform(-jitter_range, jitter_range)

    @classmethod
    def create_for_batch_settings(cls, batch_settings) -> "RetryService":
        """Create retry service from batch configuration settings.

        Args:
            batch_settings: BatchSettings instance

        Returns:
            Configured RetryService instance
        """
        from .batch_config import BatchSettings

        if not isinstance(batch_settings, BatchSettings):
            raise ValueError("batch_settings must be a BatchSettings instance")

        return cls(
            max_attempts=batch_settings.retry_attempts + 1,  # +1 for initial attempt
            min_wait=DEFAULT_MIN_WAIT_SECONDS,
            max_wait=DEFAULT_MAX_WAIT_SECONDS,
            multiplier=DEFAULT_MULTIPLIER,
            jitter=True,
        )


# Convenience functions for common retry scenarios
def create_transfer_retry_service(
    max_attempts: int = DEFAULT_MAX_ATTEMPTS,
) -> RetryService:
    """Create retry service optimized for image transfers.

    Args:
        max_attempts: Maximum retry attempts

    Returns:
        Configured RetryService for transfers
    """
    return RetryService(
        max_attempts=max_attempts,
        min_wait=2,  # Start with 2 second wait for transfers
        max_wait=120,  # Cap at 2 minutes for transfers
        multiplier=2,
        jitter=True,
    )


def create_network_retry_service(max_attempts: int = 5) -> RetryService:
    """Create retry service optimized for network operations.

    Args:
        max_attempts: Maximum retry attempts

    Returns:
        Configured RetryService for network operations
    """
    return RetryService(
        max_attempts=max_attempts,
        min_wait=1,  # Quick retry for network issues
        max_wait=30,  # Shorter max wait for network
        multiplier=1.5,  # Gentler backoff
        jitter=True,
    )


def create_rate_limit_retry_service(max_attempts: int = 8) -> RetryService:
    """Create retry service optimized for rate-limited operations.

    Args:
        max_attempts: Maximum retry attempts

    Returns:
        Configured RetryService for rate-limited operations
    """
    return RetryService(
        max_attempts=max_attempts,
        min_wait=5,  # Longer initial wait for rate limits
        max_wait=300,  # Up to 5 minutes for rate limits
        multiplier=2,
        jitter=True,
    )
