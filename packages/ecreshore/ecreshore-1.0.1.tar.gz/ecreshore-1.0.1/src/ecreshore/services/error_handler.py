"""Error categorization and handling framework."""

import logging
from enum import Enum
from typing import Optional

from .transfer_service import DockerClientError
from ..ecr_auth import ECRAuthenticationError


class ConfigurationError(Exception):
    """Exception raised for configuration file or parsing errors."""

    pass


logger = logging.getLogger(__name__)


class ErrorCategory(Enum):
    """Categories of errors for handling strategies."""

    # Retryable errors - temporary issues that might resolve
    NETWORK_TIMEOUT = "network_timeout"
    SERVICE_UNAVAILABLE = "service_unavailable"
    RATE_LIMITED = "rate_limited"
    TEMPORARY_FAILURE = "temporary_failure"

    # Non-retryable errors - permanent issues requiring user intervention
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    NOT_FOUND = "not_found"
    INVALID_INPUT = "invalid_input"
    CONFIGURATION = "configuration"

    # System errors - local environment issues
    DOCKER_DAEMON = "docker_daemon"
    FILE_SYSTEM = "file_system"
    RESOURCE_EXHAUSTED = "resource_exhausted"

    # Unknown errors - unclassified
    UNKNOWN = "unknown"


class CategorizedError(Exception):
    """Exception with error category information."""

    def __init__(
        self,
        message: str,
        category: ErrorCategory,
        original_error: Optional[Exception] = None,
    ):
        super().__init__(message)
        self.category = category
        self.original_error = original_error

    @property
    def is_retryable(self) -> bool:
        """Check if this error category supports retrying."""
        return self.category in {
            ErrorCategory.NETWORK_TIMEOUT,
            ErrorCategory.SERVICE_UNAVAILABLE,
            ErrorCategory.RATE_LIMITED,
            ErrorCategory.TEMPORARY_FAILURE,
        }

    @property
    def requires_user_action(self) -> bool:
        """Check if this error requires user intervention."""
        return self.category in {
            ErrorCategory.AUTHENTICATION,
            ErrorCategory.AUTHORIZATION,
            ErrorCategory.INVALID_INPUT,
            ErrorCategory.CONFIGURATION,
            ErrorCategory.DOCKER_DAEMON,
        }


