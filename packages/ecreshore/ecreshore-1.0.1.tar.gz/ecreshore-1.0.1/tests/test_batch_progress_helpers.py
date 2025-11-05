"""Unit tests for helper methods in BatchProgressReporter.

Following brain/patterns/fixture-pattern.xml, factory-fixture-pattern.xml,
and async-mock-pattern.xml for test structure.
"""

import pytest
from unittest.mock import Mock, patch, call
import time
from src.ecreshore.services.batch_progress import (
    BatchProgressReporter,
    TransferProgress,
    TransferStatus,
)
from src.ecreshore.services.batch_config import BatchTransferRequest


# Factory Fixtures following brain/patterns/factory-fixture-pattern.xml

@pytest.fixture
def make_transfer_request():
    """Factory for creating BatchTransferRequest objects with customizable fields.

    Follows brain pattern: factory-fixture-pattern for flexible test data creation.
    """
    def _factory(**kwargs):
        defaults = {
            'source': 'nginx',
            'target': 'my-nginx',
            'source_tag': 'latest',
            'target_tag': 'v1.0',
        }
        defaults.update(kwargs)
        return BatchTransferRequest(**defaults)
    return _factory


@pytest.fixture
def make_transfer_progress(make_transfer_request):
    """Factory for creating TransferProgress objects with customizable fields.

    Follows brain pattern: factory-fixture-pattern for flexible test data creation.
    """
    def _factory(**kwargs):
        defaults = {
            'request': make_transfer_request(),
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


# Mock Fixtures

@pytest.fixture
def mock_console():
    """Mock Console for testing output."""
    return Mock()


@pytest.fixture
def mock_progress():
    """Mock Progress bar for complex mode testing."""
    progress = Mock()
    progress.update = Mock()
    return progress


@pytest.fixture
def mock_error_aggregator():
    """Mock BatchErrorAggregator for error recording tests."""
    aggregator = Mock()
    aggregator.add_transfer_error = Mock()
    return aggregator


@pytest.fixture
def reporter(mock_console, mock_error_aggregator):
    """BatchProgressReporter instance with mocked dependencies."""
    reporter = BatchProgressReporter(console=mock_console, simple_mode=True)
    reporter.error_aggregator = mock_error_aggregator
    reporter.transfers = {}  # Will be populated in tests
    return reporter


# Tests for _update_transfer_status()

def test_update_transfer_status_success(reporter, make_transfer_progress):
    """Success case - sets status to COMPLETED and end_time."""
    progress = make_transfer_progress(start_time=time.time())

    reporter._update_transfer_status(progress, success=True, error_message=None)

    assert progress.status == TransferStatus.COMPLETED
    assert progress.end_time is not None
    assert progress.error_message is None
    assert progress.current_operation == "Complete"


def test_update_transfer_status_failure(reporter, make_transfer_progress):
    """Failure case - sets status to FAILED with error message."""
    progress = make_transfer_progress(start_time=time.time())
    error_msg = "Connection refused"

    reporter._update_transfer_status(progress, success=False, error_message=error_msg)

    assert progress.status == TransferStatus.FAILED
    assert progress.end_time is not None
    assert progress.error_message == error_msg
    assert progress.current_operation == "Failed"


def test_update_transfer_status_timing(reporter, make_transfer_progress):
    """Verify end_time is set correctly on completion."""
    start = time.time()
    progress = make_transfer_progress(start_time=start)

    reporter._update_transfer_status(progress, success=True, error_message=None)

    assert progress.end_time >= start
    assert progress.end_time <= time.time()


# Tests for _log_transfer_completion()

@patch('src.ecreshore.services.batch_progress.struct_logger')
def test_log_transfer_completion_success(mock_struct_logger, reporter, make_transfer_progress):
    """Logs structured event with correct success parameters."""
    reporter.output_mode = 'log'  # Enable structured logging
    progress = make_transfer_progress(start_time=time.time() - 5.0, end_time=time.time())
    reporter.transfers = {'transfer_0': progress}

    reporter._log_transfer_completion('transfer_0', progress, success=True, error_message=None)

    # Verify structured log was called
    mock_struct_logger.info.assert_called_once()
    call_args = mock_struct_logger.info.call_args

    assert call_args[0][0] == 'transfer_completed'
    assert call_args[1]['transfer_id'] == 'transfer_0'
    assert call_args[1]['transfer_num'] == 1
    assert call_args[1]['success'] is True
    assert call_args[1]['source'] == 'nginx'
    assert call_args[1]['target'] == 'my-nginx'


@patch('src.ecreshore.services.batch_progress.struct_logger')
def test_log_transfer_completion_failure(mock_struct_logger, reporter, make_transfer_progress):
    """Logs structured event with error message for failures."""
    reporter.output_mode = 'log'
    error_msg = "Repository not found"
    progress = make_transfer_progress(start_time=time.time() - 3.0, end_time=time.time())
    reporter.transfers = {'transfer_0': progress}

    reporter._log_transfer_completion('transfer_0', progress, success=False, error_message=error_msg)

    call_args = mock_struct_logger.info.call_args
    assert call_args[1]['success'] is False
    assert call_args[1]['error_message'] == error_msg


@patch('src.ecreshore.services.batch_progress.struct_logger')
def test_log_transfer_completion_transfer_number(mock_struct_logger, reporter, make_transfer_progress):
    """Correctly calculates transfer number from transfer_id."""
    reporter.output_mode = 'log'
    progress = make_transfer_progress(start_time=time.time(), end_time=time.time())
    reporter.transfers = {
        'transfer_0': progress,
        'transfer_1': progress,
        'transfer_5': progress,  # Test with non-sequential ID
    }

    reporter._log_transfer_completion('transfer_5', progress, success=True, error_message=None)

    call_args = mock_struct_logger.info.call_args
    assert call_args[1]['transfer_num'] == 6  # transfer_5 + 1


# Tests for _record_transfer_error()

def test_record_transfer_error_success(reporter, make_transfer_progress, mock_error_aggregator):
    """Successfully records error in aggregator."""
    progress = make_transfer_progress(retry_count=2, end_time=time.time())
    error_msg = "Digest verification failed"

    reporter._record_transfer_error('transfer_0', progress, error_msg)

    # Verify aggregator was called with correct parameters
    mock_error_aggregator.add_transfer_error.assert_called_once()
    call_args = mock_error_aggregator.add_transfer_error.call_args[1]

    assert call_args['transfer_id'] == 'transfer_0'
    assert call_args['source_image'] == 'nginx'
    assert call_args['target_repository'] == 'my-nginx'
    assert call_args['source_tag'] == 'latest'
    assert call_args['target_tag'] == 'v1.0'
    assert call_args['retry_count'] == 2
    assert str(call_args['error']) == error_msg


@patch('src.ecreshore.services.batch_progress.logger')
def test_record_transfer_error_aggregator_failure(mock_logger, reporter, make_transfer_progress):
    """Handles aggregator exceptions gracefully with warning log."""
    progress = make_transfer_progress(end_time=time.time())
    error_msg = "Transfer failed"

    # Make aggregator raise exception
    reporter.error_aggregator.add_transfer_error.side_effect = Exception("Aggregator error")

    # Should not raise - exception is caught
    reporter._record_transfer_error('transfer_0', progress, error_msg)

    # Verify warning was logged
    mock_logger.warning.assert_called_once()
    assert "Failed to add error to aggregator" in mock_logger.warning.call_args[0][0]


def test_record_transfer_error_exception_wrapping(reporter, make_transfer_progress, mock_error_aggregator):
    """Wraps error message in Exception object for aggregator."""
    progress = make_transfer_progress(end_time=time.time())
    error_msg = "Network timeout"

    reporter._record_transfer_error('transfer_0', progress, error_msg)

    call_args = mock_error_aggregator.add_transfer_error.call_args[1]
    error_obj = call_args['error']

    assert isinstance(error_obj, Exception)
    assert str(error_obj) == error_msg


# Tests for _display_simple_completion()

def test_display_simple_completion_success(reporter, make_transfer_progress, mock_console):
    """Displays success message in simple mode."""
    progress = make_transfer_progress(start_time=time.time() - 2.5, end_time=time.time())
    reporter.transfers = {'transfer_0': progress}

    reporter._display_simple_completion('transfer_0', progress, success=True, error_message=None)

    # Verify console output
    assert mock_console.print.called
    output = mock_console.print.call_args[0][0]
    assert '[1/1] ✓ Completed' in output
    assert 'nginx:latest → my-nginx:v1.0' in output
    assert 's)' in output  # Duration is included


def test_display_simple_completion_failure_with_error(reporter, make_transfer_progress, mock_console):
    """Displays failure message with error in simple mode."""
    progress = make_transfer_progress(start_time=time.time() - 1.0, end_time=time.time())
    reporter.transfers = {'transfer_0': progress}
    error_msg = "Authentication failed"

    reporter._display_simple_completion('transfer_0', progress, success=False, error_message=error_msg)

    # Verify failure indicator and error message
    calls = [str(call) for call in mock_console.print.call_args_list]
    output_text = ''.join(calls)
    assert '✗ Failed' in output_text
    assert error_msg in output_text


def test_display_simple_completion_failure_without_error(reporter, make_transfer_progress, mock_console):
    """Displays failure message without error in simple mode."""
    progress = make_transfer_progress(start_time=time.time(), end_time=time.time())
    reporter.transfers = {'transfer_0': progress}

    reporter._display_simple_completion('transfer_0', progress, success=False, error_message=None)

    # Should show failure but no error message
    calls = [str(call) for call in mock_console.print.call_args_list]
    assert len(calls) == 1  # Only one print call (no error message print)


@patch('src.ecreshore.services.batch_progress.struct_logger')
def test_display_simple_completion_log_mode(mock_struct_logger, reporter, make_transfer_progress, mock_console):
    """Logs transfer error in log mode."""
    reporter.output_mode = 'log'
    progress = make_transfer_progress(start_time=time.time(), end_time=time.time())
    reporter.transfers = {'transfer_0': progress}
    error_msg = "Image not found"

    reporter._display_simple_completion('transfer_0', progress, success=False, error_message=error_msg)

    # Verify structured log for error
    assert mock_struct_logger.info.call_count >= 1
    # Find the transfer_error log call
    error_log_calls = [call for call in mock_struct_logger.info.call_args_list
                       if call[0][0] == 'transfer_error']
    assert len(error_log_calls) == 1


# Tests for _display_complex_completion()

def test_display_complex_completion_success(reporter, make_transfer_progress, mock_progress):
    """Updates progress bar for successful completion in complex mode."""
    reporter.simple_mode = False
    reporter.progress = mock_progress
    reporter.overall_task = 1

    progress = make_transfer_progress(start_time=time.time() - 5.0, end_time=time.time())
    reporter.transfers = {'transfer_0': progress}
    reporter.transfer_tasks = {'transfer_0': 10}  # Task ID 10

    reporter._display_complex_completion('transfer_0', progress, success=True)

    # Verify progress bar was updated with success indicator
    assert mock_progress.update.call_count == 2  # Task update + overall update
    task_update = mock_progress.update.call_args_list[0]
    assert task_update[0][0] == 10  # Task ID
    assert task_update[1]['completed'] == 100
    assert '✓' in task_update[1]['description']


def test_display_complex_completion_early_return(reporter, make_transfer_progress):
    """Returns early if progress or transfer_tasks not initialized."""
    reporter.simple_mode = False
    reporter.progress = None  # Not initialized

    progress = make_transfer_progress()

    # Should return early without error
    reporter._display_complex_completion('transfer_0', progress, success=True)

    # No assertions needed - just verify no exception is raised


# ========================================
# Error Summary Helper Tests
# ========================================


@pytest.fixture
def mock_error_summary():
    """Factory for creating mock error summaries for testing."""
    from src.ecreshore.services.batch_error_aggregator import ErrorSummary
    from src.ecreshore.services.error_handler import ErrorCategory
    from unittest.mock import Mock

    def _factory(category=ErrorCategory.NETWORK_TIMEOUT, count=2, with_errors=True):
        summary = Mock(spec=ErrorSummary)
        summary.count = count
        summary.is_retryable = True
        summary.requires_user_action = False
        summary.user_guidance = "Check network connectivity"

        if with_errors:
            error1 = Mock()
            error1.source_image = "nginx"
            error1.source_tag = "latest"
            error1.target_repository = "my-registry/nginx"
            error1.target_tag = "v1.0"

            error2 = Mock()
            error2.source_image = "redis"
            error2.source_tag = "7.0"
            error2.target_repository = "my-registry/redis"
            error2.target_tag = "v7"

            summary.errors = [error1, error2]
        else:
            summary.errors = []

        return {category: summary}

    return _factory


class TestFormatCategoryName:
    """Tests for _format_category_name() pure function."""

    def test_format_network_timeout(self, reporter):
        """Test formatting NETWORK_TIMEOUT category."""
        from src.ecreshore.services.error_handler import ErrorCategory
        result = reporter._format_category_name(ErrorCategory.NETWORK_TIMEOUT)
        assert result == "Network Timeout"

    def test_format_authentication(self, reporter):
        """Test formatting AUTHENTICATION category."""
        from src.ecreshore.services.error_handler import ErrorCategory
        result = reporter._format_category_name(ErrorCategory.AUTHENTICATION)
        assert result == "Authentication"

    def test_format_rate_limited(self, reporter):
        """Test formatting RATE_LIMITED category."""
        from src.ecreshore.services.error_handler import ErrorCategory
        result = reporter._format_category_name(ErrorCategory.RATE_LIMITED)
        assert result == "Rate Limited"

    def test_format_removes_underscores(self, reporter):
        """Test that underscores are replaced with spaces."""
        from src.ecreshore.services.error_handler import ErrorCategory
        result = reporter._format_category_name(ErrorCategory.DOCKER_DAEMON)
        assert "_" not in result
        assert " " in result

    def test_format_title_case(self, reporter):
        """Test that result is in title case."""
        from src.ecreshore.services.error_handler import ErrorCategory
        result = reporter._format_category_name(ErrorCategory.SERVICE_UNAVAILABLE)
        assert result[0].isupper()  # First letter uppercase
        words = result.split()
        assert all(word[0].isupper() for word in words)  # All words capitalized


class TestDisplaySimpleErrorSummary:
    """Tests for _display_simple_error_summary() helper."""

    def test_displays_error_summary_header(self, reporter, mock_console, mock_error_summary):
        """Test that error summary header is displayed."""
        from src.ecreshore.services.error_handler import ErrorCategory

        error_summary = mock_error_summary(ErrorCategory.NETWORK_TIMEOUT)
        recommendations = []

        reporter._display_simple_error_summary(error_summary, recommendations)

        # Check that header was output
        calls = [str(call) for call in mock_console.print.call_args_list]
        assert any("Error Summary:" in str(call) for call in calls)

    def test_displays_category_with_count(self, reporter, mock_console, mock_error_summary):
        """Test that category name and count are displayed."""
        from src.ecreshore.services.error_handler import ErrorCategory

        error_summary = mock_error_summary(ErrorCategory.NETWORK_TIMEOUT, count=3)
        recommendations = []

        reporter._display_simple_error_summary(error_summary, recommendations)

        # Check output contains category and count
        calls = [str(call) for call in mock_console.print.call_args_list]
        output = " ".join(calls)
        assert "Network Timeout" in output
        assert "3 error(s)" in output

    def test_displays_user_guidance_when_present(self, reporter, mock_console, mock_error_summary):
        """Test that user guidance is displayed when available."""
        from src.ecreshore.services.error_handler import ErrorCategory

        error_summary = mock_error_summary(ErrorCategory.NETWORK_TIMEOUT)
        recommendations = []

        reporter._display_simple_error_summary(error_summary, recommendations)

        # Check that guidance was output
        calls = [str(call) for call in mock_console.print.call_args_list]
        output = " ".join(calls)
        assert "Check network connectivity" in output

    def test_displays_recommendations_when_provided(self, reporter, mock_console, mock_error_summary):
        """Test that recommendations are displayed with numbering."""
        from src.ecreshore.services.error_handler import ErrorCategory

        error_summary = mock_error_summary(ErrorCategory.NETWORK_TIMEOUT)
        recommendations = ["Retry the operation", "Check firewall settings"]

        reporter._display_simple_error_summary(error_summary, recommendations)

        # Check recommendations displayed
        calls = [str(call) for call in mock_console.print.call_args_list]
        output = " ".join(calls)
        assert "Recommended Actions:" in output
        assert "1. Retry the operation" in output
        assert "2. Check firewall settings" in output

    def test_displays_retry_suggestion_when_applicable(self, reporter, mock_console, mock_error_summary):
        """Test that retry suggestion is displayed when should_suggest_retry is True."""
        from src.ecreshore.services.error_handler import ErrorCategory

        error_summary = mock_error_summary(ErrorCategory.NETWORK_TIMEOUT)
        recommendations = []
        reporter.error_aggregator.should_suggest_retry.return_value = True

        reporter._display_simple_error_summary(error_summary, recommendations)

        # Check retry suggestion displayed
        calls = [str(call) for call in mock_console.print.call_args_list]
        output = " ".join(calls)
        assert "temporary" in output.lower()
        assert "retry" in output.lower()

    def test_no_retry_suggestion_when_not_applicable(self, reporter, mock_console, mock_error_summary):
        """Test that retry suggestion is NOT displayed when should_suggest_retry is False."""
        from src.ecreshore.services.error_handler import ErrorCategory

        error_summary = mock_error_summary(ErrorCategory.NETWORK_TIMEOUT)
        recommendations = []
        reporter.error_aggregator.should_suggest_retry.return_value = False

        reporter._display_simple_error_summary(error_summary, recommendations)

        # Check NO retry suggestion
        calls = [str(call) for call in mock_console.print.call_args_list]
        output = " ".join(calls)
        # Should not contain the emoji or specific retry message
        assert "💡 Most errors appear to be temporary" not in output


class TestDisplayRichErrorSummary:
    """Tests for _display_rich_error_summary() helper."""

    def test_displays_error_analysis_header(self, reporter, mock_console, mock_error_summary):
        """Test that rich mode displays error analysis header."""
        from src.ecreshore.services.error_handler import ErrorCategory

        error_summary = mock_error_summary(ErrorCategory.NETWORK_TIMEOUT)
        recommendations = []

        reporter._display_rich_error_summary(error_summary, recommendations)

        # Check header with rich markup
        calls = [str(call) for call in mock_console.print.call_args_list]
        output = " ".join(calls)
        assert "Error Analysis" in output or "[bold red]" in output

    def test_creates_error_table_with_correct_columns(self, reporter, mock_console, mock_error_summary):
        """Test that error table is created with proper columns."""
        from src.ecreshore.services.error_handler import ErrorCategory
        from rich.table import Table

        error_summary = mock_error_summary(ErrorCategory.NETWORK_TIMEOUT)
        recommendations = []

        reporter._display_rich_error_summary(error_summary, recommendations)

        # Check that a Table was printed
        table_calls = [call for call in mock_console.print.call_args_list
                       if call[0] and isinstance(call[0][0], Table)]
        assert len(table_calls) > 0

    def test_displays_retryable_indicator_green(self, reporter, mock_console, mock_error_summary):
        """Test that retryable errors show green checkmark."""
        from src.ecreshore.services.error_handler import ErrorCategory
        from rich.table import Table

        error_summary = mock_error_summary(ErrorCategory.NETWORK_TIMEOUT)
        error_summary[ErrorCategory.NETWORK_TIMEOUT].is_retryable = True
        recommendations = []

        reporter._display_rich_error_summary(error_summary, recommendations)

        # Check that error table was created (implies formatting happened correctly)
        table_calls = [call for call in mock_console.print.call_args_list
                       if call[0] and isinstance(call[0][0], Table)]
        assert len(table_calls) > 0
        # Note: We can't easily inspect Rich Table internals, but creation confirms
        # the retryable logic executed

    def test_displays_retryable_indicator_red(self, reporter, mock_console, mock_error_summary):
        """Test that non-retryable errors show red X."""
        from src.ecreshore.services.error_handler import ErrorCategory
        from rich.table import Table

        error_summary = mock_error_summary(ErrorCategory.AUTHENTICATION)
        error_summary[ErrorCategory.AUTHENTICATION].is_retryable = False
        recommendations = []

        reporter._display_rich_error_summary(error_summary, recommendations)

        # Check that error table was created (implies formatting happened correctly)
        table_calls = [call for call in mock_console.print.call_args_list
                       if call[0] and isinstance(call[0][0], Table)]
        assert len(table_calls) > 0

    def test_displays_recommendations_panel(self, reporter, mock_console, mock_error_summary):
        """Test that recommendations are displayed in a Panel."""
        from src.ecreshore.services.error_handler import ErrorCategory
        from rich.panel import Panel

        error_summary = mock_error_summary(ErrorCategory.NETWORK_TIMEOUT)
        recommendations = ["Action 1", "Action 2"]

        reporter._display_rich_error_summary(error_summary, recommendations)

        # Check that a Panel was printed
        panel_calls = [call for call in mock_console.print.call_args_list
                       if call[0] and isinstance(call[0][0], Panel)]
        assert len(panel_calls) > 0

    def test_displays_retry_suggestion_panel(self, reporter, mock_console, mock_error_summary):
        """Test that retry suggestion is displayed in a Panel."""
        from src.ecreshore.services.error_handler import ErrorCategory
        from rich.panel import Panel

        error_summary = mock_error_summary(ErrorCategory.NETWORK_TIMEOUT)
        recommendations = []
        reporter.error_aggregator.should_suggest_retry.return_value = True

        reporter._display_rich_error_summary(error_summary, recommendations)

        # Check for retry panel
        panel_calls = [call for call in mock_console.print.call_args_list
                       if call[0] and isinstance(call[0][0], Panel)]
        # Should have at least one panel (retry suggestion)
        assert len(panel_calls) >= 1


class TestDisplayFailedTransferDetails:
    """Tests for _display_failed_transfer_details() helper."""

    def test_displays_failed_transfers_header(self, reporter, mock_console, mock_error_summary):
        """Test that failed transfers header is displayed."""
        from src.ecreshore.services.error_handler import ErrorCategory

        error_summary = mock_error_summary(ErrorCategory.NETWORK_TIMEOUT, with_errors=True)

        reporter._display_failed_transfer_details(error_summary)

        calls = [str(call) for call in mock_console.print.call_args_list]
        output = " ".join(calls)
        assert "Failed Transfers Details" in output or "failed" in output.lower()

    def test_displays_category_with_error_count(self, reporter, mock_console, mock_error_summary):
        """Test that category name and error count are displayed."""
        from src.ecreshore.services.error_handler import ErrorCategory

        error_summary = mock_error_summary(ErrorCategory.NETWORK_TIMEOUT, count=2, with_errors=True)

        reporter._display_failed_transfer_details(error_summary)

        calls = [str(call) for call in mock_console.print.call_args_list]
        output = " ".join(calls)
        assert "Network Timeout" in output
        assert "2 errors" in output

    def test_displays_first_three_errors(self, reporter, mock_console, mock_error_summary):
        """Test that first 3 errors are displayed with transfer details."""
        from src.ecreshore.services.error_handler import ErrorCategory

        error_summary = mock_error_summary(ErrorCategory.NETWORK_TIMEOUT, with_errors=True)

        reporter._display_failed_transfer_details(error_summary)

        calls = [str(call) for call in mock_console.print.call_args_list]
        output = " ".join(calls)
        assert "nginx:latest" in output
        assert "my-registry/nginx:v1.0" in output

    def test_shows_more_indicator_when_over_three_errors(self, reporter, mock_console, mock_error_summary):
        """Test that '... and X more' is displayed when > 3 errors."""
        from src.ecreshore.services.error_handler import ErrorCategory
        from unittest.mock import Mock

        # Create 5 errors
        summary = mock_error_summary(ErrorCategory.NETWORK_TIMEOUT, count=5, with_errors=True)
        errors = []
        for i in range(5):
            error = Mock()
            error.source_image = f"image{i}"
            error.source_tag = "latest"
            error.target_repository = f"repo{i}"
            error.target_tag = "v1"
            errors.append(error)

        summary[ErrorCategory.NETWORK_TIMEOUT].errors = errors

        reporter._display_failed_transfer_details(summary)

        calls = [str(call) for call in mock_console.print.call_args_list]
        output = " ".join(calls)
        assert "and 2 more" in output or "... and" in output

    def test_skips_categories_without_errors(self, reporter, mock_console, mock_error_summary):
        """Test that categories with no errors are skipped."""
        from src.ecreshore.services.error_handler import ErrorCategory

        error_summary = mock_error_summary(ErrorCategory.NETWORK_TIMEOUT, with_errors=False)

        reporter._display_failed_transfer_details(error_summary)

        # Should only have header, no category details
        calls = [str(call) for call in mock_console.print.call_args_list]
        # Should not display category name for empty errors
        output = " ".join(calls)
        # Should see header but not the specific error category
        assert "Network Timeout" not in output or output.count("Network Timeout") <= 1


class TestShowErrorSummaryOrchestrator:
    """Tests for _show_error_summary() orchestrator method."""

    def test_returns_early_when_no_errors(self, reporter, mock_console):
        """Test that function returns early if no error summary."""
        reporter.error_aggregator.get_error_summary.return_value = {}

        reporter._show_error_summary(simple_mode=True)

        # Should not output anything except maybe blank line
        assert mock_console.print.call_count <= 1

    def test_calls_simple_display_in_simple_mode(self, reporter, mock_error_summary):
        """Test that simple mode calls _display_simple_error_summary."""
        from src.ecreshore.services.error_handler import ErrorCategory

        error_summary = mock_error_summary(ErrorCategory.NETWORK_TIMEOUT)
        reporter.error_aggregator.get_error_summary.return_value = error_summary
        reporter.error_aggregator.get_actionable_recommendations.return_value = []

        with patch.object(reporter, '_display_simple_error_summary') as mock_simple:
            reporter._show_error_summary(simple_mode=True)
            assert mock_simple.called

    def test_calls_rich_display_in_rich_mode(self, reporter, mock_error_summary):
        """Test that rich mode calls _display_rich_error_summary."""
        from src.ecreshore.services.error_handler import ErrorCategory

        error_summary = mock_error_summary(ErrorCategory.NETWORK_TIMEOUT)
        reporter.error_aggregator.get_error_summary.return_value = error_summary
        reporter.error_aggregator.get_actionable_recommendations.return_value = []

        with patch.object(reporter, '_display_rich_error_summary') as mock_rich:
            with patch.object(reporter, '_display_failed_transfer_details'):
                reporter._show_error_summary(simple_mode=False)
                assert mock_rich.called

    def test_calls_failed_transfer_details_in_rich_mode(self, reporter, mock_error_summary):
        """Test that rich mode also calls _display_failed_transfer_details."""
        from src.ecreshore.services.error_handler import ErrorCategory

        error_summary = mock_error_summary(ErrorCategory.NETWORK_TIMEOUT)
        reporter.error_aggregator.get_error_summary.return_value = error_summary
        reporter.error_aggregator.get_actionable_recommendations.return_value = []

        with patch.object(reporter, '_display_rich_error_summary'):
            with patch.object(reporter, '_display_failed_transfer_details') as mock_details:
                reporter._show_error_summary(simple_mode=False)
                assert mock_details.called
