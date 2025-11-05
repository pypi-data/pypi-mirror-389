"""Tests for purge service helper functions.

Following the pure-function-extraction-pattern from brain/:
- Test helpers extracted from _delete_image_batch()
- No AWS SDK dependencies - pure response processing
- Fast tests (no mocking AWS APIs)
"""

import pytest
from datetime import datetime
from dataclasses import dataclass
from botocore.exceptions import ClientError

from src.ecreshore.services.purge_service import ECRPurgeService
from src.ecreshore.services.ecr_repository import ECRImage

# Import shared mock from fixtures
from tests.fixtures.ecr_fixtures import MockECRImage


class TestExtractDeletedImages:
    """Test _extract_deleted_images() pure function."""

    def test_extract_single_deleted_image(self):
        """Test extracting one successfully deleted image."""
        service = ECRPurgeService(region_name="us-east-1")

        img1 = MockECRImage(image_digest="sha256:abc123", image_tags=["v1.0"])
        digest_to_image = {"sha256:abc123": img1}

        response_ids = [{"imageDigest": "sha256:abc123"}]

        result = service._extract_deleted_images(response_ids, digest_to_image)

        assert len(result) == 1
        assert result[0] == img1

    def test_extract_multiple_deleted_images(self):
        """Test extracting multiple successfully deleted images."""
        service = ECRPurgeService(region_name="us-east-1")

        img1 = MockECRImage(image_digest="sha256:abc123", image_tags=["v1.0"])
        img2 = MockECRImage(image_digest="sha256:def456", image_tags=["v2.0"])
        img3 = MockECRImage(image_digest="sha256:ghi789", image_tags=["v3.0"])

        digest_to_image = {
            "sha256:abc123": img1,
            "sha256:def456": img2,
            "sha256:ghi789": img3,
        }

        response_ids = [
            {"imageDigest": "sha256:abc123"},
            {"imageDigest": "sha256:def456"},
            {"imageDigest": "sha256:ghi789"},
        ]

        result = service._extract_deleted_images(response_ids, digest_to_image)

        assert len(result) == 3
        assert img1 in result
        assert img2 in result
        assert img3 in result

    def test_skip_missing_digest_field(self):
        """Test that entries without imageDigest are skipped."""
        service = ECRPurgeService(region_name="us-east-1")

        img1 = MockECRImage(image_digest="sha256:abc123", image_tags=["v1.0"])
        digest_to_image = {"sha256:abc123": img1}

        response_ids = [
            {"imageDigest": "sha256:abc123"},
            {},  # Missing imageDigest
            {"imageTag": "latest"},  # Wrong field
        ]

        result = service._extract_deleted_images(response_ids, digest_to_image)

        assert len(result) == 1
        assert result[0] == img1

    def test_skip_unknown_digests(self):
        """Test that digests not in mapping are skipped."""
        service = ECRPurgeService(region_name="us-east-1")

        img1 = MockECRImage(image_digest="sha256:abc123", image_tags=["v1.0"])
        digest_to_image = {"sha256:abc123": img1}

        response_ids = [
            {"imageDigest": "sha256:abc123"},  # Known
            {"imageDigest": "sha256:unknown"},  # Unknown
        ]

        result = service._extract_deleted_images(response_ids, digest_to_image)

        assert len(result) == 1
        assert result[0] == img1

    def test_empty_response(self):
        """Test handling empty response list."""
        service = ECRPurgeService(region_name="us-east-1")

        digest_to_image = {}
        response_ids = []

        result = service._extract_deleted_images(response_ids, digest_to_image)

        assert len(result) == 0


