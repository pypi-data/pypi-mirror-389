"""Tests for list_images CLI command helpers.

Following cli-testing-pattern: Test business logic, not Click framework.
Test extracted helpers with standard pytest, avoiding CliRunner complexity.
"""

from datetime import datetime
from unittest.mock import AsyncMock, Mock, call, patch

import pytest

from ecreshore.cli.repository.list_images import (
    _build_images_table,
    _display_image_summary,
    _filter_digest_images,
    _load_images,
)
from ecreshore.services.ecr_repository import ECRImage


# ============================================================================
# Test Fixtures
# ============================================================================


@pytest.fixture
def sample_images():
    """Create sample ECRImage objects for testing."""
    return [
        ECRImage(
            repository_name="my-repo",
            image_tags=["v1.0.0", "latest"],
            image_digest="sha256:abc123def456",
            size_bytes=100 * 1024 * 1024,  # 100 MB
            pushed_at=datetime(2024, 1, 15, 10, 30),
            registry_id="123456789012",
            region="us-west-2",
            architectures=["linux/amd64", "linux/arm64"],
        ),
        ECRImage(
            repository_name="my-repo",
            image_tags=["v1.1.0"],
            image_digest="sha256:def456ghi789",
            size_bytes=150 * 1024 * 1024,  # 150 MB
            pushed_at=datetime(2024, 2, 20, 14, 45),
            registry_id="123456789012",
            region="us-west-2",
            architectures=["linux/amd64"],
        ),
        ECRImage(
            repository_name="my-repo",
            image_tags=["sha256:999888777666"],  # Digest-tagged image
            image_digest="sha256:999888777666",
            size_bytes=75 * 1024 * 1024,  # 75 MB
            pushed_at=datetime(2024, 3, 10, 9, 15),
            registry_id="123456789012",
            region="us-west-2",
            architectures=["linux/amd64"],
        ),
    ]


@pytest.fixture
def digest_only_image():
    """Create an image with no tags (digest-only)."""
    return ECRImage(
        repository_name="my-repo",
        image_tags=[],  # No tags
        image_digest="sha256:fedcba987654",
        size_bytes=50 * 1024 * 1024,
        pushed_at=datetime(2024, 4, 1, 8, 0),
        registry_id="123456789012",
        region="us-west-2",
        architectures=["linux/arm64"],
    )


@pytest.fixture
def mock_progress_reporter():
    """Create a mock progress reporter."""
    return Mock()


@pytest.fixture
def mock_ecr_service():
    """Create a mock ECR service."""
    return Mock()


# ============================================================================
# Test _filter_digest_images (Pure Function)
# ============================================================================


class TestFilterDigestImages:
    """Test digest image filtering logic."""

    def test_show_digests_true_returns_all_images(self, sample_images):
        """When show_digests=True, all images should be returned."""
        filtered, digest_count = _filter_digest_images(sample_images, show_digests=True)

        assert filtered == sample_images
        assert digest_count == 0

    def test_show_digests_false_filters_digest_tags(self, sample_images):
        """When show_digests=False, digest-tagged images should be filtered out."""
        filtered, digest_count = _filter_digest_images(
            sample_images, show_digests=False
        )

        # Should filter out the third image (digest-tagged)
        assert len(filtered) == 2
        assert digest_count == 1
        assert filtered[0].image_tags == ["v1.0.0", "latest"]
        assert filtered[1].image_tags == ["v1.1.0"]

    def test_no_digest_images_returns_all(self):
        """When no digest-tagged images, all should be returned."""
        images = [
            ECRImage(
                repository_name="test",
                image_tags=["v1"],
                image_digest="sha256:abc",
                size_bytes=100,
                pushed_at=datetime.now(),
                registry_id="123",
                region="us-west-2",
            )
        ]

        filtered, digest_count = _filter_digest_images(images, show_digests=False)

        assert filtered == images
        assert digest_count == 0

    def test_all_digest_images_filters_all(self, digest_only_image):
        """When all images are digest-tagged, all should be filtered."""
        images = [digest_only_image]

        filtered, digest_count = _filter_digest_images(images, show_digests=False)

        assert len(filtered) == 0
        assert digest_count == 1

    def test_empty_list_returns_empty(self):
        """Empty input should return empty output."""
        filtered, digest_count = _filter_digest_images([], show_digests=False)

        assert filtered == []
        assert digest_count == 0


