"""Tests for ErrorCategorizer and error handling framework."""

import pytest

from src.ecreshore.services.error_handler import (
    ErrorCategory, CategorizedError, ErrorCategorizer
)
from src.ecreshore.services.transfer_service import DockerClientError
from src.ecreshore.ecr_auth import ECRAuthenticationError


class TestErrorCategory:
    def test_error_category_values(self):
        """Test ErrorCategory enum values."""
        assert ErrorCategory.NETWORK_TIMEOUT.value == "network_timeout"
        assert ErrorCategory.AUTHENTICATION.value == "authentication"
        assert ErrorCategory.DOCKER_DAEMON.value == "docker_daemon"
        assert ErrorCategory.UNKNOWN.value == "unknown"


class TestCategorizedError:
    def test_categorized_error_creation(self):
        """Test CategorizedError creation."""
        original_error = Exception("Original error")
        error = CategorizedError(
            "Test error message",
            ErrorCategory.NETWORK_TIMEOUT,
            original_error
        )
        
        assert str(error) == "Test error message"
        assert error.category == ErrorCategory.NETWORK_TIMEOUT
        assert error.original_error is original_error
    
    def test_categorized_error_without_original(self):
        """Test CategorizedError without original error."""
        error = CategorizedError(
            "Test error message",
            ErrorCategory.CONFIGURATION
        )
        
        assert str(error) == "Test error message"
        assert error.category == ErrorCategory.CONFIGURATION
        assert error.original_error is None
    
    def test_is_retryable_true(self):
        """Test is_retryable for retryable categories."""
        retryable_categories = [
            ErrorCategory.NETWORK_TIMEOUT,
            ErrorCategory.SERVICE_UNAVAILABLE,
            ErrorCategory.RATE_LIMITED,
            ErrorCategory.TEMPORARY_FAILURE
        ]
        
        for category in retryable_categories:
            error = CategorizedError("Test", category)
            assert error.is_retryable is True, f"Category {category} should be retryable"
    
    def test_is_retryable_false(self):
        """Test is_retryable for non-retryable categories."""
        non_retryable_categories = [
            ErrorCategory.AUTHENTICATION,
            ErrorCategory.AUTHORIZATION,
            ErrorCategory.NOT_FOUND,
            ErrorCategory.INVALID_INPUT,
            ErrorCategory.CONFIGURATION,
            ErrorCategory.DOCKER_DAEMON,
            ErrorCategory.FILE_SYSTEM,
            ErrorCategory.RESOURCE_EXHAUSTED,
            ErrorCategory.UNKNOWN
        ]
        
        for category in non_retryable_categories:
            error = CategorizedError("Test", category)
            assert error.is_retryable is False, f"Category {category} should not be retryable"
    
    def test_requires_user_action_true(self):
        """Test requires_user_action for categories requiring intervention."""
        user_action_categories = [
            ErrorCategory.AUTHENTICATION,
            ErrorCategory.AUTHORIZATION,
            ErrorCategory.INVALID_INPUT,
            ErrorCategory.CONFIGURATION,
            ErrorCategory.DOCKER_DAEMON
        ]
        
        for category in user_action_categories:
            error = CategorizedError("Test", category)
            assert error.requires_user_action is True, f"Category {category} should require user action"
    
    def test_requires_user_action_false(self):
        """Test requires_user_action for categories not requiring intervention."""
        no_user_action_categories = [
            ErrorCategory.NETWORK_TIMEOUT,
            ErrorCategory.SERVICE_UNAVAILABLE,
            ErrorCategory.RATE_LIMITED,
            ErrorCategory.TEMPORARY_FAILURE,
            ErrorCategory.NOT_FOUND,
            ErrorCategory.FILE_SYSTEM,
            ErrorCategory.RESOURCE_EXHAUSTED,
            ErrorCategory.UNKNOWN
        ]
        
        for category in no_user_action_categories:
            error = CategorizedError("Test", category)
            assert error.requires_user_action is False, f"Category {category} should not require user action"


