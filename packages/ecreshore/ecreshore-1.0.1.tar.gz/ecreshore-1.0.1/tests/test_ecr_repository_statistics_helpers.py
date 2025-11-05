"""Tests for ECR repository statistics helper functions.

Following the pure-function-extraction-pattern from brain/:
- Test helpers extracted from _get_repository_statistics()
- No AWS SDK dependencies - pure business logic
- Fast tests (no mocking AWS APIs)
"""

import pytest
from datetime import datetime
from unittest.mock import Mock

from src.ecreshore.services.ecr_repository import ECRRepositoryService


class TestShouldCountImage:
    """Test _should_count_image() filtering logic."""

    def test_count_normal_tagged_image(self):
        """Test that normal tagged images are counted."""
        service = ECRRepositoryService(region_name="us-east-1")

        image_detail = {
            "imageTags": ["v1.0", "latest"],
            "imageDigest": "sha256:abc123",
            "imageSizeInBytes": 50000000,
            "imagePushedAt": datetime(2024, 1, 1, 12, 0),
            "registryId": "123456789012"
        }

        result = service._should_count_image(image_detail, "my-repo")

        # Normal tagged images should be counted
        assert result is True

    def test_skip_sha256_prefixed_tag(self):
        """Test that images with sha256: prefixed tags are not counted."""
        service = ECRRepositoryService(region_name="us-east-1")

        # Image with sha256: prefixed tag
        image_detail = {
            "imageTags": ["sha256:abc123def456"],  # Starts with sha256:
            "imageDigest": "sha256:abc123def456",
            "imageSizeInBytes": 1000,
            "imagePushedAt": datetime(2024, 1, 1, 12, 0),
            "registryId": "123456789012"
        }

        result = service._should_count_image(image_detail, "my-repo")

        # sha256: prefixed tags should NOT be counted
        assert result is False

    def test_skip_untagged_image_using_digest_fallback(self):
        """Test that untagged images (using digest fallback) are NOT counted."""
        service = ECRRepositoryService(region_name="us-east-1")

        image_detail = {
            "imageTags": [],  # No tags - will use digest as primary_tag
            "imageDigest": "sha256:def456",
            "imageSizeInBytes": 30000000,
            "imagePushedAt": datetime(2024, 1, 2, 12, 0),
            "registryId": "123456789012"
        }

        result = service._should_count_image(image_detail, "my-repo")

        # Untagged images use digest fallback, so is_digest_tag is True
        assert result is False

    def test_count_semantic_versioned_image(self):
        """Test that semantic versioned images are counted."""
        service = ECRRepositoryService(region_name="us-east-1")

        image_detail = {
            "imageTags": ["v1.2.3", "1.2.3"],
            "imageDigest": "sha256:xyz789",
            "imageSizeInBytes": 60000000,
            "imagePushedAt": datetime(2024, 1, 3, 12, 0),
            "registryId": "123456789012"
        }

        result = service._should_count_image(image_detail, "my-repo")

        assert result is True

    def test_count_signature_tag(self):
        """Test that signature tags (not starting with sha256:) are counted."""
        service = ECRRepositoryService(region_name="us-east-1")

        # Signature tag - doesn't start with sha256:
        image_detail = {
            "imageTags": ["sha256-aabbccddee1122334455.sig"],
            "imageDigest": "sha256:aabbccddee1122334455",
            "imageSizeInBytes": 500,
            "imagePushedAt": datetime(2024, 1, 4, 12, 0),
            "registryId": "123456789012"
        }

        result = service._should_count_image(image_detail, "my-repo")

        # This tag doesn't start with "sha256:", so it's counted
        assert result is True

    def test_with_registry_id_override(self):
        """Test counting with explicit registry_id in service."""
        service = ECRRepositoryService(
            region_name="us-east-1",
            registry_id="987654321098"
        )

        image_detail = {
            "imageTags": ["production"],
            "imageDigest": "sha256:prod123",
            "imageSizeInBytes": 80000000,
            "imagePushedAt": datetime(2024, 1, 5, 12, 0),
            "registryId": "123456789012"  # Different in detail
        }

        result = service._should_count_image(image_detail, "my-repo")

        # Should use service's registry_id, image should be counted
        assert result is True


