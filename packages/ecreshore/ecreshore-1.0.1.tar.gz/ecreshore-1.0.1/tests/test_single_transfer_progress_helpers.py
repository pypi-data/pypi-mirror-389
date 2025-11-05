"""Tests for single transfer progress helper functions.

Following the pure-function-extraction-pattern from brain/:
- Test helpers extracted from complete_transfer()
- No Rich dependencies - pure string formatting
- Fast tests (no mocking needed for pure functions)
"""

import pytest
from dataclasses import dataclass

from src.ecreshore.services.single_transfer_progress import SingleTransferProgressReporter


# Mock TransferRequest for testing
@dataclass
class MockTransferRequest:
    """Mock TransferRequest for testing."""
    source_image: str
    source_tag: str
    target_repository: str
    target_tag: str


class TestBuildTransferDescription:
    """Test _build_transfer_description() pure function."""

    def test_successful_transfer_description(self):
        """Test description for successful transfer."""
        reporter = SingleTransferProgressReporter(simple_mode=True)
        req = MockTransferRequest(
            source_image="ghcr.io/myorg/myapp",
            source_tag="v1.0",
            target_repository="myapp",
            target_tag="v1.0"
        )

        result = reporter._build_transfer_description(req, duration=15.5, success=True)

        assert "✓ Completed" in result
        assert "ghcr.io/myorg/myapp:v1.0" in result
        assert "myapp:v1.0" in result
        assert "15.5s" in result
        assert "→" in result

    def test_failed_transfer_description(self):
        """Test description for failed transfer."""
        reporter = SingleTransferProgressReporter(simple_mode=True)
        req = MockTransferRequest(
            source_image="ghcr.io/myorg/myapp",
            source_tag="v2.0",
            target_repository="myapp",
            target_tag="v2.0"
        )

        result = reporter._build_transfer_description(req, duration=8.3, success=False)

        assert "✗ Failed" in result
        assert "ghcr.io/myorg/myapp:v2.0" in result
        assert "myapp:v2.0" in result
        assert "8.3s" in result
        assert "→" in result

    def test_duration_formatting(self):
        """Test that duration is formatted to 1 decimal place."""
        reporter = SingleTransferProgressReporter(simple_mode=True)
        req = MockTransferRequest(
            source_image="nginx",
            source_tag="latest",
            target_repository="web-server",
            target_tag="prod"
        )

        # Test various durations
        result1 = reporter._build_transfer_description(req, duration=1.234, success=True)
        assert "1.2s" in result1

        result2 = reporter._build_transfer_description(req, duration=100.999, success=True)
        assert "101.0s" in result2

    def test_with_different_source_target_tags(self):
        """Test description when source and target tags differ."""
        reporter = SingleTransferProgressReporter(simple_mode=True)
        req = MockTransferRequest(
            source_image="redis",
            source_tag="7.0",
            target_repository="cache",
            target_tag="latest"
        )

        result = reporter._build_transfer_description(req, duration=5.0, success=True)

        assert "redis:7.0" in result
        assert "cache:latest" in result


class TestFormatCompletionStatusSimple:
    """Test _format_completion_status_simple() pure function."""

    def test_successful_completion_no_error(self):
        """Test simple success status."""
        reporter = SingleTransferProgressReporter(simple_mode=True)

        lines = reporter._format_completion_status_simple(
            success=True,
            error_message=None,
            duration=10.5
        )

        assert len(lines) == 1
        assert "✓ Completed" in lines[0]
        assert "10.5s" in lines[0]

    def test_failed_completion_with_error(self):
        """Test simple failure status with error message."""
        reporter = SingleTransferProgressReporter(simple_mode=True)

        lines = reporter._format_completion_status_simple(
            success=False,
            error_message="Connection timeout",
            duration=30.0
        )

        assert len(lines) == 2
        assert "✗ Failed" in lines[0]
        assert "30.0s" in lines[0]
        assert "Error: Connection timeout" in lines[1]

    def test_failed_completion_no_error_message(self):
        """Test simple failure status without error message."""
        reporter = SingleTransferProgressReporter(simple_mode=True)

        lines = reporter._format_completion_status_simple(
            success=False,
            error_message=None,
            duration=5.0
        )

        assert len(lines) == 1
        assert "✗ Failed" in lines[0]
        assert "5.0s" in lines[0]

    def test_error_message_indentation(self):
        """Test that error messages are properly indented."""
        reporter = SingleTransferProgressReporter(simple_mode=True)

        lines = reporter._format_completion_status_simple(
            success=False,
            error_message="Network error",
            duration=2.5
        )

        assert len(lines) == 2
        assert lines[1].startswith("    Error:")


