"""Tests for ECR authentication module."""

import base64
from datetime import datetime, timedelta, timezone
from unittest.mock import Mock, patch, MagicMock, call
import pytest

from src.ecreshore.ecr_auth import ECRAuthenticator, ECRAuthenticationError


class TestECRAuthenticator:
    """Test ECR authentication functionality."""

    @patch('boto3.client')
    def test_init_default_values(self, mock_boto_client):
        """Test ECRAuthenticator initialization with defaults."""
        # Mock STS client for auto-detection
        mock_sts_client = Mock()
        mock_sts_client.get_caller_identity.return_value = {'Account': '123456789012'}
        mock_boto_client.return_value = mock_sts_client

        auth = ECRAuthenticator()
        assert auth.region_name is None
        # registry_id should be auto-detected now, not None
        assert auth.registry_id is not None
        assert len(auth.registry_id) == 12  # AWS account IDs are 12 digits
        assert auth._cached_token is None
        assert auth._token_expires_at is None

    def test_init_with_values(self):
        """Test ECRAuthenticator initialization with provided values."""
        auth = ECRAuthenticator(region_name="us-west-2", registry_id="123456789012")
        assert auth.region_name == "us-west-2"
        assert auth.registry_id == "123456789012"

    @patch('boto3.client')
    def test_ecr_client_creation(self, mock_boto_client):
        """Test ECR client creation."""
        # Mock STS client for auto-detection
        mock_sts_client = Mock()
        mock_sts_client.get_caller_identity.return_value = {'Account': '123456789012'}
        
        # Mock ECR client  
        mock_ecr_client = Mock()
        
        # Configure boto3.client to return different mocks based on service
        def mock_client_side_effect(service, **kwargs):
            if service == 'sts':
                return mock_sts_client
            elif service == 'ecr':
                return mock_ecr_client
            return Mock()
        
        mock_boto_client.side_effect = mock_client_side_effect
        
        auth = ECRAuthenticator(region_name="us-east-1")
        client = auth.ecr_client
        
        assert client == mock_ecr_client
        # Verify both STS and ECR clients were created
        expected_calls = [
            call('sts', region_name='us-east-1'),
            call('ecr', region_name='us-east-1')
        ]
        mock_boto_client.assert_has_calls(expected_calls)

    @patch('boto3.client')
    def test_ecr_client_creation_failure(self, mock_boto_client):
        """Test ECR client creation failure."""
        mock_boto_client.side_effect = Exception("AWS error")
        
        auth = ECRAuthenticator()
        with pytest.raises(ECRAuthenticationError, match="Failed to create ECR client"):
            auth.ecr_client

    @patch('boto3.client')
    def test_is_token_expired_no_token(self, mock_boto_client):
        """Test token expiry check when no token exists."""
        # Mock STS client for auto-detection
        mock_sts_client = Mock()
        mock_sts_client.get_caller_identity.return_value = {'Account': '123456789012'}
        mock_boto_client.return_value = mock_sts_client

        auth = ECRAuthenticator()
        assert auth._is_token_expired() is True

    @patch('boto3.client')
    def test_is_token_expired_with_valid_token(self, mock_boto_client):
        """Test token expiry check with valid token."""
        # Mock STS client for auto-detection
        mock_sts_client = Mock()
        mock_sts_client.get_caller_identity.return_value = {'Account': '123456789012'}
        mock_boto_client.return_value = mock_sts_client

        auth = ECRAuthenticator()
        auth._token_expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
        assert auth._is_token_expired() is False

    @patch('boto3.client')
    def test_is_token_expired_with_expired_token(self, mock_boto_client):
        """Test token expiry check with expired token."""
        # Mock STS client for auto-detection
        mock_sts_client = Mock()
        mock_sts_client.get_caller_identity.return_value = {'Account': '123456789012'}
        mock_boto_client.return_value = mock_sts_client

        auth = ECRAuthenticator()
        auth._token_expires_at = datetime.now(timezone.utc) - timedelta(hours=1)
        assert auth._is_token_expired() is True

    @patch('boto3.client')
    def test_is_token_expired_near_expiry(self, mock_boto_client):
        """Test token expiry check when token expires soon."""
        # Mock STS client for auto-detection
        mock_sts_client = Mock()
        mock_sts_client.get_caller_identity.return_value = {'Account': '123456789012'}
        mock_boto_client.return_value = mock_sts_client

        auth = ECRAuthenticator()
        auth._token_expires_at = datetime.now(timezone.utc) + timedelta(minutes=3)
        assert auth._is_token_expired() is True  # Should refresh 5 min before expiry

    @patch('boto3.client')
    def test_fetch_authorization_token_success(self, mock_boto_client):
        """Test successful token fetch."""
        mock_client = Mock()
        mock_boto_client.return_value = mock_client
        
        # Create base64 encoded token
        token_data = "AWS:test-password"
        encoded_token = base64.b64encode(token_data.encode()).decode()
        expires_at = datetime.now(timezone.utc) + timedelta(hours=12)
        
        mock_client.get_authorization_token.return_value = {
            'authorizationData': [{
                'authorizationToken': encoded_token,
                'expiresAt': expires_at
            }]
        }
        
        auth = ECRAuthenticator()
        username, password, expiry = auth._fetch_authorization_token()
        
        assert username == "AWS"
        assert password == "test-password"
        assert expiry == expires_at

    @patch('boto3.client')
    def test_fetch_authorization_token_with_registry_id(self, mock_boto_client):
        """Test token fetch with specific registry ID."""
        mock_client = Mock()
        mock_boto_client.return_value = mock_client
        
        token_data = "AWS:test-password"
        encoded_token = base64.b64encode(token_data.encode()).decode()
        expires_at = datetime.now(timezone.utc) + timedelta(hours=12)
        
        mock_client.get_authorization_token.return_value = {
            'authorizationData': [{
                'authorizationToken': encoded_token,
                'expiresAt': expires_at
            }]
        }
        
        auth = ECRAuthenticator(registry_id="123456789012")
        auth._fetch_authorization_token()
        
        mock_client.get_authorization_token.assert_called_once_with(
            registryIds=['123456789012']
        )

    @patch('boto3.client')
    def test_fetch_authorization_token_client_error(self, mock_boto_client):
        """Test token fetch with client error."""
        mock_client = Mock()
        mock_boto_client.return_value = mock_client
        mock_client.get_authorization_token.side_effect = Exception("AWS API error")
        
        auth = ECRAuthenticator()
        with pytest.raises(ECRAuthenticationError, match="Failed to get ECR authorization token"):
            auth._fetch_authorization_token()

    @patch('boto3.client')
    def test_fetch_authorization_token_invalid_format(self, mock_boto_client):
        """Test token fetch with invalid token format."""
        mock_client = Mock()
        mock_boto_client.return_value = mock_client
        
        # Invalid base64 token
        mock_client.get_authorization_token.return_value = {
            'authorizationData': [{
                'authorizationToken': 'invalid-token',
                'expiresAt': datetime.now(timezone.utc)
            }]
        }
        
        auth = ECRAuthenticator()
        with pytest.raises(ECRAuthenticationError, match="Invalid ECR token format"):
            auth._fetch_authorization_token()

    @patch('boto3.client')
    @patch.object(ECRAuthenticator, '_fetch_authorization_token')
    def test_get_docker_credentials_fresh_token(self, mock_fetch, mock_boto_client):
        """Test getting Docker credentials with fresh token."""
        # Mock STS client for auto-detection
        mock_sts_client = Mock()
        mock_sts_client.get_caller_identity.return_value = {'Account': '123456789012'}
        mock_boto_client.return_value = mock_sts_client

        expires_at = datetime.now(timezone.utc) + timedelta(hours=12)
        mock_fetch.return_value = ("AWS", "test-password", expires_at)

        auth = ECRAuthenticator()
        username, password = auth.get_docker_credentials()
        
        assert username == "AWS"
        assert password == "test-password"
        assert auth._cached_token == "test-password"
        assert auth._token_expires_at == expires_at

    @patch('boto3.client')
    @patch.object(ECRAuthenticator, '_fetch_authorization_token')
    def test_get_docker_credentials_cached_token(self, mock_fetch, mock_boto_client):
        """Test getting Docker credentials with cached token."""
        # Mock STS client for auto-detection
        mock_sts_client = Mock()
        mock_sts_client.get_caller_identity.return_value = {'Account': '123456789012'}
        mock_boto_client.return_value = mock_sts_client

        # Set up cached token and username
        auth = ECRAuthenticator()
        auth._cached_token = "cached-password"
        auth._cached_username = "AWS"
        auth._token_expires_at = datetime.now(timezone.utc) + timedelta(hours=6)

        username, password = auth.get_docker_credentials()

        assert username == "AWS"
        assert password == "cached-password"  # Should use cached password
        # Mock should NOT be called when credentials are cached
        mock_fetch.assert_not_called()

    @patch('boto3.client')
    @patch('boto3.Session')
    def test_get_registry_url_with_region(self, mock_session, mock_boto_client):
        """Test registry URL generation with provided region."""
        mock_sts_client = Mock()
        mock_boto_client.return_value = mock_sts_client
        mock_sts_client.get_caller_identity.return_value = {'Account': '123456789012'}
        
        auth = ECRAuthenticator(region_name="us-west-2")
        url = auth.get_registry_url()
        
        assert url == "123456789012.dkr.ecr.us-west-2.amazonaws.com"

    @patch('boto3.client')
    def test_get_registry_url_with_registry_id(self, mock_boto_client):
        """Test registry URL generation with provided registry ID."""
        auth = ECRAuthenticator(region_name="eu-west-1", registry_id="987654321098")
        url = auth.get_registry_url()
        
        assert url == "987654321098.dkr.ecr.eu-west-1.amazonaws.com"
        # Should not call STS when registry_id is provided
        mock_boto_client.assert_not_called()

    @patch('boto3.client')
    @patch('boto3.Session')
    def test_get_registry_url_default_region(self, mock_session, mock_boto_client):
        """Test registry URL generation with default region."""
        mock_sts_client = Mock()
        mock_boto_client.return_value = mock_sts_client
        mock_sts_client.get_caller_identity.return_value = {'Account': '123456789012'}
        
        mock_session.return_value.region_name = "us-east-1"
        
        auth = ECRAuthenticator()
        url = auth.get_registry_url()
        
        assert url == "123456789012.dkr.ecr.us-east-1.amazonaws.com"

    @patch('boto3.client')
    @patch('boto3.Session')
    def test_get_registry_url_no_region(self, mock_session, mock_boto_client):
        """Test registry URL generation with no region available."""
        mock_session.return_value.region_name = None
        
        auth = ECRAuthenticator()
        with pytest.raises(ECRAuthenticationError, match="AWS region not specified"):
            auth.get_registry_url()

    @patch('boto3.client')
    def test_get_registry_url_sts_error(self, mock_boto_client):
        """Test registry URL generation with STS error."""
        mock_sts_client = Mock()
        mock_boto_client.return_value = mock_sts_client
        mock_sts_client.get_caller_identity.side_effect = Exception("STS error")
        
        auth = ECRAuthenticator(region_name="us-east-1")
        with pytest.raises(ECRAuthenticationError, match="Failed to get AWS account ID"):
            auth.get_registry_url()

    @patch('boto3.client')
    @patch.object(ECRAuthenticator, 'get_docker_credentials')
    def test_validate_credentials_success(self, mock_get_creds, mock_boto_client):
        """Test credential validation success."""
        # Mock STS client for auto-detection
        mock_sts_client = Mock()
        mock_sts_client.get_caller_identity.return_value = {'Account': '123456789012'}
        mock_boto_client.return_value = mock_sts_client

        mock_get_creds.return_value = ("AWS", "password")

        auth = ECRAuthenticator()
        assert auth.validate_credentials() is True

    @patch('boto3.client')
    @patch.object(ECRAuthenticator, 'get_docker_credentials')
    def test_validate_credentials_failure(self, mock_get_creds, mock_boto_client):
        """Test credential validation failure."""
        # Mock STS client for auto-detection
        mock_sts_client = Mock()
        mock_sts_client.get_caller_identity.return_value = {'Account': '123456789012'}
        mock_boto_client.return_value = mock_sts_client

        mock_get_creds.side_effect = ECRAuthenticationError("Auth failed")

        auth = ECRAuthenticator()
        assert auth.validate_credentials() is False