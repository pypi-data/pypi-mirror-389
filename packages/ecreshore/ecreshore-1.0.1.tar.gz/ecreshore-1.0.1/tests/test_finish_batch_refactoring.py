"""Unit tests for finish_batch() refactoring - service layer only (NO Click testing).

Following brain/patterns:
- fixture-pattern.xml for reusable fixtures
- factory-fixture-pattern.xml for factory fixtures
- pure-function-extraction-pattern.xml for BatchSummary tests
- test-refactoring-pattern.xml for overall strategy
"""

import pytest
from unittest.mock import Mock, patch
import time
from src.ecreshore.services.batch_progress import (
    BatchProgressReporter,
    BatchSummary,
    TransferProgress,
    TransferStatus,
)
from src.ecreshore.services.batch_config import BatchTransferRequest


# Factory Fixtures following brain/patterns/factory-fixture-pattern.xml

@pytest.fixture
def make_transfer_progress():
    """Factory for TransferProgress objects with customizable fields.

    Follows brain pattern: factory-fixture-pattern for flexible test data creation.
    """
    def _factory(**kwargs):
        defaults = {
            'request': BatchTransferRequest(
                source='nginx',
                target='my-nginx',
                source_tag='latest',
                target_tag='v1.0'
            ),
            'status': TransferStatus.PENDING,
            'start_time': None,
            'end_time': None,
            'retry_count': 0,
            'error_message': None,
            'current_operation': '',
        }
        defaults.update(kwargs)
        return TransferProgress(**defaults)
    return _factory


@pytest.fixture
def mock_console():
    """Mock Rich Console for testing output."""
    return Mock()


@pytest.fixture
def mock_error_aggregator():
    """Mock BatchErrorAggregator."""
    aggregator = Mock()
    aggregator.set_transfer_counts = Mock()
    aggregator.get_error_summary = Mock(return_value={})  # Return empty dict by default
    aggregator.get_actionable_recommendations = Mock(return_value=[])
    return aggregator


@pytest.fixture
def reporter(mock_console, mock_error_aggregator):
    """BatchProgressReporter instance for testing."""
    reporter = BatchProgressReporter(console=mock_console, simple_mode=True)
    reporter.error_aggregator = mock_error_aggregator
    reporter.batch_start_time = time.time() - 10.0  # 10 seconds ago
    reporter.batch_end_time = time.time()
    reporter.transfers = {}
    return reporter


# Tests for _calculate_batch_summary() - Pure Function Tests

class TestCalculateBatchSummary:
    """Pure function tests for batch summary calculation."""

    def test_all_completed_success(self, reporter, make_transfer_progress):
        """All transfers completed successfully."""
        reporter.transfers = {
            'transfer_0': make_transfer_progress(status=TransferStatus.COMPLETED),
            'transfer_1': make_transfer_progress(status=TransferStatus.COMPLETED),
        }

        summary = reporter._calculate_batch_summary()

        assert summary.completed == 2
        assert summary.failed == 0
        assert summary.skipped == 0
        assert summary.total == 2
        assert summary.total_retries == 0

    def test_mixed_statuses(self, reporter, make_transfer_progress):
        """Mixed success, failure, and skipped."""
        reporter.transfers = {
            'transfer_0': make_transfer_progress(status=TransferStatus.COMPLETED),
            'transfer_1': make_transfer_progress(status=TransferStatus.FAILED, retry_count=2),
            'transfer_2': make_transfer_progress(status=TransferStatus.SKIPPED),
        }

        summary = reporter._calculate_batch_summary()

        assert summary.completed == 1
        assert summary.failed == 1
        assert summary.skipped == 1
        assert summary.total == 3
        assert summary.total_retries == 2

    def test_duration_calculation(self, reporter):
        """Duration calculated from start/end times."""
        reporter.batch_start_time = 100.0
        reporter.batch_end_time = 110.0
        reporter.transfers = {}

        summary = reporter._calculate_batch_summary()

        assert summary.duration == 10.0

    def test_all_failed(self, reporter, make_transfer_progress):
        """All transfers failed."""
        reporter.transfers = {
            'transfer_0': make_transfer_progress(status=TransferStatus.FAILED, retry_count=1),
            'transfer_1': make_transfer_progress(status=TransferStatus.FAILED, retry_count=3),
        }

        summary = reporter._calculate_batch_summary()

        assert summary.completed == 0
        assert summary.failed == 2
        assert summary.total_retries == 4

    def test_retry_accumulation(self, reporter, make_transfer_progress):
        """Retries accumulated across all transfers."""
        reporter.transfers = {
            'transfer_0': make_transfer_progress(status=TransferStatus.COMPLETED, retry_count=2),
            'transfer_1': make_transfer_progress(status=TransferStatus.FAILED, retry_count=3),
        }

        summary = reporter._calculate_batch_summary()

        assert summary.total_retries == 5

    def test_empty_transfers(self, reporter):
        """Empty transfers dict handled correctly."""
        reporter.transfers = {}

        summary = reporter._calculate_batch_summary()

        assert summary.total == 0
        assert summary.completed == 0

    def test_batch_end_time_stored(self, reporter):
        """batch_end_time stored in summary."""
        reporter.batch_end_time = 12345.0
        reporter.transfers = {}

        summary = reporter._calculate_batch_summary()

        assert summary.batch_end_time == 12345.0

    def test_none_start_time_fallback(self, reporter):
        """None start_time uses end_time as fallback."""
        reporter.batch_start_time = None
        reporter.batch_end_time = 100.0
        reporter.transfers = {}

        summary = reporter._calculate_batch_summary()

        assert summary.duration == 0.0


