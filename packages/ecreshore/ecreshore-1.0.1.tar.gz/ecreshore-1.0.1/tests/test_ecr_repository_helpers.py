"""Tests for ECR repository service helper functions.

Following the Extract Method pattern: Test extracted pure functions
and service helpers independently from the main service orchestration.
"""

from datetime import datetime
from unittest.mock import Mock, patch

import pytest
from botocore.exceptions import ClientError

from ecreshore.ecr_auth import ECRAuthenticationError
from ecreshore.services.ecr_repository import (
    ECRImage,
    _build_ecr_image,
    _handle_list_images_error,
    _matches_tag_filter,
)


# ============================================================================
# Test _matches_tag_filter (Pure Function)
# ============================================================================


class TestMatchesTagFilter:
    """Test tag and digest filtering logic."""

    def test_matches_tag_case_insensitive(self):
        """Tag matching should be case-insensitive."""
        matches, matching_tags, has_digest = _matches_tag_filter(
            ["v1.0.0", "latest", "PROD"],
            "sha256:abc123",
            "prod",
        )

        assert matches is True
        assert matching_tags == ["PROD"]
        assert has_digest is False

    def test_matches_digest_case_insensitive(self):
        """Digest matching should be case-insensitive."""
        matches, matching_tags, has_digest = _matches_tag_filter(
            ["v1.0.0"],
            "sha256:ABC123DEF456",
            "abc123",
        )

        assert matches is True
        assert matching_tags == []
        assert has_digest is True

    def test_matches_both_tag_and_digest(self):
        """When both tag and digest match, both should be reported."""
        matches, matching_tags, has_digest = _matches_tag_filter(
            ["v1.0.0", "test"],
            "sha256:test123",
            "test",
        )

        assert matches is True
        assert matching_tags == ["test"]
        assert has_digest is True

    def test_no_match_returns_false(self):
        """When neither tag nor digest matches, should return False."""
        matches, matching_tags, has_digest = _matches_tag_filter(
            ["v1.0.0", "latest"],
            "sha256:abc123",
            "production",
        )

        assert matches is False
        assert matching_tags == []
        assert has_digest is False

    def test_partial_tag_match(self):
        """Tag filter should match partial strings."""
        matches, matching_tags, has_digest = _matches_tag_filter(
            ["v1.0.0", "release-candidate", "stable"],
            "sha256:xyz789",
            "candidate",
        )

        assert matches is True
        assert matching_tags == ["release-candidate"]
        assert has_digest is False

    def test_multiple_matching_tags(self):
        """Should return all tags that match the filter."""
        matches, matching_tags, has_digest = _matches_tag_filter(
            ["dev-v1", "dev-v2", "prod-v1"],
            "sha256:def456",
            "dev",
        )

        assert matches is True
        assert matching_tags == ["dev-v1", "dev-v2"]
        assert has_digest is False

    def test_empty_tags_list(self):
        """Should handle empty tags list correctly."""
        matches, matching_tags, has_digest = _matches_tag_filter(
            [],
            "sha256:abc123",
            "test",
        )

        assert matches is False
        assert matching_tags == []
        assert has_digest is False

    def test_digest_only_match(self):
        """Should match digest when no tags exist."""
        matches, matching_tags, has_digest = _matches_tag_filter(
            [],
            "sha256:abc123",
            "abc123",
        )

        assert matches is True
        assert matching_tags == []
        assert has_digest is True


# ============================================================================
# Test _build_ecr_image (Pure Function)
# ============================================================================