class TestExtractFailedImages:
    """Test _extract_failed_images() pure function."""

    def test_extract_single_failed_image(self):
        """Test extracting one failed deletion."""
        service = ECRPurgeService(region_name="us-east-1")

        img1 = MockECRImage(image_digest="sha256:abc123", image_tags=["v1.0"])
        digest_to_image = {"sha256:abc123": img1}

        response_failures = [
            {
                "imageId": {"imageDigest": "sha256:abc123"},
                "failureCode": "ImageReferencedByManifestList",
                "failureReason": "Image is referenced by a manifest list"
            }
        ]

        result = service._extract_failed_images(response_failures, digest_to_image)

        assert len(result) == 1
        assert result[0] == img1

    def test_extract_multiple_failed_images(self):
        """Test extracting multiple failed deletions."""
        service = ECRPurgeService(region_name="us-east-1")

        img1 = MockECRImage(image_digest="sha256:abc123", image_tags=["v1.0"])
        img2 = MockECRImage(image_digest="sha256:def456", image_tags=["v2.0"])

        digest_to_image = {
            "sha256:abc123": img1,
            "sha256:def456": img2,
        }

        response_failures = [
            {
                "imageId": {"imageDigest": "sha256:abc123"},
                "failureCode": "ImageReferencedByManifestList",
                "failureReason": "Referenced by manifest"
            },
            {
                "imageId": {"imageDigest": "sha256:def456"},
                "failureCode": "InvalidParameterException",
                "failureReason": "Invalid parameter"
            }
        ]

        result = service._extract_failed_images(response_failures, digest_to_image)

        assert len(result) == 2
        assert img1 in result
        assert img2 in result

    def test_skip_missing_image_id(self):
        """Test that failures without imageId are skipped."""
        service = ECRPurgeService(region_name="us-east-1")

        img1 = MockECRImage(image_digest="sha256:abc123", image_tags=["v1.0"])
        digest_to_image = {"sha256:abc123": img1}

        response_failures = [
            {
                "imageId": {"imageDigest": "sha256:abc123"},
                "failureReason": "Some error"
            },
            {
                # Missing imageId
                "failureReason": "Some error"
            }
        ]

        result = service._extract_failed_images(response_failures, digest_to_image)

        assert len(result) == 1
        assert result[0] == img1

    def test_skip_unknown_digests(self):
        """Test that unknown digests in failures are skipped."""
        service = ECRPurgeService(region_name="us-east-1")

        img1 = MockECRImage(image_digest="sha256:abc123", image_tags=["v1.0"])
        digest_to_image = {"sha256:abc123": img1}

        response_failures = [
            {
                "imageId": {"imageDigest": "sha256:abc123"},
                "failureReason": "Error"
            },
            {
                "imageId": {"imageDigest": "sha256:unknown"},
                "failureReason": "Error"
            }
        ]

        result = service._extract_failed_images(response_failures, digest_to_image)

        assert len(result) == 1
        assert result[0] == img1

    def test_empty_failures(self):
        """Test handling empty failures list."""
        service = ECRPurgeService(region_name="us-east-1")

        digest_to_image = {}
        response_failures = []

        result = service._extract_failed_images(response_failures, digest_to_image)

        assert len(result) == 0


class TestHandleDeleteError:
    """Test _handle_delete_error() error handler."""

    def test_repository_not_found_error(self):
        """Test handling RepositoryNotFoundException."""
        service = ECRPurgeService(region_name="us-east-1")

        img1 = MockECRImage(image_digest="sha256:abc123", image_tags=["v1.0"])
        images = [img1]

        error = ClientError(
            {"Error": {"Code": "RepositoryNotFoundException", "Message": "Not found"}},
            "batch_delete_image"
        )

        deleted, failed = service._handle_delete_error(error, "test-repo", images)

        assert len(deleted) == 0
        assert len(failed) == 1
        assert failed[0] == img1

    def test_invalid_parameter_error(self):
        """Test handling InvalidParameterException."""
        service = ECRPurgeService(region_name="us-east-1")

        img1 = MockECRImage(image_digest="sha256:abc123", image_tags=["v1.0"])
        images = [img1]

        error = ClientError(
            {"Error": {"Code": "InvalidParameterException", "Message": "Invalid"}},
            "batch_delete_image"
        )

        deleted, failed = service._handle_delete_error(error, "test-repo", images)

        assert len(deleted) == 0
        assert len(failed) == 1
        assert failed[0] == img1

    def test_other_client_error(self):
        """Test handling other ClientError types."""
        service = ECRPurgeService(region_name="us-east-1")

        img1 = MockECRImage(image_digest="sha256:abc123", image_tags=["v1.0"])
        images = [img1]

        error = ClientError(
            {"Error": {"Code": "ServerException", "Message": "Server error"}},
            "batch_delete_image"
        )

        deleted, failed = service._handle_delete_error(error, "test-repo", images)

        assert len(deleted) == 0
        assert len(failed) == 1

    def test_generic_exception(self):
        """Test handling generic exceptions."""
        service = ECRPurgeService(region_name="us-east-1")

        img1 = MockECRImage(image_digest="sha256:abc123", image_tags=["v1.0"])
        img2 = MockECRImage(image_digest="sha256:def456", image_tags=["v2.0"])
        images = [img1, img2]

        error = Exception("Something went wrong")

        deleted, failed = service._handle_delete_error(error, "test-repo", images)

        assert len(deleted) == 0
        assert len(failed) == 2
        assert img1 in failed
        assert img2 in failed

    def test_all_images_returned_as_failed(self):
        """Test that all images are returned as failed on error."""
        service = ECRPurgeService(region_name="us-east-1")

        images = [
            MockECRImage(image_digest="sha256:img1", image_tags=["v1"]),
            MockECRImage(image_digest="sha256:img2", image_tags=["v2"]),
            MockECRImage(image_digest="sha256:img3", image_tags=["v3"]),
        ]

        error = Exception("Error")

        deleted, failed = service._handle_delete_error(error, "repo", images)

        assert len(deleted) == 0
        assert len(failed) == 3
        assert all(img in failed for img in images)