# Tests for _build_transfer_history()

class TestBuildTransferHistory:
    """Tests for transfer history building."""

    def test_completed_transfer_format(self, reporter, make_transfer_progress):
        """Completed transfer formatted with green and checkmark."""
        reporter.transfers = {
            'transfer_0': make_transfer_progress(status=TransferStatus.COMPLETED)
        }

        history = reporter._build_transfer_history()

        assert len(history) == 1
        assert '[green]' in history[0]
        assert '✅' in history[0]
        assert 'nginx:latest → my-nginx:v1.0' in history[0]
        assert 'Completed' in history[0]

    def test_failed_transfer_format(self, reporter, make_transfer_progress):
        """Failed transfer formatted with red and X."""
        reporter.transfers = {
            'transfer_0': make_transfer_progress(status=TransferStatus.FAILED)
        }

        history = reporter._build_transfer_history()

        assert '[red]' in history[0]
        assert '❌' in history[0]
        assert 'Failed' in history[0]

    def test_skipped_transfer_format(self, reporter, make_transfer_progress):
        """Skipped transfer formatted with dim."""
        reporter.transfers = {
            'transfer_0': make_transfer_progress(status=TransferStatus.SKIPPED)
        }

        history = reporter._build_transfer_history()

        assert '[dim]' in history[0]
        assert '‥' in history[0]
        assert 'Skipped' in history[0]

    def test_transfer_ordering(self, reporter, make_transfer_progress):
        """Transfers ordered by transfer_id."""
        reporter.transfers = {
            'transfer_2': make_transfer_progress(status=TransferStatus.COMPLETED),
            'transfer_0': make_transfer_progress(status=TransferStatus.FAILED),
            'transfer_1': make_transfer_progress(status=TransferStatus.SKIPPED),
        }

        history = reporter._build_transfer_history()

        # Should be ordered transfer_0, transfer_1, transfer_2
        assert 'Transfer 1:' in history[0]  # transfer_0
        assert 'Transfer 2:' in history[1]  # transfer_1
        assert 'Transfer 3:' in history[2]  # transfer_2

    def test_multiple_transfers_unique_content(self, reporter, make_transfer_progress):
        """Each transfer has unique content in history."""
        reporter.transfers = {
            'transfer_0': make_transfer_progress(
                request=BatchTransferRequest(
                    source='nginx', target='my-nginx',
                    source_tag='1.0', target_tag='v1'
                ),
                status=TransferStatus.COMPLETED
            ),
            'transfer_1': make_transfer_progress(
                request=BatchTransferRequest(
                    source='redis', target='my-redis',
                    source_tag='7.0', target_tag='v2'
                ),
                status=TransferStatus.FAILED
            ),
        }

        history = reporter._build_transfer_history()

        assert 'nginx:1.0 → my-nginx:v1' in history[0]
        assert 'redis:7.0 → my-redis:v2' in history[1]


# Tests for _display_simple_summary()

