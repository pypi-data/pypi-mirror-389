"""Tests for pure purge display helper functions.

Following the pure-function-extraction-pattern from brain/:
- Test helpers extracted from _display_purge_results()
- No Rich dependencies - pure data transformation
- Fast tests (no mocking needed for pure functions)
"""

import pytest
from datetime import datetime
from dataclasses import dataclass
from typing import List, Optional

# Import the functions under test
from src.ecreshore.cli.repository.purge import (
    _format_image_row_data,
    _build_purge_summary_lines,
    _should_display_repository,
    ImageRowData
)

# Import shared mock from fixtures
from tests.fixtures.ecr_fixtures import MockECRImage


# Mock PurgeResult for testing
@dataclass
class MockPurgeResult:
    """Mock PurgeResult for testing."""
    repository_name: str
    deleted_images: List = None
    kept_images: List = None
    failed_images: List = None
    error_message: Optional[str] = None

    def __post_init__(self):
        self.deleted_images = self.deleted_images or []
        self.kept_images = self.kept_images or []
        self.failed_images = self.failed_images or []


# Mock PurgeSummary for testing
@dataclass
class MockPurgeSummary:
    """Mock PurgeSummary for testing."""
    total_images_deleted: int
    total_images_kept: int
    total_images_failed: int
    repositories_failed: int
    overall_success: bool


class TestFormatImageRowData:
    """Test _format_image_row_data() pure function."""

    def test_format_image_with_all_fields(self):
        """Test formatting image with all metadata present."""
        image = MockECRImage(
            image_tags=["v1.0", "latest"],
            image_digest="sha256:abc123def456",
            pushed_at=datetime(2024, 1, 15, 10, 30),
            size_bytes=50000000  # ~47.7 MB
        )

        result = _format_image_row_data(image)

        assert isinstance(result, ImageRowData)
        assert result.tags_str == "v1.0, latest"
        assert result.digest_short == "abc123def456"
        assert result.pushed_str == "01-15 10:30"
        assert result.size_mb == "47.7"

    def test_format_untagged_image(self):
        """Test formatting image without tags."""
        image = MockECRImage(
            image_tags=[],
            image_digest="sha256:def456abc123",
            pushed_at=datetime(2024, 2, 20, 15, 45),
            size_bytes=100000000
        )

        result = _format_image_row_data(image)

        assert result.tags_str == "[dim italic]<untagged>[/dim italic]"
        assert result.digest_short == "def456abc123"
        assert result.pushed_str == "02-20 15:45"
        assert result.size_mb == "95.4"

    def test_format_digest_without_prefix(self):
        """Test formatting digest without sha256: prefix."""
        image = MockECRImage(
            image_tags=["test"],
            image_digest="abc123def456ghi789",  # No prefix
            pushed_at=datetime(2024, 3, 1, 8, 0),
            size_bytes=1024 * 1024  # 1 MB
        )

        result = _format_image_row_data(image)

        assert result.digest_short == "abc123def456"  # First 12 chars
        assert result.size_mb == "1.0"

    def test_format_image_missing_pushed_at(self):
        """Test formatting image without push timestamp."""
        image = MockECRImage(
            image_tags=["v2.0"],
            image_digest="sha256:xyz789",
            pushed_at=None,
            size_bytes=5000000
        )

        result = _format_image_row_data(image)

        assert result.pushed_str == "unknown"
        assert result.tags_str == "v2.0"

    def test_format_image_missing_size(self):
        """Test formatting image without size information."""
        image = MockECRImage(
            image_tags=["v3.0"],
            image_digest="sha256:zzz111",
            pushed_at=datetime(2024, 4, 10, 12, 0),
            size_bytes=None
        )

        result = _format_image_row_data(image)

        assert result.size_mb == "?"
        assert result.pushed_str == "04-10 12:00"

    def test_format_multiple_tags(self):
        """Test formatting image with multiple tags."""
        image = MockECRImage(
            image_tags=["v1.0", "v1.0.0", "stable", "latest"],
            image_digest="sha256:multi123",
            pushed_at=datetime(2024, 5, 1, 9, 15),
            size_bytes=75000000
        )

        result = _format_image_row_data(image)

        assert result.tags_str == "v1.0, v1.0.0, stable, latest"
        assert "multi123" in result.digest_short

    def test_format_zero_size_image(self):
        """Test formatting image with zero size - treated as missing."""
        image = MockECRImage(
            image_tags=["empty"],
            image_digest="sha256:empty000",
            pushed_at=datetime(2024, 6, 1, 0, 0),
            size_bytes=0  # Zero is falsy, treated as missing
        )

        result = _format_image_row_data(image)

        # Zero size is treated as missing (falsy check)
        assert result.size_mb == "?"