class TestErrorCategorizer:
    def test_categorize_ecr_authentication_credentials(self):
        """Test ECR authentication error categorization - credentials."""
        error = ECRAuthenticationError("Invalid credentials")
        result = ErrorCategorizer.categorize_error(error)
        
        assert result.category == ErrorCategory.AUTHENTICATION
        assert "ECR authentication failed" in str(result)
        assert result.original_error is error
    
    def test_categorize_ecr_authentication_token(self):
        """Test ECR authentication error categorization - token."""
        error = ECRAuthenticationError("Token expired")
        result = ErrorCategorizer.categorize_error(error)
        
        assert result.category == ErrorCategory.AUTHENTICATION
        assert "ECR authentication failed" in str(result)
    
    def test_categorize_ecr_authentication_region(self):
        """Test ECR authentication error categorization - region."""
        error = ECRAuthenticationError("Invalid region specified")
        result = ErrorCategorizer.categorize_error(error)
        
        assert result.category == ErrorCategory.CONFIGURATION
        assert "ECR configuration error" in str(result)
    
    def test_categorize_ecr_authentication_generic(self):
        """Test ECR authentication error categorization - generic."""
        error = ECRAuthenticationError("Service temporarily unavailable")
        result = ErrorCategorizer.categorize_error(error)
        
        assert result.category == ErrorCategory.TEMPORARY_FAILURE
        assert "ECR error" in str(result)
    
    def test_categorize_docker_daemon_connection(self):
        """Test Docker client error categorization - daemon connection."""
        error = DockerClientError("Cannot connect to the Docker daemon")
        result = ErrorCategorizer.categorize_error(error)
        
        assert result.category == ErrorCategory.DOCKER_DAEMON
        assert "Docker daemon connection failed" in str(result)
    
    def test_categorize_docker_not_found(self):
        """Test Docker client error categorization - not found."""
        error = DockerClientError("Image not found")
        result = ErrorCategorizer.categorize_error(error)
        
        assert result.category == ErrorCategory.NOT_FOUND
        assert "Docker image not found" in str(result)
    
    def test_categorize_docker_timeout(self):
        """Test Docker client error categorization - timeout."""
        error = DockerClientError("Operation timeout")
        result = ErrorCategorizer.categorize_error(error)
        
        assert result.category == ErrorCategory.NETWORK_TIMEOUT
        assert "Docker operation timeout" in str(result)
    
    def test_categorize_docker_push_denied(self):
        """Test Docker client error categorization - push denied."""
        error = DockerClientError("Push denied: access forbidden")
        result = ErrorCategorizer.categorize_error(error)
        
        assert result.category == ErrorCategory.AUTHORIZATION
        assert "Docker push authorization failed" in str(result)
    
    def test_categorize_docker_push_unauthorized(self):
        """Test Docker client error categorization - push unauthorized."""
        error = DockerClientError("Push failed: unauthorized")
        result = ErrorCategorizer.categorize_error(error)
        
        assert result.category == ErrorCategory.AUTHORIZATION
        assert "Docker push authorization failed" in str(result)
    
    def test_categorize_docker_disk_space(self):
        """Test Docker client error categorization - disk space."""
        error = DockerClientError("No space left on device")
        result = ErrorCategorizer.categorize_error(error)
        
        assert result.category == ErrorCategory.RESOURCE_EXHAUSTED
        assert "Insufficient disk space" in str(result)
    
    def test_categorize_docker_generic(self):
        """Test Docker client error categorization - generic."""
        error = DockerClientError("Generic Docker error")
        result = ErrorCategorizer.categorize_error(error)
        
        assert result.category == ErrorCategory.TEMPORARY_FAILURE
        assert "Docker operation failed" in str(result)
    
    def test_categorize_network_errors(self):
        """Test network error categorization."""
        network_errors = [
            Exception("Connection timeout"),
            Exception("Network unreachable"),
            Exception("DNS resolution failed"),
            Exception("Connection refused")
        ]
        
        for error in network_errors:
            result = ErrorCategorizer.categorize_error(error)
            assert result.category == ErrorCategory.NETWORK_TIMEOUT
            assert "Network error" in str(result)
    
    def test_categorize_rate_limit_errors(self):
        """Test rate limit error categorization."""
        rate_limit_errors = [
            Exception("Rate limit exceeded"),
            Exception("Too many requests"),
            Exception("Request throttled")
        ]
        
        for error in rate_limit_errors:
            result = ErrorCategorizer.categorize_error(error)
            assert result.category == ErrorCategory.RATE_LIMITED
            assert "Rate limited" in str(result)
    
    def test_categorize_service_unavailable_errors(self):
        """Test service unavailable error categorization."""
        service_errors = [
            Exception("Service unavailable"),
            Exception("Internal server error"),
            Exception("HTTP 502 Bad Gateway"),
            Exception("HTTP 503 Service Unavailable"),
            Exception("HTTP 504 Gateway Timeout")
        ]
        
        for error in service_errors:
            result = ErrorCategorizer.categorize_error(error)
            assert result.category == ErrorCategory.SERVICE_UNAVAILABLE
            assert "Service unavailable" in str(result)
    
    def test_categorize_authorization_errors(self):
        """Test authorization error categorization."""
        auth_errors = [
            Exception("Unauthorized access"),
            Exception("Access forbidden"),
            Exception("Permission denied"),
            Exception("Access denied")
        ]
        
        for error in auth_errors:
            result = ErrorCategorizer.categorize_error(error)
            assert result.category == ErrorCategory.AUTHORIZATION
            assert "Authorization error" in str(result)
    
    def test_categorize_file_system_errors(self):
        """Test file system error categorization."""
        fs_errors = [
            Exception("No space left on device"),
            Exception("Disk full"),
            Exception("Permission denied accessing file"),
            Exception("File not found")
        ]
        
        for error in fs_errors:
            result = ErrorCategorizer.categorize_error(error)
            assert result.category == ErrorCategory.FILE_SYSTEM
            assert "File system error" in str(result)
    
    def test_categorize_unknown_error(self):
        """Test unknown error categorization."""
        error = Exception("Some unknown error")
        result = ErrorCategorizer.categorize_error(error)
        
        assert result.category == ErrorCategory.UNKNOWN
        assert "Unknown error" in str(result)
    
    def test_get_max_retries_retryable(self):
        """Test max retries for retryable errors."""
        assert ErrorCategorizer.get_recommended_retry_attempts(ErrorCategory.NETWORK_TIMEOUT) == 3
        assert ErrorCategorizer.get_recommended_retry_attempts(ErrorCategory.SERVICE_UNAVAILABLE) == 3
        assert ErrorCategorizer.get_recommended_retry_attempts(ErrorCategory.RATE_LIMITED) == 5
        assert ErrorCategorizer.get_recommended_retry_attempts(ErrorCategory.TEMPORARY_FAILURE) == 2
    
    def test_get_max_retries_non_retryable(self):
        """Test max retries for non-retryable errors."""
        non_retryable_categories = [
            ErrorCategory.AUTHENTICATION,
            ErrorCategory.DOCKER_DAEMON,
            ErrorCategory.UNKNOWN
        ]
        
        for category in non_retryable_categories:
            max_retries = ErrorCategorizer.get_recommended_retry_attempts(category)
            assert max_retries == 0, f"Category {category} should have 0 max retries"
    
    def test_get_user_guidance(self):
        """Test user guidance messages."""
        guidance_tests = [
            (ErrorCategory.AUTHENTICATION, "AWS credentials"),
            (ErrorCategory.AUTHORIZATION, "access to the ECR repository"),
            (ErrorCategory.DOCKER_DAEMON, "Docker daemon is running"),
            (ErrorCategory.NOT_FOUND, "source image name"),
            (ErrorCategory.INVALID_INPUT, "command arguments"),
            (ErrorCategory.CONFIGURATION, "AWS region"),
            (ErrorCategory.RESOURCE_EXHAUSTED, "disk space"),
            (ErrorCategory.FILE_SYSTEM, "file permissions"),
            (ErrorCategory.NETWORK_TIMEOUT, "network connectivity"),
            (ErrorCategory.SERVICE_UNAVAILABLE, "temporarily unavailable"),
            (ErrorCategory.RATE_LIMITED, "avoid rate limits"),
            (ErrorCategory.TEMPORARY_FAILURE, "Try the operation again"),
            (ErrorCategory.UNKNOWN, "check logs")
        ]
        
        for category, expected_keyword in guidance_tests:
            guidance = ErrorCategorizer.get_user_guidance(category)
            assert expected_keyword in guidance, f"Guidance for {category} should contain '{expected_keyword}'"
            assert len(guidance) > 0, f"Guidance for {category} should not be empty"