class TestDisplaySimpleSummary:
    """Tests for simple mode summary display."""

    def test_all_success_no_skipped(self, reporter, mock_console):
        """All successful, no skipped - success message."""
        summary = BatchSummary(
            completed=5, failed=0, skipped=0, total=5,
            duration=10.5, total_retries=0, batch_end_time=time.time()
        )

        reporter._display_simple_summary(summary)

        calls = [str(call) for call in mock_console.print.call_args_list]
        output = ''.join(calls)
        assert '✓ Batch completed successfully' in output
        assert '5/5 transfers' in output
        assert '10.5s' in output

    def test_success_with_skipped(self, reporter, mock_console):
        """Success with some skipped transfers."""
        summary = BatchSummary(
            completed=3, failed=0, skipped=2, total=5,
            duration=8.0, total_retries=0, batch_end_time=time.time()
        )

        reporter._display_simple_summary(summary)

        calls = [str(call) for call in mock_console.print.call_args_list]
        output = ''.join(calls)
        assert '✓ Batch completed' in output
        assert '3/5 transferred' in output
        assert '2 skipped' in output

    def test_with_failures_no_skipped(self, reporter, mock_console):
        """Failures without skipped - warning message."""
        summary = BatchSummary(
            completed=3, failed=2, skipped=0, total=5,
            duration=8.0, total_retries=1, batch_end_time=time.time()
        )

        reporter._display_simple_summary(summary)

        calls = [str(call) for call in mock_console.print.call_args_list]
        output = ''.join(calls)
        assert '⚠ Batch completed with errors' in output
        assert '3/5 successful' in output
        assert '2 failed' in output

    def test_failures_with_skipped(self, reporter, mock_console):
        """Failures and skipped - comprehensive message."""
        summary = BatchSummary(
            completed=2, failed=2, skipped=1, total=5,
            duration=7.0, total_retries=3, batch_end_time=time.time()
        )

        reporter._display_simple_summary(summary)

        calls = [str(call) for call in mock_console.print.call_args_list]
        output = ''.join(calls)
        assert '⚠ Batch completed' in output
        assert '2 successful' in output
        assert '2 failed' in output
        assert '1 skipped' in output

    def test_retry_count_displayed(self, reporter, mock_console):
        """Retry count displayed when > 0."""
        summary = BatchSummary(
            completed=5, failed=0, skipped=0, total=5,
            duration=10.0, total_retries=3, batch_end_time=time.time()
        )

        reporter._display_simple_summary(summary)

        calls = [str(call) for call in mock_console.print.call_args_list]
        output = ''.join(calls)
        assert 'Total retries: 3' in output

    def test_no_retry_count_when_zero(self, reporter, mock_console):
        """Retry count not displayed when 0."""
        summary = BatchSummary(
            completed=5, failed=0, skipped=0, total=5,
            duration=10.0, total_retries=0, batch_end_time=time.time()
        )

        reporter._display_simple_summary(summary)

        calls = [str(call) for call in mock_console.print.call_args_list]
        output = ''.join(calls)
        assert 'Total retries' not in output

    @patch.object(BatchProgressReporter, '_show_error_summary')
    def test_error_summary_called_on_failures(self, mock_error_summary, reporter, mock_console):
        """Error summary called when failures present."""
        summary = BatchSummary(
            completed=3, failed=2, skipped=0, total=5,
            duration=8.0, total_retries=0, batch_end_time=time.time()
        )

        reporter._display_simple_summary(summary)

        mock_error_summary.assert_called_once_with(simple_mode=True)

    @patch.object(BatchProgressReporter, '_show_error_summary')
    def test_error_summary_not_called_on_success(self, mock_error_summary, reporter, mock_console):
        """Error summary not called when all successful."""
        summary = BatchSummary(
            completed=5, failed=0, skipped=0, total=5,
            duration=10.0, total_retries=0, batch_end_time=time.time()
        )

        reporter._display_simple_summary(summary)

        mock_error_summary.assert_not_called()


# Tests for _display_rich_summary()