class TestBuildEcrImage:
    """Test ECR image object construction from API response."""

    @patch("ecreshore.aws_utils.resolve_aws_region")
    def test_builds_image_with_all_fields(self, mock_resolve_region):
        """Should construct ECRImage with all fields from API response."""
        mock_resolve_region.return_value = "us-west-2"

        image_detail = {
            "imageTags": ["v1.0.0", "latest"],
            "imageDigest": "sha256:abc123def456",
            "imageSizeInBytes": 100 * 1024 * 1024,  # 100 MB
            "imagePushedAt": datetime(2024, 1, 15, 10, 30),
            "registryId": "123456789012",
        }

        image = _build_ecr_image(
            image_detail,
            repository_name="my-repo",
            registry_id="999888777666",
            region_name="us-west-2",
        )

        assert image.repository_name == "my-repo"
        assert image.image_tags == ["v1.0.0", "latest"]
        assert image.image_digest == "sha256:abc123def456"
        assert image.size_bytes == 100 * 1024 * 1024
        assert image.pushed_at == datetime(2024, 1, 15, 10, 30)
        assert image.registry_id == "999888777666"
        assert image.region == "us-west-2"

    @patch("ecreshore.aws_utils.resolve_aws_region")
    def test_handles_missing_tags(self, mock_resolve_region):
        """Should handle images without tags (digest-only)."""
        mock_resolve_region.return_value = "us-east-1"

        image_detail = {
            # No imageTags field
            "imageDigest": "sha256:fedcba987654",
            "imageSizeInBytes": 50 * 1024 * 1024,
            "imagePushedAt": datetime(2024, 2, 1, 8, 0),
        }

        image = _build_ecr_image(
            image_detail,
            repository_name="test-repo",
            registry_id="111222333444",
            region_name="us-east-1",
        )

        assert image.image_tags == []
        assert image.image_digest == "sha256:fedcba987654"

    @patch("ecreshore.aws_utils.resolve_aws_region")
    def test_uses_fallback_registry_id(self, mock_resolve_region):
        """Should use registry_id from response if not provided."""
        mock_resolve_region.return_value = "eu-west-1"

        image_detail = {
            "imageTags": ["v2.0"],
            "imageDigest": "sha256:xyz789",
            "imageSizeInBytes": 75 * 1024 * 1024,
            "imagePushedAt": datetime(2024, 3, 10, 12, 0),
            "registryId": "555666777888",
        }

        image = _build_ecr_image(
            image_detail,
            repository_name="fallback-test",
            registry_id="",  # Empty registry_id
            region_name="eu-west-1",
        )

        # Should use registry_id from image_detail
        assert image.registry_id == "555666777888"

    @patch("ecreshore.aws_utils.resolve_aws_region")
    def test_resolves_region(self, mock_resolve_region):
        """Should call resolve_aws_region to normalize region name."""
        mock_resolve_region.return_value = "ap-southeast-2"

        image_detail = {
            "imageTags": ["test"],
            "imageDigest": "sha256:test123",
            "imageSizeInBytes": 1024,
            "imagePushedAt": datetime(2024, 4, 1, 9, 0),
        }

        image = _build_ecr_image(
            image_detail,
            repository_name="region-test",
            registry_id="123",
            region_name="ap-southeast-2",
        )

        mock_resolve_region.assert_called_once_with("ap-southeast-2")
        assert image.region == "ap-southeast-2"


# ============================================================================
# Test _handle_list_images_error (Error Handler)
# ============================================================================


class TestHandleListImagesError:
    """Test error handling for list_images operation."""

    def test_repository_not_found_error(self):
        """Should raise ECRAuthenticationError for RepositoryNotFoundException."""
        error = ClientError(
            {"Error": {"Code": "RepositoryNotFoundException"}},
            "DescribeImages",
        )

        with pytest.raises(
            ECRAuthenticationError, match="Repository 'test-repo' not found"
        ):
            _handle_list_images_error(error, "test-repo")

    def test_unauthorized_operation_error(self):
        """Should raise ECRAuthenticationError for UnauthorizedOperation."""
        error = ClientError(
            {"Error": {"Code": "UnauthorizedOperation"}},
            "DescribeImages",
        )

        with pytest.raises(ECRAuthenticationError, match="Insufficient permissions"):
            _handle_list_images_error(error, "my-repo")

    def test_other_client_error(self):
        """Should raise ECRAuthenticationError for other ClientError codes."""
        error = ClientError(
            {"Error": {"Code": "ThrottlingException", "Message": "Rate exceeded"}},
            "DescribeImages",
        )

        with pytest.raises(ECRAuthenticationError, match="ECR API error"):
            _handle_list_images_error(error, "throttled-repo")

    @patch("ecreshore.services.ecr_repository.logger")
    def test_generic_exception(self, mock_logger):
        """Should handle generic exceptions and log error."""
        error = ValueError("Something went wrong")

        with pytest.raises(ECRAuthenticationError, match="Failed to list images"):
            _handle_list_images_error(error, "error-repo")

        # Should log the error
        mock_logger.error.assert_called_once()
        assert "error-repo" in mock_logger.error.call_args[0][0]

    def test_error_message_includes_repository_name(self):
        """Error messages should include repository name for context."""
        error = ClientError(
            {"Error": {"Code": "RepositoryNotFoundException"}},
            "DescribeImages",
        )

        with pytest.raises(ECRAuthenticationError) as exc_info:
            _handle_list_images_error(error, "specific-repo-name")

        assert "specific-repo-name" in str(exc_info.value)


# ============================================================================
# Integration Test for Helper Composition
# ============================================================================


class TestHelperComposition:
    """Test how helpers work together (integration-style)."""

    @patch("ecreshore.aws_utils.resolve_aws_region")
    def test_filter_and_build_workflow(self, mock_resolve_region):
        """Test typical workflow: filter check → build image."""
        mock_resolve_region.return_value = "us-west-2"

        # Simulate API response
        image_detail = {
            "imageTags": ["v1.0.0", "production"],
            "imageDigest": "sha256:abc123",
            "imageSizeInBytes": 100 * 1024 * 1024,
            "imagePushedAt": datetime(2024, 1, 1, 12, 0),
        }

        # 1. Check if image matches filter
        matches, matching_tags, _ = _matches_tag_filter(
            image_detail.get("imageTags", []),
            image_detail["imageDigest"],
            "prod",
        )

        assert matches is True

        # 2. Build image if it matches
        if matches:
            image = _build_ecr_image(
                image_detail,
                repository_name="my-repo",
                registry_id="123",
                region_name="us-west-2",
            )

            assert image.image_tags == ["v1.0.0", "production"]
            assert image.repository_name == "my-repo"