# ============================================================================
# Test _display_image_summary (Display Helper)
# ============================================================================


class TestDisplayImageSummary:
    """Test image summary display logic."""

    def test_show_digests_true_displays_simple_count(
        self, sample_images, mock_progress_reporter
    ):
        """When show_digests=True, show simple image count."""
        _display_image_summary(
            sample_images,
            digest_count=0,
            show_digests=True,
            progress_reporter=mock_progress_reporter,
            verbose=False,
        )

        mock_progress_reporter.success.assert_called_once_with("Found 3 images")

    def test_show_digests_false_with_hidden_digests(
        self, sample_images, mock_progress_reporter
    ):
        """When digest images are hidden, show count with hidden message."""
        _display_image_summary(
            sample_images[:2],  # 2 filtered images
            digest_count=1,
            show_digests=False,
            progress_reporter=mock_progress_reporter,
            verbose=False,
        )

        mock_progress_reporter.success.assert_called_once_with(
            "Found 2 tagged images (1 digest entries hidden)"
        )

    def test_verbose_shows_hint_about_show_digests(
        self, sample_images, mock_progress_reporter
    ):
        """When verbose=True and digests hidden, show hint."""
        _display_image_summary(
            sample_images[:2],
            digest_count=1,
            show_digests=False,
            progress_reporter=mock_progress_reporter,
            verbose=True,
        )

        assert mock_progress_reporter.info.call_count == 1
        mock_progress_reporter.info.assert_called_with(
            "Use --show-digests to include SHA256-tagged entries"
        )

    def test_no_verbose_no_hint(self, sample_images, mock_progress_reporter):
        """When verbose=False, don't show hint."""
        _display_image_summary(
            sample_images[:2],
            digest_count=1,
            show_digests=False,
            progress_reporter=mock_progress_reporter,
            verbose=False,
        )

        mock_progress_reporter.info.assert_not_called()

    def test_no_digests_filtered_simple_message(
        self, sample_images, mock_progress_reporter
    ):
        """When no digests were filtered, show simple success message."""
        _display_image_summary(
            sample_images,
            digest_count=0,
            show_digests=False,
            progress_reporter=mock_progress_reporter,
            verbose=False,
        )

        mock_progress_reporter.success.assert_called_once_with("Found 3 images")


# ============================================================================
# Test _build_images_table (Pure Function)
# ============================================================================


class TestBuildImagesTable:
    """Test table building logic."""

    def test_brief_mode_has_four_columns(self, sample_images):
        """Brief mode should have 4 columns (no architectures)."""
        table = _build_images_table("my-repo", sample_images, brief=True)

        assert len(table.columns) == 4
        column_headers = [col.header for col in table.columns]
        assert "Tag" in column_headers
        assert "Digest" in column_headers
        assert "Size" in column_headers
        assert "Pushed" in column_headers
        assert "Architectures" not in column_headers

    def test_detailed_mode_has_five_columns(self, sample_images):
        """Detailed mode should have 5 columns (including architectures)."""
        table = _build_images_table("my-repo", sample_images, brief=False)

        assert len(table.columns) == 5
        column_headers = [col.header for col in table.columns]
        assert "Architectures" in column_headers

    def test_table_title_includes_repository_name(self, sample_images):
        """Table title should include repository name."""
        table = _build_images_table("my-test-repo", sample_images, brief=False)

        assert "my-test-repo" in table.title

    def test_correct_number_of_rows(self, sample_images):
        """Table should have one row per image."""
        table = _build_images_table("my-repo", sample_images, brief=False)

        # Rich table doesn't expose row count directly, but we can verify
        # by checking the row_count property
        assert table.row_count == 3

    def test_empty_images_creates_empty_table(self):
        """Empty image list should create table with headers only."""
        table = _build_images_table("my-repo", [], brief=False)

        assert table.row_count == 0
        assert len(table.columns) == 5  # Headers still present

    def test_single_tag_display(self):
        """Image with single tag should display without additional tags."""
        image = ECRImage(
            repository_name="test",
            image_tags=["v1.0"],
            image_digest="sha256:abc123",
            size_bytes=100 * 1024 * 1024,
            pushed_at=datetime(2024, 1, 1, 12, 0),
            registry_id="123",
            region="us-west-2",
            architectures=["linux/amd64"],
        )

        table = _build_images_table("test", [image], brief=False)
        assert table.row_count == 1

    def test_multiple_tags_displayed(self):
        """Image with multiple tags should show additional tags."""
        image = ECRImage(
            repository_name="test",
            image_tags=["v1.0", "latest", "stable", "prod", "release"],  # 5 tags
            image_digest="sha256:abc123",
            size_bytes=100 * 1024 * 1024,
            pushed_at=datetime(2024, 1, 1, 12, 0),
            registry_id="123",
            region="us-west-2",
        )

        table = _build_images_table("test", [image], brief=True)
        # We can't easily inspect the cell contents, but we verify it doesn't crash
        assert table.row_count == 1


