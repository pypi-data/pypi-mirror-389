"""Base service class for ECR operations with common functionality."""

from abc import ABC
from typing import Optional

from ..ecr_auth import ECRAuthenticator, ECRAuthenticationError
from ..aws_utils import resolve_aws_region


class BaseECRService(ABC):
    """Abstract base class for ECR services with common initialization and authentication patterns.

    Consolidates the duplicate constructor patterns, ECR authenticator lazy loading,
    and common method implementations found across multiple service classes.
    """

    def __init__(
        self,
        region_name: Optional[str] = None,
        registry_id: Optional[str] = None,
    ):
        """Initialize base ECR service with common parameters.

        Args:
            region_name: AWS region for ECR registry
            registry_id: AWS account ID for ECR registry
        """
        self.region_name = region_name
        self.registry_id = registry_id
        self._ecr_auth: Optional[ECRAuthenticator] = None

    @property
    def ecr_auth(self) -> ECRAuthenticator:
        """Get or create ECR authenticator with lazy initialization.

        This consolidates the duplicate lazy loading pattern found in:
        - AsyncTransferService
        - BuildxTransferService
        - TransferService
        - ECRRepositoryService
        """
        if self._ecr_auth is None:
            self._ecr_auth = ECRAuthenticator(
                region_name=self.region_name, registry_id=self.registry_id
            )
        return self._ecr_auth

    def get_ecr_registry_url(self) -> str:
        """Get ECR registry URL for the configured region and account.

        This consolidates the duplicate implementations found in:
        - AsyncTransferService.get_ecr_registry_url()
        - BuildxTransferService.get_ecr_registry_url()
        - TransferService.get_ecr_registry_url()

        Returns:
            ECR registry URL in format: {account}.dkr.ecr.{region}.amazonaws.com

        Raises:
            ECRAuthenticationError: If unable to determine registry URL
        """
        try:
            region = resolve_aws_region(self.region_name)
        except ValueError as e:
            raise ECRAuthenticationError(str(e)) from e

        registry_id = self.registry_id or self.ecr_auth.registry_id
        if not registry_id:
            raise ECRAuthenticationError("Registry ID not available")
        return f"{registry_id}.dkr.ecr.{region}.amazonaws.com"

    def validate_prerequisites(self) -> bool:
        """Validate that ECR access is working.

        This provides a default implementation that consolidates the common pattern
        found in multiple service classes. Subclasses can override for additional
        validation requirements.

        Returns:
            True if prerequisites are valid, False otherwise
        """
        try:
            # Test ECR authentication
            self.ecr_auth.get_docker_credentials()
            return True
        except ECRAuthenticationError:
            return False