class ErrorCategorizer:
    """Service for categorizing exceptions into error types."""

    @staticmethod
    def categorize_error(error: Exception) -> CategorizedError:
        """Categorize an exception into an error category.

        Args:
            error: Exception to categorize

        Returns:
            CategorizedError with appropriate category
        """
        error_msg = str(error)
        error_msg_lower = error_msg.lower()

        # Try specific error type handlers first
        if isinstance(error, ECRAuthenticationError):
            return ErrorCategorizer._categorize_ecr_error(
                error_msg, error_msg_lower, error
            )

        if isinstance(error, DockerClientError):
            return ErrorCategorizer._categorize_docker_error(
                error_msg, error_msg_lower, error
            )

        # Try message-based categorization
        result = ErrorCategorizer._categorize_by_message_patterns(
            error_msg, error_msg_lower, error
        )
        if result:
            return result

        # Default to unknown
        return CategorizedError(
            f"Unknown error: {error_msg}", ErrorCategory.UNKNOWN, error
        )

    @staticmethod
    def _categorize_ecr_error(
        error_msg: str, error_msg_lower: str, error: Exception
    ) -> CategorizedError:
        """Categorize ECR-specific authentication errors."""
        if "credentials" in error_msg_lower or "token" in error_msg_lower:
            return CategorizedError(
                f"ECR authentication failed: {error_msg}",
                ErrorCategory.AUTHENTICATION,
                error,
            )
        elif "region" in error_msg_lower:
            return CategorizedError(
                f"ECR configuration error: {error_msg}",
                ErrorCategory.CONFIGURATION,
                error,
            )
        else:
            return CategorizedError(
                f"ECR error: {error_msg}", ErrorCategory.TEMPORARY_FAILURE, error
            )

    @staticmethod
    def _categorize_docker_error(
        error_msg: str, error_msg_lower: str, error: Exception
    ) -> CategorizedError:
        """Categorize Docker client errors."""
        if "connection" in error_msg_lower or "daemon" in error_msg_lower:
            return CategorizedError(
                f"Docker daemon connection failed: {error_msg}",
                ErrorCategory.DOCKER_DAEMON,
                error,
            )
        elif "not found" in error_msg_lower or "does not exist" in error_msg_lower:
            return CategorizedError(
                f"Docker image not found: {error_msg}",
                ErrorCategory.NOT_FOUND,
                error,
            )
        elif "timeout" in error_msg_lower:
            return CategorizedError(
                f"Docker operation timeout: {error_msg}",
                ErrorCategory.NETWORK_TIMEOUT,
                error,
            )
        elif "push" in error_msg_lower and (
            "denied" in error_msg_lower or "unauthorized" in error_msg_lower
        ):
            return CategorizedError(
                f"Docker push authorization failed: {error_msg}",
                ErrorCategory.AUTHORIZATION,
                error,
            )
        elif "space" in error_msg_lower or "disk" in error_msg_lower:
            return CategorizedError(
                f"Insufficient disk space: {error_msg}",
                ErrorCategory.RESOURCE_EXHAUSTED,
                error,
            )
        else:
            return CategorizedError(
                f"Docker operation failed: {error_msg}",
                ErrorCategory.TEMPORARY_FAILURE,
                error,
            )

    @staticmethod
    def _categorize_by_message_patterns(
        error_msg: str, error_msg_lower: str, error: Exception
    ) -> Optional[CategorizedError]:
        """Categorize errors based on message content patterns."""
        # Rate limiting - highest priority
        if ErrorCategorizer._is_rate_limited_error(error_msg_lower):
            return CategorizedError(
                f"Rate limited: {error_msg}", ErrorCategory.RATE_LIMITED, error
            )

        # Service unavailable - check before network errors for specificity
        if ErrorCategorizer._is_service_unavailable_error(error_msg_lower):
            return CategorizedError(
                f"Service unavailable: {error_msg}",
                ErrorCategory.SERVICE_UNAVAILABLE,
                error,
            )

        # File system errors - check before authorization for specificity
        if ErrorCategorizer._is_file_system_error(error_msg_lower):
            return CategorizedError(
                f"File system error: {error_msg}", ErrorCategory.FILE_SYSTEM, error
            )

        # Network-related errors
        if ErrorCategorizer._is_network_error(error_msg_lower):
            return CategorizedError(
                f"Network error: {error_msg}", ErrorCategory.NETWORK_TIMEOUT, error
            )

        # Authentication/authorization - most general, check last
        if ErrorCategorizer._is_authorization_error(error_msg_lower):
            return CategorizedError(
                f"Authorization error: {error_msg}", ErrorCategory.AUTHORIZATION, error
            )

        return None

    @staticmethod
    def _is_rate_limited_error(error_msg_lower: str) -> bool:
        """Check if error indicates rate limiting."""
        return any(
            keyword in error_msg_lower
            for keyword in ["rate limit", "throttled", "too many requests"]
        )

    @staticmethod
    def _is_service_unavailable_error(error_msg_lower: str) -> bool:
        """Check if error indicates service unavailability."""
        return any(
            keyword in error_msg_lower
            for keyword in [
                "service unavailable",
                "internal server error",
                "502",
                "503",
                "504",
            ]
        )

    @staticmethod
    def _is_network_error(error_msg_lower: str) -> bool:
        """Check if error is network-related."""
        return any(
            keyword in error_msg_lower
            for keyword in ["connection", "network", "timeout", "unreachable", "dns"]
        )

    @staticmethod
    def _is_file_system_error(error_msg_lower: str) -> bool:
        """Check if error is file system related."""
        # General file system errors
        if any(
            keyword in error_msg_lower
            for keyword in ["no space", "disk full", "file not found"]
        ):
            return True

        # File permission errors specifically
        if "permission denied" in error_msg_lower and any(
            keyword in error_msg_lower
            for keyword in ["file", "directory", "path", "accessing"]
        ):
            return True

        return False

    @staticmethod
    def _is_authorization_error(error_msg_lower: str) -> bool:
        """Check if error is authorization/permission related."""
        return any(
            keyword in error_msg_lower
            for keyword in ["unauthorized", "forbidden", "access denied", "permission"]
        )

    @staticmethod
    def get_recommended_retry_attempts(category: ErrorCategory) -> int:
        """Get recommended number of retry attempts for error category.

        Args:
            category: Error category

        Returns:
            Recommended retry attempts (0 means no retry recommended)
        """
        retry_attempts = {
            ErrorCategory.NETWORK_TIMEOUT: 3,
            ErrorCategory.SERVICE_UNAVAILABLE: 3,
            ErrorCategory.RATE_LIMITED: 5,
            ErrorCategory.TEMPORARY_FAILURE: 2,
        }

        return retry_attempts.get(category, 0)

    @staticmethod
    def get_user_guidance(category: ErrorCategory) -> str:
        """Get user guidance message for error category.

        Args:
            category: Error category

        Returns:
            Helpful guidance message
        """
        guidance = {
            ErrorCategory.AUTHENTICATION: "Check your AWS credentials and ensure they have ECR permissions",
            ErrorCategory.AUTHORIZATION: "Verify your AWS account has access to the ECR repository",
            ErrorCategory.DOCKER_DAEMON: "Ensure Docker daemon is running and accessible",
            ErrorCategory.NOT_FOUND: "Verify the source image name and tag are correct",
            ErrorCategory.INVALID_INPUT: "Check the command arguments and try again",
            ErrorCategory.CONFIGURATION: "Review your AWS region and registry configuration",
            ErrorCategory.RESOURCE_EXHAUSTED: "Free up disk space and try again",
            ErrorCategory.FILE_SYSTEM: "Check file permissions and available disk space",
            ErrorCategory.NETWORK_TIMEOUT: "Check network connectivity and try again",
            ErrorCategory.SERVICE_UNAVAILABLE: "AWS service may be temporarily unavailable",
            ErrorCategory.RATE_LIMITED: "Wait before retrying to avoid rate limits",
            ErrorCategory.TEMPORARY_FAILURE: "Try the operation again",
            ErrorCategory.UNKNOWN: "Review the error details and check logs",
        }

        return guidance.get(category, "Contact support if the problem persists")