# ============================================================================
# Test _load_images (Service Layer - Async)
# ============================================================================


class TestLoadImages:
    """Test async image loading logic."""

    @pytest.mark.asyncio
    async def test_brief_mode_calls_sync_list_images(
        self, mock_ecr_service, mock_progress_reporter, sample_images
    ):
        """Brief mode should call synchronous list_images method."""
        mock_ecr_service.list_images.return_value = sample_images

        result = await _load_images(
            mock_ecr_service,
            "my-repo",
            tag_filter=None,
            max_results=20,
            brief=True,
            progress_reporter=mock_progress_reporter,
        )

        mock_ecr_service.list_images.assert_called_once_with(
            "my-repo", tag_filter=None, max_results=20
        )
        assert result == sample_images

    @pytest.mark.asyncio
    async def test_detailed_mode_calls_async_with_architectures(
        self, mock_ecr_service, mock_progress_reporter, sample_images
    ):
        """Detailed mode should call async list_images_with_architectures."""
        mock_ecr_service.list_images_with_architectures = AsyncMock(
            return_value=sample_images
        )

        result = await _load_images(
            mock_ecr_service,
            "my-repo",
            tag_filter=None,
            max_results=20,
            brief=False,
            progress_reporter=mock_progress_reporter,
        )

        mock_ecr_service.list_images_with_architectures.assert_called_once_with(
            "my-repo", tag_filter=None, max_results=20
        )
        assert result == sample_images

    @pytest.mark.asyncio
    async def test_displays_loading_message(
        self, mock_ecr_service, mock_progress_reporter, sample_images
    ):
        """Should display loading message."""
        mock_ecr_service.list_images.return_value = sample_images

        await _load_images(
            mock_ecr_service,
            "test-repo",
            tag_filter=None,
            max_results=20,
            brief=True,
            progress_reporter=mock_progress_reporter,
        )

        # Check that info was called with loading message
        calls = mock_progress_reporter.info.call_args_list
        assert any(
            "Loading images from repository 'test-repo'" in str(call) for call in calls
        )

    @pytest.mark.asyncio
    async def test_detailed_mode_shows_architecture_detection_message(
        self, mock_ecr_service, mock_progress_reporter, sample_images
    ):
        """Detailed mode should show architecture detection message."""
        mock_ecr_service.list_images_with_architectures = AsyncMock(
            return_value=sample_images
        )

        await _load_images(
            mock_ecr_service,
            "my-repo",
            tag_filter=None,
            max_results=20,
            brief=False,
            progress_reporter=mock_progress_reporter,
        )

        calls = mock_progress_reporter.info.call_args_list
        assert any("Detecting image architectures" in str(call) for call in calls)

    @pytest.mark.asyncio
    async def test_tag_filter_passed_correctly(
        self, mock_ecr_service, mock_progress_reporter, sample_images
    ):
        """Tag filter should be passed to service method."""
        mock_ecr_service.list_images.return_value = sample_images

        await _load_images(
            mock_ecr_service,
            "my-repo",
            tag_filter="v1.*",
            max_results=50,
            brief=True,
            progress_reporter=mock_progress_reporter,
        )

        mock_ecr_service.list_images.assert_called_once_with(
            "my-repo", tag_filter="v1.*", max_results=50
        )

    @pytest.mark.asyncio
    async def test_returns_empty_list_when_no_images(
        self, mock_ecr_service, mock_progress_reporter
    ):
        """Should handle empty image list."""
        mock_ecr_service.list_images.return_value = []

        result = await _load_images(
            mock_ecr_service,
            "empty-repo",
            tag_filter=None,
            max_results=20,
            brief=True,
            progress_reporter=mock_progress_reporter,
        )

        assert result == []