class TestHelperIntegration:
    """Integration tests for helper composition."""

    def test_typical_delete_workflow(self):
        """Test typical workflow: some succeed, some fail."""
        service = ECRPurgeService(region_name="us-east-1")

        img1 = MockECRImage(image_digest="sha256:abc123", image_tags=["v1.0"])
        img2 = MockECRImage(image_digest="sha256:def456", image_tags=["v2.0"])
        img3 = MockECRImage(image_digest="sha256:ghi789", image_tags=["v3.0"])

        digest_to_image = {
            "sha256:abc123": img1,
            "sha256:def456": img2,
            "sha256:ghi789": img3,
        }

        # Simulate AWS response: 2 deleted, 1 failed
        response_ids = [
            {"imageDigest": "sha256:abc123"},
            {"imageDigest": "sha256:def456"},
        ]

        response_failures = [
            {
                "imageId": {"imageDigest": "sha256:ghi789"},
                "failureCode": "ImageReferenced",
                "failureReason": "Image is referenced"
            }
        ]

        deleted = service._extract_deleted_images(response_ids, digest_to_image)
        failed = service._extract_failed_images(response_failures, digest_to_image)

        assert len(deleted) == 2
        assert img1 in deleted
        assert img2 in deleted

        assert len(failed) == 1
        assert img3 in failed

    def test_all_deletions_succeed(self):
        """Test when all deletions succeed."""
        service = ECRPurgeService(region_name="us-east-1")

        img1 = MockECRImage(image_digest="sha256:abc123", image_tags=["v1.0"])
        img2 = MockECRImage(image_digest="sha256:def456", image_tags=["v2.0"])

        digest_to_image = {
            "sha256:abc123": img1,
            "sha256:def456": img2,
        }

        response_ids = [
            {"imageDigest": "sha256:abc123"},
            {"imageDigest": "sha256:def456"},
        ]
        response_failures = []

        deleted = service._extract_deleted_images(response_ids, digest_to_image)
        failed = service._extract_failed_images(response_failures, digest_to_image)

        assert len(deleted) == 2
        assert len(failed) == 0

    def test_all_deletions_fail(self):
        """Test when all deletions fail."""
        service = ECRPurgeService(region_name="us-east-1")

        img1 = MockECRImage(image_digest="sha256:abc123", image_tags=["v1.0"])
        img2 = MockECRImage(image_digest="sha256:def456", image_tags=["v2.0"])

        digest_to_image = {
            "sha256:abc123": img1,
            "sha256:def456": img2,
        }

        response_ids = []
        response_failures = [
            {"imageId": {"imageDigest": "sha256:abc123"}, "failureReason": "Error"},
            {"imageId": {"imageDigest": "sha256:def456"}, "failureReason": "Error"},
        ]

        deleted = service._extract_deleted_images(response_ids, digest_to_image)
        failed = service._extract_failed_images(response_failures, digest_to_image)

        assert len(deleted) == 0
        assert len(failed) == 2
