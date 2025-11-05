"""Tests for TransferService."""

import pytest
from unittest.mock import Mock, patch, MagicMock

from src.ecreshore.services.transfer_service import (
    TransferService, TransferRequest, TransferResult, DockerClientError
)
from src.ecreshore.ecr_auth import ECRAuthenticationError


class TestTransferRequest:
    def test_transfer_request_creation(self):
        """Test TransferRequest dataclass creation."""
        request = TransferRequest(
            source_image="nginx",
            source_tag="latest",
            target_repository="my-nginx",
            target_tag="v1.0"
        )
        
        assert request.source_image == "nginx"
        assert request.source_tag == "latest"
        assert request.target_repository == "my-nginx"
        assert request.target_tag == "v1.0"
        assert request.verify_digest is True
    
    def test_transfer_request_defaults(self):
        """Test TransferRequest with default values."""
        request = TransferRequest(
            source_image="nginx",
            source_tag="latest",
            target_repository="my-nginx",
            target_tag="v1.0",
            verify_digest=False
        )
        
        assert request.verify_digest is False


class TestTransferResult:
    def test_transfer_result_success(self):
        """Test successful TransferResult."""
        request = TransferRequest("nginx", "latest", "my-nginx", "v1.0")
        result = TransferResult(
            request=request,
            success=True,
            source_digest="abc123",
            target_digest="abc123"
        )
        
        assert result.success is True
        assert result.error_message is None
        assert result.source_digest == "abc123"
        assert result.target_digest == "abc123"
    
    def test_transfer_result_failure(self):
        """Test failed TransferResult."""
        request = TransferRequest("nginx", "latest", "my-nginx", "v1.0")
        result = TransferResult(
            request=request,
            success=False,
            error_message="Connection failed"
        )
        
        assert result.success is False
        assert result.error_message == "Connection failed"
        assert result.source_digest is None


class TestTransferService:
    def test_init_default_values(self):
        """Test TransferService initialization with defaults."""
        service = TransferService()
        
        assert service.region_name is None
        assert service.registry_id is None
        assert service._docker_client is None
        assert service._ecr_auth is None
    
    def test_init_with_values(self):
        """Test TransferService initialization with values."""
        service = TransferService(region_name="us-west-2", registry_id="123456789012")
        
        assert service.region_name == "us-west-2"
        assert service.registry_id == "123456789012"
    
    def test_docker_client_property_raises_error(self):
        """Test docker_client property raises async migration error."""
        service = TransferService()
        
        with pytest.raises(DockerClientError, match="Docker client operations require async implementation - use AsyncTransferService"):
            service.docker_client
    
    @patch('src.ecreshore.services.base_service.ECRAuthenticator')
    def test_ecr_auth_property(self, mock_ecr_auth):
        """Test ecr_auth property lazy loading."""
        service = TransferService(region_name="us-west-2", registry_id="123456789012")
        
        # First access creates authenticator
        auth1 = service.ecr_auth
        mock_ecr_auth.assert_called_once_with(
            region_name="us-west-2",
            registry_id="123456789012"
        )
        
        # Second access returns same authenticator
        auth2 = service.ecr_auth
        assert auth1 is auth2
    
    @patch('src.ecreshore.services.base_service.ECRAuthenticator')
    def test_validate_prerequisites_success(self, mock_ecr_auth_class):
        """Test successful prerequisites validation."""
        mock_ecr_auth = Mock()
        mock_ecr_auth.get_docker_credentials.return_value = {'username': 'test', 'password': 'test'}
        mock_ecr_auth_class.return_value = mock_ecr_auth

        service = TransferService()
        result = service.validate_prerequisites()

        assert result is True
        mock_ecr_auth.get_docker_credentials.assert_called_once()
    
    @patch('src.ecreshore.services.base_service.ECRAuthenticator')
    def test_validate_prerequisites_ecr_failure(self, mock_ecr_auth_class):
        """Test prerequisites validation with ECR failure."""
        mock_ecr_auth = Mock()
        mock_ecr_auth.get_docker_credentials.side_effect = ECRAuthenticationError("Auth failed")
        mock_ecr_auth_class.return_value = mock_ecr_auth

        service = TransferService()
        result = service.validate_prerequisites()

        assert result is False
    
    @patch('src.ecreshore.services.base_service.ECRAuthenticator')
    def test_get_ecr_registry_url(self, mock_ecr_auth_class):
        """Test ECR registry URL retrieval."""
        mock_ecr_auth = Mock()
        mock_ecr_auth.registry_id = "123456789012"
        mock_ecr_auth_class.return_value = mock_ecr_auth

        service = TransferService(region_name="us-west-2")
        url = service.get_ecr_registry_url()

        assert url == "123456789012.dkr.ecr.us-west-2.amazonaws.com"
    
    def test_transfer_image_async_migration_error(self):
        """Test image transfer returns async migration error."""
        service = TransferService()
        request = TransferRequest("nginx", "latest", "my-nginx", "v1.0")
        result = service.transfer_image(request)
        
        assert result.success is False
        assert "Docker client operations require async implementation - use AsyncTransferService" in result.error_message
    
    def test_transfer_image_with_retry_async_migration_error(self):
        """Test image transfer with retry returns async migration error."""
        service = TransferService(enable_retry=True)
        request = TransferRequest("nginx", "latest", "my-nginx", "v1.0")
        result = service.transfer_image(request)
        
        assert result.success is False
        assert "Docker client operations require async implementation - use AsyncTransferService" in result.error_message
    
    def test_transfer_image_without_retry_async_migration_error(self):
        """Test image transfer without retry returns async migration error."""
        service = TransferService(enable_retry=False)
        request = TransferRequest("nginx", "latest", "my-nginx", "v1.0")
        result = service.transfer_image(request)
        
        assert result.success is False
        assert "Docker client operations require async implementation - use AsyncTransferService" in result.error_message