class TestFormatRichProgressDescription:
    """Test _format_rich_progress_description() pure function."""

    def test_successful_rich_description(self):
        """Test Rich format for successful transfer."""
        reporter = SingleTransferProgressReporter(simple_mode=False)
        req = MockTransferRequest(
            source_image="postgres",
            source_tag="15",
            target_repository="database",
            target_tag="prod"
        )

        result = reporter._format_rich_progress_description(req, duration=20.5, success=True)

        assert "[green]✓" in result
        assert "Transfer 1:" in result
        assert "postgres:15" in result
        assert "database:prod" in result
        assert "20.5s" in result
        assert "→" in result

    def test_failed_rich_description(self):
        """Test Rich format for failed transfer."""
        reporter = SingleTransferProgressReporter(simple_mode=False)
        req = MockTransferRequest(
            source_image="mongo",
            source_tag="6.0",
            target_repository="nosql",
            target_tag="staging"
        )

        result = reporter._format_rich_progress_description(req, duration=10.0, success=False)

        assert "[red]✗" in result
        assert "Transfer 1:" in result
        assert "mongo:6.0" in result
        assert "nosql:staging" in result
        assert "(Failed)" in result
        # Should NOT include duration in failed message (as per original)
        assert "10.0s" not in result

    def test_rich_markup_preserved(self):
        """Test that Rich markup tags are properly formatted."""
        reporter = SingleTransferProgressReporter(simple_mode=False)
        req = MockTransferRequest(
            source_image="alpine",
            source_tag="3.18",
            target_repository="base",
            target_tag="v1"
        )

        result_success = reporter._format_rich_progress_description(req, duration=3.0, success=True)
        assert result_success.startswith("[green]")

        result_failure = reporter._format_rich_progress_description(req, duration=3.0, success=False)
        assert result_failure.startswith("[red]")


class TestHelperIntegration:
    """Integration tests for helper composition."""

    def test_complete_workflow_success(self):
        """Test complete workflow: build description, format status."""
        reporter = SingleTransferProgressReporter(simple_mode=True)
        req = MockTransferRequest(
            source_image="nginx",
            source_tag="latest",
            target_repository="webserver",
            target_tag="prod"
        )

        # Build transfer description
        description = reporter._build_transfer_description(req, duration=15.0, success=True)

        # Format simple status
        status_lines = reporter._format_completion_status_simple(
            success=True,
            error_message=None,
            duration=15.0
        )

        # Both should indicate success
        assert "✓" in description
        assert "✓" in status_lines[0]
        assert "15.0s" in description
        assert "15.0s" in status_lines[0]

    def test_complete_workflow_failure(self):
        """Test complete workflow for failed transfer."""
        reporter = SingleTransferProgressReporter(simple_mode=True)
        req = MockTransferRequest(
            source_image="redis",
            source_tag="7.0",
            target_repository="cache",
            target_tag="prod"
        )

        # Build transfer description
        description = reporter._build_transfer_description(req, duration=8.0, success=False)

        # Format simple status with error
        error_msg = "Timeout during push"
        status_lines = reporter._format_completion_status_simple(
            success=False,
            error_message=error_msg,
            duration=8.0
        )

        # Both should indicate failure
        assert "✗" in description
        assert "✗" in status_lines[0]
        assert error_msg in status_lines[1]

    def test_simple_vs_rich_mode_consistency(self):
        """Test that simple and rich modes produce consistent information."""
        req = MockTransferRequest(
            source_image="mysql",
            source_tag="8.0",
            target_repository="db",
            target_tag="latest"
        )

        simple_reporter = SingleTransferProgressReporter(simple_mode=True)
        rich_reporter = SingleTransferProgressReporter(simple_mode=False)

        # Simple mode
        simple_desc = simple_reporter._build_transfer_description(req, duration=12.5, success=True)

        # Rich mode
        rich_desc = rich_reporter._format_rich_progress_description(req, duration=12.5, success=True)

        # Both should contain key information
        for desc in [simple_desc, rich_desc]:
            assert "mysql:8.0" in desc
            assert "db:latest" in desc

        # Rich should have markup, simple should not
        assert "[green]" not in simple_desc
        assert "[green]" in rich_desc