class TestBuildPurgeSummaryLines:
    """Test _build_purge_summary_lines() pure function."""

    def test_successful_purge_summary(self):
        """Test summary for completely successful purge."""
        result = MockPurgeSummary(
            total_images_deleted=10,
            total_images_kept=2,
            total_images_failed=0,
            repositories_failed=0,
            overall_success=True
        )

        lines = _build_purge_summary_lines(result, displayable_count=3)

        assert len(lines) == 4
        assert "[bold green]✅ Purge completed successfully!" in lines[0]
        assert "Images deleted: 10" in lines[1]
        assert "Images kept: 2" in lines[2]
        assert "Repositories processed: 3" in lines[3]

    def test_successful_purge_no_kept_images(self):
        """Test summary when no images were kept."""
        result = MockPurgeSummary(
            total_images_deleted=5,
            total_images_kept=0,
            total_images_failed=0,
            repositories_failed=0,
            overall_success=True
        )

        lines = _build_purge_summary_lines(result, displayable_count=2)

        assert len(lines) == 3  # No "Images kept" line
        assert "[bold green]✅ Purge completed successfully!" in lines[0]
        assert "Images deleted: 5" in lines[1]
        assert "Repositories processed: 2" in lines[2]
        assert not any("Images kept" in line for line in lines)

    def test_partial_success_with_failures(self):
        """Test summary for partially successful purge."""
        result = MockPurgeSummary(
            total_images_deleted=8,
            total_images_kept=1,
            total_images_failed=3,
            repositories_failed=1,
            overall_success=False
        )

        lines = _build_purge_summary_lines(result, displayable_count=4)

        assert len(lines) == 6
        assert "[bold yellow]⚠️  Purge partially completed" in lines[0]
        assert "Images deleted: 8" in lines[1]
        assert "Images failed: 3" in lines[2]
        assert "Images kept: 1" in lines[3]
        assert "Repositories failed: 1" in lines[4]
        assert "Repositories processed: 4" in lines[5]

    def test_partial_success_no_kept_images(self):
        """Test partial success summary without kept images."""
        result = MockPurgeSummary(
            total_images_deleted=5,
            total_images_kept=0,
            total_images_failed=2,
            repositories_failed=1,
            overall_success=False
        )

        lines = _build_purge_summary_lines(result, displayable_count=2)

        assert "[bold yellow]⚠️  Purge partially completed" in lines[0]
        assert "Images deleted: 5" in lines[1]
        assert "Images failed: 2" in lines[2]
        assert "Repositories failed: 1" in lines[3]
        assert not any("Images kept" in line for line in lines)

    def test_zero_deleted_images(self):
        """Test summary when no images were deleted."""
        result = MockPurgeSummary(
            total_images_deleted=0,
            total_images_kept=5,
            total_images_failed=0,
            repositories_failed=0,
            overall_success=True
        )

        lines = _build_purge_summary_lines(result, displayable_count=1)

        assert "Images deleted: 0" in lines[1]
        assert "Images kept: 5" in lines[2]


class TestShouldDisplayRepository:
    """Test _should_display_repository() pure function."""

    def test_display_with_deleted_images(self):
        """Test repository should display if it has deleted images."""
        purge_result = MockPurgeResult(
            repository_name="test-repo",
            deleted_images=["image1"],  # Has deletions
            kept_images=[],
            failed_images=[],
            error_message=None
        )

        assert _should_display_repository(purge_result) is True

    def test_display_with_kept_images(self):
        """Test repository should display if it has kept images."""
        purge_result = MockPurgeResult(
            repository_name="test-repo",
            deleted_images=[],
            kept_images=["image1"],  # Has kept
            failed_images=[],
            error_message=None
        )

        assert _should_display_repository(purge_result) is True

    def test_display_with_failed_images(self):
        """Test repository should display if it has failed images."""
        purge_result = MockPurgeResult(
            repository_name="test-repo",
            deleted_images=[],
            kept_images=[],
            failed_images=["image1"],  # Has failures
            error_message=None
        )

        assert _should_display_repository(purge_result) is True

    def test_display_with_error_message(self):
        """Test repository should display if it has an error message."""
        purge_result = MockPurgeResult(
            repository_name="test-repo",
            deleted_images=[],
            kept_images=[],
            failed_images=[],
            error_message="Repository not found"  # Has error
        )

        assert _should_display_repository(purge_result) is True

    def test_no_display_when_empty(self):
        """Test repository should NOT display if completely empty."""
        purge_result = MockPurgeResult(
            repository_name="test-repo",
            deleted_images=[],
            kept_images=[],
            failed_images=[],
            error_message=None
        )

        assert _should_display_repository(purge_result) is False

    def test_display_with_multiple_categories(self):
        """Test repository displays with images in multiple categories."""
        purge_result = MockPurgeResult(
            repository_name="test-repo",
            deleted_images=["img1", "img2"],
            kept_images=["img3"],
            failed_images=["img4"],
            error_message=None
        )

        assert _should_display_repository(purge_result) is True


class TestHelperIntegration:
    """Integration tests for helper composition."""

    def test_format_and_display_workflow(self):
        """Test typical workflow: format image → build summary."""
        # Format an image
        image = MockECRImage(
            image_tags=["v1.0"],
            image_digest="sha256:abc123",
            pushed_at=datetime(2024, 1, 1, 12, 0),
            size_bytes=10485760  # 10 MB
        )

        row_data = _format_image_row_data(image)

        # Verify formatted data is ready for display
        assert all([
            row_data.tags_str,
            row_data.digest_short,
            row_data.pushed_str,
            row_data.size_mb
        ])

        # Build summary for successful operation
        result = MockPurgeSummary(
            total_images_deleted=1,
            total_images_kept=0,
            total_images_failed=0,
            repositories_failed=0,
            overall_success=True
        )

        summary = _build_purge_summary_lines(result, displayable_count=1)

        # Verify summary is complete
        assert len(summary) >= 3
        assert any("successfully" in line for line in summary)
