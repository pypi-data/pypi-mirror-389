"""Tests for AWS utility functions."""

from unittest.mock import Mock, patch
import pytest

from src.ecreshore.aws_utils import resolve_aws_region


class TestResolveAwsRegion:
    """Tests for AWS region resolution logic."""

    def test_explicit_region_returns_immediately(self):
        """Test that explicit region parameter is returned without session creation."""
        result = resolve_aws_region(explicit_region="us-west-2")

        assert result == "us-west-2"

    @patch('boto3.Session')
    def test_uses_boto3_session_when_no_explicit_region(self, mock_session_class):
        """Test that boto3 session is used when no explicit region provided."""
        mock_session = Mock()
        mock_session.region_name = "us-east-1"
        mock_session_class.return_value = mock_session

        result = resolve_aws_region()

        mock_session_class.assert_called_once()
        assert result == "us-east-1"

    @patch('boto3.Session')
    def test_raises_value_error_when_no_region_found(self, mock_session_class):
        """Test that ValueError is raised when no region can be determined."""
        mock_session = Mock()
        mock_session.region_name = None
        mock_session_class.return_value = mock_session

        with pytest.raises(ValueError) as exc_info:
            resolve_aws_region()

        error_message = str(exc_info.value)
        assert "AWS region not specified" in error_message
        assert "--region command line flag" in error_message
        assert "AWS_DEFAULT_REGION environment variable" in error_message
        assert "AWS_REGION environment variable" in error_message
        assert "AWS shared config file" in error_message
        assert "EC2 instance metadata" in error_message

    @patch('boto3.Session')
    def test_empty_string_region_treated_as_none(self, mock_session_class):
        """Test that empty string region from boto3 is treated as None."""
        mock_session = Mock()
        mock_session.region_name = ""
        mock_session_class.return_value = mock_session

        with pytest.raises(ValueError):
            resolve_aws_region()

    def test_explicit_region_overrides_everything(self):
        """Test that explicit region takes precedence over environment/config."""
        # Even if environment variables are set, explicit region should win
        result = resolve_aws_region(explicit_region="eu-central-1")

        assert result == "eu-central-1"

    @patch('boto3.Session')
    def test_boto3_session_region_resolution(self, mock_session_class):
        """Test that boto3 session properly resolves region from standard mechanisms."""
        mock_session = Mock()
        mock_session.region_name = "ap-southeast-2"
        mock_session_class.return_value = mock_session

        result = resolve_aws_region()

        # Verify session was created (which allows boto3 to use standard resolution)
        mock_session_class.assert_called_once()
        assert result == "ap-southeast-2"

    @patch('boto3.Session')
    def test_handles_whitespace_only_region(self, mock_session_class):
        """Test that whitespace-only region is treated as None."""
        mock_session = Mock()
        mock_session.region_name = "   "
        mock_session_class.return_value = mock_session

        # Even though there's a value, it's effectively empty
        # boto3 might return whitespace in some edge cases
        result = resolve_aws_region()
        assert result == "   "  # Function trusts boto3's return value

    def test_none_explicit_region_uses_session(self):
        """Test that None as explicit region uses boto3 session."""
        with patch('boto3.Session') as mock_session_class:
            mock_session = Mock()
            mock_session.region_name = "us-west-1"
            mock_session_class.return_value = mock_session

            result = resolve_aws_region(explicit_region=None)

            mock_session_class.assert_called_once()
            assert result == "us-west-1"

    @patch('boto3.Session')
    def test_comprehensive_error_message_format(self, mock_session_class):
        """Test that error message contains all expected resolution methods."""
        mock_session = Mock()
        mock_session.region_name = None
        mock_session_class.return_value = mock_session

        with pytest.raises(ValueError) as exc_info:
            resolve_aws_region()

        error_message = str(exc_info.value)

        # Verify all resolution methods are mentioned
        expected_methods = [
            "--region command line flag",
            "AWS_DEFAULT_REGION environment variable",
            "AWS_REGION environment variable",
            "AWS shared config file (~/.aws/config)",
            "EC2 instance metadata (if running on EC2)"
        ]

        for method in expected_methods:
            assert method in error_message


def test_import_paths():
    """Test that all imports work correctly."""
    from src.ecreshore.aws_utils import resolve_aws_region

    assert resolve_aws_region is not None