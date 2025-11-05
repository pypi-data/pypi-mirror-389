"""Enhanced error aggregation and reporting for batch operations."""

import logging
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum

from .error_handler import ErrorCategorizer, ErrorCategory, CategorizedError

logger = logging.getLogger(__name__)


@dataclass
class TransferError:
    """Individual transfer error with context."""

    transfer_id: str
    source_image: str
    target_repository: str
    source_tag: str
    target_tag: str
    error: Exception
    categorized_error: CategorizedError
    retry_count: int = 0
    timestamp: Optional[float] = None


@dataclass
class ErrorSummary:
    """Summary of errors by category."""

    category: ErrorCategory
    count: int
    errors: List[TransferError] = field(default_factory=list)
    user_guidance: str = ""
    is_retryable: bool = False
    requires_user_action: bool = False


class BatchErrorAggregator:
    """Aggregates and categorizes batch transfer errors for clean reporting."""

    def __init__(self):
        """Initialize batch error aggregator."""
        self.transfer_errors: Dict[str, TransferError] = {}
        self.error_categories: Dict[ErrorCategory, List[TransferError]] = defaultdict(
            list
        )
        self.total_transfers: int = 0
        self.successful_transfers: int = 0
        self.failed_transfers: int = 0
        self.skipped_transfers: int = 0

    def set_transfer_counts(
        self, total: int, successful: int, failed: int, skipped: int = 0
    ) -> None:
        """Set transfer count statistics.

        Args:
            total: Total number of transfers
            successful: Number of successful transfers
            failed: Number of failed transfers
            skipped: Number of skipped transfers
        """
        self.total_transfers = total
        self.successful_transfers = successful
        self.failed_transfers = failed
        self.skipped_transfers = skipped

    def add_transfer_error(
        self,
        transfer_id: str,
        source_image: str,
        target_repository: str,
        source_tag: str,
        target_tag: str,
        error: Exception,
        retry_count: int = 0,
        timestamp: Optional[float] = None,
    ) -> None:
        """Add a transfer error to the aggregator.

        Args:
            transfer_id: Unique transfer identifier
            source_image: Source image name
            target_repository: Target repository name
            source_tag: Source image tag
            target_tag: Target image tag
            error: Exception that occurred
            retry_count: Number of retries attempted
            timestamp: When the error occurred
        """
        # Categorize the error using existing categorizer
        categorized_error = ErrorCategorizer.categorize_error(error)

        transfer_error = TransferError(
            transfer_id=transfer_id,
            source_image=source_image,
            target_repository=target_repository,
            source_tag=source_tag,
            target_tag=target_tag,
            error=error,
            categorized_error=categorized_error,
            retry_count=retry_count,
            timestamp=timestamp,
        )

        # Store the error
        self.transfer_errors[transfer_id] = transfer_error
        self.error_categories[categorized_error.category].append(transfer_error)

    def get_error_summary(self) -> Dict[ErrorCategory, ErrorSummary]:
        """Get summary of errors grouped by category.

        Returns:
            Dictionary mapping error categories to summaries
        """
        summaries = {}

        for category, errors in self.error_categories.items():
            if not errors:
                continue

            summary = ErrorSummary(
                category=category,
                count=len(errors),
                errors=errors,
                user_guidance=ErrorCategorizer.get_user_guidance(category),
                is_retryable=category
                in {
                    ErrorCategory.NETWORK_TIMEOUT,
                    ErrorCategory.SERVICE_UNAVAILABLE,
                    ErrorCategory.RATE_LIMITED,
                    ErrorCategory.TEMPORARY_FAILURE,
                },
                requires_user_action=category
                in {
                    ErrorCategory.AUTHENTICATION,
                    ErrorCategory.AUTHORIZATION,
                    ErrorCategory.INVALID_INPUT,
                    ErrorCategory.CONFIGURATION,
                    ErrorCategory.DOCKER_DAEMON,
                    ErrorCategory.NOT_FOUND,
                },
            )
            summaries[category] = summary

        return summaries

    def get_actionable_recommendations(self) -> List[str]:
        """Get actionable recommendations for resolving errors.

        Returns:
            List of specific recommendations based on error patterns
        """
        recommendations = []
        error_summary = self.get_error_summary()

        # Check for common patterns and provide specific guidance
        if ErrorCategory.NOT_FOUND in error_summary:
            not_found_errors = error_summary[ErrorCategory.NOT_FOUND].errors
            missing_repos = {error.target_repository for error in not_found_errors}
            if missing_repos:
                repo_list = ", ".join(sorted(missing_repos))
                recommendations.append(f"Create missing ECR repositories: {repo_list}")
                recommendations.append(
                    "Use 'aws ecr create-repository --repository-name <name>' or enable auto-creation"
                )

        if ErrorCategory.AUTHENTICATION in error_summary:
            recommendations.append(
                "Verify AWS credentials: run 'aws sts get-caller-identity' to check authentication"
            )
            recommendations.append(
                "Ensure your credentials have ECR permissions (ecr:GetAuthorizationToken, ecr:BatchCheckLayerAvailability, etc.)"
            )

        if ErrorCategory.AUTHORIZATION in error_summary:
            recommendations.append("Check ECR repository permissions and IAM policies")
            recommendations.append(
                "Verify your AWS account has access to the target registry"
            )

        if ErrorCategory.DOCKER_DAEMON in error_summary:
            recommendations.append(
                "Ensure Docker daemon is running: 'sudo systemctl start docker'"
            )
            recommendations.append("Check Docker socket permissions for your user")

        if ErrorCategory.NETWORK_TIMEOUT in error_summary:
            recommendations.append("Check network connectivity and try again")
            recommendations.append(
                "Consider increasing timeout values if on slow connection"
            )

        # Pattern-based recommendations
        if self._has_high_failure_rate():
            recommendations.append(
                "High failure rate detected - consider running with --dry-run first to validate configuration"
            )

        if self._has_many_retries():
            recommendations.append(
                "Multiple retries detected - check network stability and service availability"
            )

        return recommendations

    def get_error_statistics(self) -> Dict[str, Any]:
        """Get detailed error statistics.

        Returns:
            Dictionary with error statistics
        """
        error_summary = self.get_error_summary()

        stats = {
            "total_errors": len(self.transfer_errors),
            "unique_error_categories": len(error_summary),
            "retryable_errors": sum(
                summary.count
                for summary in error_summary.values()
                if summary.is_retryable
            ),
            "user_action_required": sum(
                summary.count
                for summary in error_summary.values()
                if summary.requires_user_action
            ),
            "category_breakdown": {
                category.value: summary.count
                for category, summary in error_summary.items()
            },
            "total_retries": sum(
                error.retry_count for error in self.transfer_errors.values()
            ),
            "failure_rate": (
                self.failed_transfers / self.total_transfers * 100
                if self.total_transfers > 0
                else 0
            ),
        }

        return stats

    def get_most_common_errors(self, limit: int = 3) -> List[Tuple[ErrorCategory, int]]:
        """Get the most common error categories.

        Args:
            limit: Maximum number of categories to return

        Returns:
            List of (category, count) tuples sorted by frequency
        """
        error_summary = self.get_error_summary()
        sorted_errors = sorted(
            error_summary.items(), key=lambda x: x[1].count, reverse=True
        )
        return [
            (category, summary.count) for category, summary in sorted_errors[:limit]
        ]

    def should_suggest_retry(self) -> bool:
        """Determine if retrying the batch operation might be successful.

        Returns:
            True if retry is recommended based on error types
        """
        error_summary = self.get_error_summary()

        # If all errors are retryable, suggest retry
        retryable_count = sum(
            summary.count for summary in error_summary.values() if summary.is_retryable
        )

        total_errors = len(self.transfer_errors)
        if total_errors == 0:
            return False

        # Suggest retry if >75% of errors are retryable
        return (retryable_count / total_errors) > 0.75

    def _has_high_failure_rate(self) -> bool:
        """Check if there's a high failure rate."""
        if self.total_transfers == 0:
            return False
        return (self.failed_transfers / self.total_transfers) > 0.5

    def _has_many_retries(self) -> bool:
        """Check if there were many retry attempts."""
        total_retries = sum(
            error.retry_count for error in self.transfer_errors.values()
        )
        return total_retries > (len(self.transfer_errors) * 2)

    def clear(self) -> None:
        """Clear all stored errors and reset counters."""
        self.transfer_errors.clear()
        self.error_categories.clear()
        self.total_transfers = 0
        self.successful_transfers = 0
        self.failed_transfers = 0
        self.skipped_transfers = 0