class TestUpdateLatestTag:
    """Test _update_latest_tag() comparison logic."""

    def test_first_tagged_image_becomes_latest(self):
        """Test that first tagged image is set as latest."""
        service = ECRRepositoryService(region_name="us-east-1")

        image_detail = {
            "imageTags": ["v1.0"],
            "imagePushedAt": datetime(2024, 1, 1, 12, 0)
        }

        result = service._update_latest_tag(None, image_detail)

        assert result is not None
        assert result[0] == datetime(2024, 1, 1, 12, 0)
        assert result[1] == "v1.0"

    def test_newer_image_replaces_latest(self):
        """Test that newer image replaces current latest."""
        service = ECRRepositoryService(region_name="us-east-1")

        current_latest = (datetime(2024, 1, 1, 12, 0), "v1.0")

        newer_image = {
            "imageTags": ["v2.0"],
            "imagePushedAt": datetime(2024, 1, 2, 12, 0)  # Newer
        }

        result = service._update_latest_tag(current_latest, newer_image)

        assert result[0] == datetime(2024, 1, 2, 12, 0)
        assert result[1] == "v2.0"

    def test_older_image_does_not_replace_latest(self):
        """Test that older image doesn't replace current latest."""
        service = ECRRepositoryService(region_name="us-east-1")

        current_latest = (datetime(2024, 1, 5, 12, 0), "v3.0")

        older_image = {
            "imageTags": ["v1.0"],
            "imagePushedAt": datetime(2024, 1, 1, 12, 0)  # Older
        }

        result = service._update_latest_tag(current_latest, older_image)

        # Should keep current latest
        assert result == current_latest
        assert result[1] == "v3.0"

    def test_untagged_image_does_not_update_latest(self):
        """Test that untagged images don't affect latest."""
        service = ECRRepositoryService(region_name="us-east-1")

        current_latest = (datetime(2024, 1, 1, 12, 0), "v1.0")

        untagged_image = {
            "imageTags": [],  # No tags
            "imagePushedAt": datetime(2024, 1, 10, 12, 0)  # Even if newer
        }

        result = service._update_latest_tag(current_latest, untagged_image)

        # Should keep current latest
        assert result == current_latest

    def test_image_without_pushed_at_does_not_update(self):
        """Test that image without timestamp doesn't affect latest."""
        service = ECRRepositoryService(region_name="us-east-1")

        current_latest = (datetime(2024, 1, 1, 12, 0), "v1.0")

        image_no_timestamp = {
            "imageTags": ["v2.0"],
            "imagePushedAt": None  # Missing timestamp
        }

        result = service._update_latest_tag(current_latest, image_no_timestamp)

        assert result == current_latest

    def test_uses_first_tag_when_multiple(self):
        """Test that first tag is used when image has multiple tags."""
        service = ECRRepositoryService(region_name="us-east-1")

        image_detail = {
            "imageTags": ["v1.0", "latest", "stable"],
            "imagePushedAt": datetime(2024, 1, 1, 12, 0)
        }

        result = service._update_latest_tag(None, image_detail)

        # Should use first tag
        assert result[1] == "v1.0"

    def test_none_current_with_untagged_image(self):
        """Test starting with None and untagged image."""
        service = ECRRepositoryService(region_name="us-east-1")

        untagged_image = {
            "imageTags": [],
            "imagePushedAt": datetime(2024, 1, 1, 12, 0)
        }

        result = service._update_latest_tag(None, untagged_image)

        # Should remain None
        assert result is None

    def test_chronological_progression(self):
        """Test tracking latest across chronological sequence."""
        service = ECRRepositoryService(region_name="us-east-1")

        # Process images in order
        images = [
            {"imageTags": ["v1.0"], "imagePushedAt": datetime(2024, 1, 1, 12, 0)},
            {"imageTags": ["v2.0"], "imagePushedAt": datetime(2024, 1, 5, 12, 0)},
            {"imageTags": ["v1.5"], "imagePushedAt": datetime(2024, 1, 3, 12, 0)},  # Older
            {"imageTags": ["v3.0"], "imagePushedAt": datetime(2024, 1, 10, 12, 0)},
        ]

        latest_info = None
        for img in images:
            latest_info = service._update_latest_tag(latest_info, img)

        # Should end with v3.0 (most recent)
        assert latest_info[1] == "v3.0"
        assert latest_info[0] == datetime(2024, 1, 10, 12, 0)


class TestHelperIntegration:
    """Integration tests for helper composition."""

    def test_filter_and_track_workflow(self):
        """Test typical workflow: filter images and track latest."""
        service = ECRRepositoryService(region_name="us-east-1")

        images = [
            {
                "imageTags": ["v1.0"],
                "imageDigest": "sha256:abc123",
                "imageSizeInBytes": 50000000,
                "imagePushedAt": datetime(2024, 1, 1, 12, 0),
                "registryId": "123456789012"
            },
            {
                "imageTags": ["sha256:digest123"],  # Starts with sha256: - skip count
                "imageDigest": "sha256:digest123",
                "imageSizeInBytes": 1000,
                "imagePushedAt": datetime(2024, 1, 2, 12, 0),
                "registryId": "123456789012"
            },
            {
                "imageTags": ["v2.0", "latest"],
                "imageDigest": "sha256:def456",
                "imageSizeInBytes": 60000000,
                "imagePushedAt": datetime(2024, 1, 5, 12, 0),
                "registryId": "123456789012"
            },
        ]

        # Simulate processing
        count = 0
        total_size = 0
        latest_info = None

        for img in images:
            if service._should_count_image(img, "test-repo"):
                count += 1
            total_size += img["imageSizeInBytes"]
            latest_info = service._update_latest_tag(latest_info, img)

        # Should count 2 (v1.0 and v2.0), skip digest-only
        assert count == 2

        # Should sum all sizes (including digest-only)
        assert total_size == 50001000 + 60000000

        # Latest should be v2.0
        assert latest_info[1] == "v2.0"
