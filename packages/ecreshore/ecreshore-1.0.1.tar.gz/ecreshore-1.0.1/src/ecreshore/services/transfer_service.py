"""Core transfer service for container image operations."""

import logging
from dataclasses import dataclass, field
from typing import List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .retry_service import RetryService

from ..ecr_auth import ECRAuthenticationError
from .base_service import BaseECRService
from .platform_models import Platform


# DockerClientError for backward compatibility (sync docker client removed)
class DockerClientError(Exception):
    """Raised when Docker operations fail."""

    pass


logger = logging.getLogger(__name__)


@dataclass
class TransferRequest:
    """Request for a single image transfer operation."""

    source_image: str
    source_tag: str
    target_repository: str
    target_tag: str
    verify_digest: bool = True
    preserve_architectures: bool = False
    target_platforms: Optional[List[str]] = None
    auto_detect_architectures: bool = True
    skip_if_present: bool = True


@dataclass
class TransferResult:
    """Result of a transfer operation."""

    request: TransferRequest
    success: bool
    error_message: Optional[str] = None
    source_digest: Optional[str] = None
    target_digest: Optional[str] = None
    platforms_copied: List[Platform] = field(default_factory=list)
    transfer_method: str = "docker_api"
    skipped: bool = False
    skip_reason: Optional[str] = None
    retry_count: int = 0


class TransferService(BaseECRService):
    """Service for managing container image transfers to ECR."""

    def __init__(
        self,
        region_name: Optional[str] = None,
        registry_id: Optional[str] = None,
        enable_retry: bool = True,
        max_retry_attempts: Optional[int] = None,
    ):
        """Initialize transfer service.

        Args:
            region_name: AWS region for ECR registry
            registry_id: AWS account ID for ECR registry
            enable_retry: Whether to enable automatic retries for transfers
            max_retry_attempts: Maximum retry attempts (uses service default if None)
        """
        super().__init__(region_name, registry_id)
        self.enable_retry = enable_retry
        self.max_retry_attempts = max_retry_attempts

        self._docker_client: Optional[object] = None  # Kept for compatibility
        self._retry_service: Optional["RetryService"] = None

    @property
    def docker_client(self):
        """Get or create Docker client - minimal implementation for compatibility."""
        # Note: Docker client functionality removed in async migration
        # This property maintained for backward compatibility only
        raise DockerClientError(
            "Docker client operations require async implementation - use AsyncTransferService"
        )

    @property
    def retry_service(self) -> "RetryService":
        """Get or create retry service."""
        if self._retry_service is None:
            from .retry_service import create_transfer_retry_service

            max_attempts = self.max_retry_attempts or 3
            self._retry_service = create_transfer_retry_service(max_attempts)
        return self._retry_service

    def validate_prerequisites(self) -> bool:
        """Validate that all prerequisites are met for transfers.

        Returns:
            True if prerequisites are valid
        """
        try:
            # Use base class validation and add Docker-specific checks
            if not super().validate_prerequisites():
                logger.error("ECR authentication failed")
                return False

            return True

        except (DockerClientError, ECRAuthenticationError) as e:
            logger.error(f"Prerequisites validation failed: {e}")
            return False

    def transfer_image(self, request: TransferRequest) -> TransferResult:
        """Transfer a single image to ECR with automatic retry logic.

        Args:
            request: Transfer request details

        Returns:
            Transfer result with success status and details
        """
        if self.enable_retry:
            return self.retry_service.transfer_image_with_retry(
                self, request, self.max_retry_attempts
            )
        else:
            return self._transfer_image_once(request)

    def _transfer_image_once(self, request: TransferRequest) -> TransferResult:
        """Transfer a single image to ECR without retry logic.

        Note: Docker operations have been moved to AsyncTransferService.
        This method is maintained for compatibility but will raise an error.

        Args:
            request: Transfer request details

        Returns:
            Transfer result with success status and details
        """
        # Docker operations require async implementation
        return TransferResult(
            request=request,
            success=False,
            error_message="Docker client operations require async implementation - use AsyncTransferService",
        )
