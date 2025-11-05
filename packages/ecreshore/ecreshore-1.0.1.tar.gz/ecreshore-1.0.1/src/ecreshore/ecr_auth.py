"""AWS ECR Authentication and Token Management."""

import base64
import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Optional, Tuple

import boto3
from botocore.exceptions import BotoCoreError, ClientError


logger = logging.getLogger(__name__)


class ECRAuthenticationError(Exception):
    """Raised when ECR authentication fails."""

    pass


class ECRAuthenticator:
    """Handles AWS ECR authentication and token management with auto-refresh."""

    def __init__(
        self, region_name: Optional[str] = None, registry_id: Optional[str] = None
    ):
        """Initialize ECR authenticator.

        Args:
            region_name: AWS region for ECR registry. Uses default if None.
            registry_id: AWS account ID. Uses current account if None.
        """
        self.region_name = region_name

        # Auto-detect account ID if not provided
        if registry_id is None:
            try:
                sts_client = boto3.client("sts", region_name=region_name)
                registry_id = sts_client.get_caller_identity()["Account"]
                logger.debug(f"Auto-detected registry ID: {registry_id}")
            except Exception as e:
                logger.warning(f"Failed to auto-detect account ID: {e}")
                registry_id = None

        self.registry_id = registry_id
        self._ecr_client: Optional[Any] = None
        self._cached_token: Optional[str] = None
        self._cached_username: Optional[str] = None
        self._token_expires_at: Optional[datetime] = None

    @property
    def ecr_client(self) -> Any:
        """Get or create ECR client using default credential chain."""
        if self._ecr_client is None:
            try:
                self._ecr_client = boto3.client("ecr", region_name=self.region_name)
            except Exception as e:
                raise ECRAuthenticationError(f"Failed to create ECR client: {e}")
        return self._ecr_client

    def _is_token_expired(self) -> bool:
        """Check if current token is expired or will expire soon."""
        if self._token_expires_at is None:
            return True
        # Refresh 5 minutes before expiry
        return datetime.now(timezone.utc) >= (
            self._token_expires_at - timedelta(minutes=5)
        )

    def _fetch_authorization_token(self) -> Tuple[str, str, datetime]:
        """Fetch new authorization token from ECR.

        Returns:
            Tuple of (username, password, expiry_datetime)
        """
        try:
            # Call ECR API with or without registryIds parameter
            if self.registry_id:
                response = self.ecr_client.get_authorization_token(
                    registryIds=[self.registry_id]
                )
            else:
                response = self.ecr_client.get_authorization_token()

            auth_data = response["authorizationData"][0]
            token = auth_data["authorizationToken"]
            expires_at = auth_data["expiresAt"]

            # Decode base64 token to get username:password
            decoded_token = base64.b64decode(token).decode("utf-8")
            username, password = decoded_token.split(":", 1)

            logger.info(f"Retrieved ECR token, expires at {expires_at}")
            return username, password, expires_at

        except (ClientError, BotoCoreError) as e:
            error_msg = str(e)
            if "registryIds" in error_msg or "Invalid length" in error_msg:
                raise ECRAuthenticationError(
                    "ECR authentication failed: registry ID required. "
                    "Auto-detection failed - try specifying --registry-id explicitly."
                )
            raise ECRAuthenticationError(f"Failed to get ECR authorization token: {e}")
        except (ValueError, IndexError, UnicodeDecodeError) as e:
            raise ECRAuthenticationError(f"Invalid ECR token format: {e}")
        except Exception as e:
            raise ECRAuthenticationError(f"Failed to get ECR authorization token: {e}")

    def get_docker_credentials(self) -> Tuple[str, str]:
        """Get Docker registry credentials for ECR.

        Returns:
            Tuple of (username, password) for Docker registry authentication
        """
        if self._is_token_expired():
            logger.debug("ECR token expired or missing, fetching new token")
            username, password, expires_at = self._fetch_authorization_token()
            self._cached_token = password
            self._cached_username = username
            self._token_expires_at = expires_at
            return username, password

        # Use cached token and username
        logger.debug("Using cached ECR token")
        if self._cached_token is None or self._cached_username is None:
            raise ECRAuthenticationError("Cached credentials are None")
        return self._cached_username, self._cached_token

    def get_registry_url(self) -> str:
        """Get ECR registry URL for this region and account.

        Returns:
            ECR registry URL in format: {account}.dkr.ecr.{region}.amazonaws.com
        """
        if not self.registry_id:
            # Get current account ID from STS
            try:
                sts_client = boto3.client("sts", region_name=self.region_name)
                account_id = sts_client.get_caller_identity()["Account"]
            except Exception as e:
                raise ECRAuthenticationError(f"Failed to get AWS account ID: {e}")
        else:
            account_id = self.registry_id

        region = self.region_name or boto3.Session().region_name
        if not region:
            raise ECRAuthenticationError(
                "AWS region not specified and cannot be determined"
            )

        return f"{account_id}.dkr.ecr.{region}.amazonaws.com"

    def validate_credentials(self) -> bool:
        """Validate that AWS credentials work with ECR.

        Returns:
            True if credentials are valid, False otherwise
        """
        try:
            self.get_docker_credentials()
            return True
        except ECRAuthenticationError:
            return False