class TestDisplayRichSummary:
    """Tests for rich mode summary display."""

    def test_all_success_message(self, reporter, mock_console):
        """All successful - green bold message."""
        summary = BatchSummary(
            completed=5, failed=0, skipped=0, total=5,
            duration=10.5, total_retries=0, batch_end_time=time.time()
        )

        reporter._display_rich_summary(summary)

        calls = [str(call) for call in mock_console.print.call_args_list]
        output = ''.join(calls)
        assert '[bold green]✓ All 5 transfers completed successfully!' in output

    def test_partial_completion_message(self, reporter, mock_console):
        """Partial completion - yellow warning."""
        summary = BatchSummary(
            completed=3, failed=2, skipped=0, total=5,
            duration=8.0, total_retries=1, batch_end_time=time.time()
        )

        reporter._display_rich_summary(summary)

        calls = [str(call) for call in mock_console.print.call_args_list]
        output = ''.join(calls)
        assert '[bold yellow]⚠ Batch partially completed' in output
        assert '[green]Successful: 3[/green]' in output
        assert '[red]Failed: 2[/red]' in output

    def test_live_display_stopped(self, reporter, mock_console, make_transfer_progress):
        """Live display stopped when present."""
        reporter.live = Mock()
        reporter.transfers = {
            'transfer_0': make_transfer_progress(status=TransferStatus.COMPLETED)
        }
        summary = BatchSummary(
            completed=1, failed=0, skipped=0, total=1,
            duration=5.0, total_retries=0, batch_end_time=time.time()
        )

        reporter._display_rich_summary(summary)

        reporter.live.stop.assert_called_once()

    def test_buffered_errors_flushed(self, reporter, mock_console):
        """Buffered errors flushed after live display stops."""
        reporter.live = Mock()
        reporter._buffered_errors = [
            ('Error 1', {}),
            ('Error 2', {'extra': 'data'}),
        ]
        reporter.base_reporter = Mock()
        summary = BatchSummary(
            completed=1, failed=0, skipped=0, total=1,
            duration=5.0, total_retries=0, batch_end_time=time.time()
        )

        reporter._display_rich_summary(summary)

        # Verify errors flushed
        assert len(reporter._buffered_errors) == 0
        assert reporter.base_reporter.error.call_count == 2

    def test_transfer_history_displayed(self, reporter, mock_console, make_transfer_progress):
        """Transfer history displayed when live present."""
        reporter.live = Mock()
        reporter.transfers = {
            'transfer_0': make_transfer_progress(status=TransferStatus.COMPLETED)
        }
        summary = BatchSummary(
            completed=1, failed=0, skipped=0, total=1,
            duration=5.0, total_retries=0, batch_end_time=time.time()
        )

        reporter._display_rich_summary(summary)

        calls = [str(call) for call in mock_console.print.call_args_list]
        output = ''.join(calls)
        assert '[bold]Transfer Summary:' in output

    @patch.object(BatchProgressReporter, '_show_error_summary')
    def test_error_summary_called_on_failures(self, mock_error_summary, reporter, mock_console):
        """Error summary called with simple_mode=False when failures."""
        summary = BatchSummary(
            completed=3, failed=2, skipped=0, total=5,
            duration=8.0, total_retries=0, batch_end_time=time.time()
        )

        reporter._display_rich_summary(summary)

        mock_error_summary.assert_called_once_with(simple_mode=False)

    def test_summary_table_created(self, reporter, mock_console):
        """Summary table with stats created."""
        summary = BatchSummary(
            completed=3, failed=2, skipped=1, total=6,
            duration=12.5, total_retries=4, batch_end_time=time.time()
        )

        reporter._display_rich_summary(summary)

        # Panel with table should be printed
        calls = [str(call) for call in mock_console.print.call_args_list]
        # Check that Panel was created (it will be in one of the calls)
        assert any('Panel' in str(call) for call in calls)


# Integration Tests for finish_batch()

class TestFinishBatchIntegration:
    """Integration tests for finish_batch orchestration."""

    def test_simple_mode_orchestration(
        self, reporter, make_transfer_progress,
        mock_console, mock_error_aggregator
    ):
        """finish_batch orchestrates all steps in simple mode."""
        reporter.transfers = {
            'transfer_0': make_transfer_progress(status=TransferStatus.COMPLETED),
            'transfer_1': make_transfer_progress(status=TransferStatus.FAILED, retry_count=1),
        }

        reporter.finish_batch()

        # Verify batch end time set
        assert reporter.batch_end_time is not None

        # Verify error aggregator called with correct counts
        mock_error_aggregator.set_transfer_counts.assert_called_once_with(2, 1, 1, 0)

        # Verify console output happened
        assert mock_console.print.called

    def test_rich_mode_orchestration(
        self, reporter, make_transfer_progress,
        mock_console, mock_error_aggregator
    ):
        """finish_batch orchestrates all steps in rich mode."""
        reporter.simple_mode = False
        reporter.transfers = {
            'transfer_0': make_transfer_progress(status=TransferStatus.COMPLETED),
        }

        reporter.finish_batch()

        # Verify orchestration steps
        assert reporter.batch_end_time is not None
        mock_error_aggregator.set_transfer_counts.assert_called_once_with(1, 1, 0, 0)

        # Verify rich mode output (contains rich formatting)
        calls = [str(call) for call in mock_console.print.call_args_list]
        assert any('[bold green]' in str(call) for call in calls)
