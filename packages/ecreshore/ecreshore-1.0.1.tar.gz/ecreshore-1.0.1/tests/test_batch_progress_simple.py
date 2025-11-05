"""Test simplified batch progress reporting functionality."""

import pytest
from unittest.mock import Mock, patch
from io import StringIO

from src.ecreshore.services.batch_progress import BatchProgressReporter, TransferStatus
from src.ecreshore.services.batch_config import BatchRequest, BatchTransferRequest, BatchSettings


def create_test_batch_request():
    """Create a test batch request with sample transfers."""
    transfers = [
        BatchTransferRequest(
            source="source1.com/repo1",
            source_tag="v1.0",
            target="target1.com/repo1", 
            target_tag="v1.0"
        ),
        BatchTransferRequest(
            source="source2.com/repo2",
            source_tag="v2.0", 
            target="target2.com/repo2",
            target_tag="v2.0"
        )
    ]
    settings = BatchSettings(concurrent_transfers=1, retry_attempts=2)
    return BatchRequest(transfers=transfers, settings=settings)


@pytest.mark.ux
def test_simple_mode_initialization():
    """Test BatchProgressReporter initializes correctly in simple mode."""
    reporter = BatchProgressReporter(simple_mode=True)
    assert reporter.simple_mode is True
    assert reporter.transfers == {}
    assert reporter.batch_start_time is None


@pytest.mark.ux
def test_simple_mode_start_batch():
    """Test batch start output in simple mode."""
    mock_console = Mock()
    reporter = BatchProgressReporter(console=mock_console, simple_mode=True)
    batch_request = create_test_batch_request()
    
    reporter.start_batch(batch_request)
    
    # Should print simple start message
    mock_console.print.assert_any_call("Starting batch transfer of 2 images")
    # Should not print complex status lines
    assert len(reporter.transfers) == 2
    assert "transfer_0" in reporter.transfers
    assert "transfer_1" in reporter.transfers


@pytest.mark.ux
def test_simple_mode_start_transfer():
    """Test transfer start output in simple mode."""
    mock_console = Mock()
    reporter = BatchProgressReporter(console=mock_console, simple_mode=True)
    batch_request = create_test_batch_request()
    
    reporter.start_batch(batch_request)
    mock_console.reset_mock()
    
    reporter.start_transfer("transfer_0")
    
    # Should print simple progress indicator
    mock_console.print.assert_called_with("[1/2] Starting source1.com/repo1:v1.0 → target1.com/repo1:v1.0")


@pytest.mark.ux
def test_simple_mode_complete_transfer_success():
    """Test successful transfer completion in simple mode."""
    mock_console = Mock()
    reporter = BatchProgressReporter(console=mock_console, simple_mode=True)
    batch_request = create_test_batch_request()
    
    reporter.start_batch(batch_request)
    reporter.start_transfer("transfer_0")
    mock_console.reset_mock()
    
    reporter.complete_transfer("transfer_0", success=True)
    
    # Should print success message with checkmark
    calls = mock_console.print.call_args_list
    assert len(calls) == 1
    call_text = calls[0][0][0]
    assert "[1/2] ✓ Completed" in call_text
    assert "source1.com/repo1:v1.0 → target1.com/repo1:v1.0" in call_text


@pytest.mark.ux
def test_simple_mode_complete_transfer_failure():
    """Test failed transfer completion in simple mode."""
    mock_console = Mock()
    reporter = BatchProgressReporter(console=mock_console, simple_mode=True)
    batch_request = create_test_batch_request()
    
    reporter.start_batch(batch_request)
    reporter.start_transfer("transfer_0")
    mock_console.reset_mock()
    
    reporter.complete_transfer("transfer_0", success=False, error_message="Connection failed")
    
    # Should print failure message and error
    calls = mock_console.print.call_args_list
    assert len(calls) == 2
    
    failure_call = calls[0][0][0]
    assert "[1/2] ✗ Failed" in failure_call
    assert "source1.com/repo1:v1.0 → target1.com/repo1:v1.0" in failure_call
    
    error_call = calls[1][0][0]
    assert "    Error: Connection failed" == error_call


@pytest.mark.ux
def test_simple_mode_retry_transfer():
    """Test retry output in simple mode."""
    mock_console = Mock()
    reporter = BatchProgressReporter(console=mock_console, simple_mode=True)
    batch_request = create_test_batch_request()
    
    reporter.start_batch(batch_request)
    reporter.start_transfer("transfer_0")
    mock_console.reset_mock()
    
    reporter.retry_transfer("transfer_0", retry_count=1, error_message="Timeout")
    
    # Should print retry message
    mock_console.print.assert_called_with("[1/2] Retrying source1.com/repo1:v1.0 (attempt 1)")


@pytest.mark.ux
def test_simple_mode_finish_batch_success():
    """Test batch completion output in simple mode - all successful."""
    mock_console = Mock()
    reporter = BatchProgressReporter(console=mock_console, simple_mode=True)
    batch_request = create_test_batch_request()
    
    reporter.start_batch(batch_request)
    reporter.start_transfer("transfer_0")
    reporter.complete_transfer("transfer_0", success=True)
    reporter.start_transfer("transfer_1")
    reporter.complete_transfer("transfer_1", success=True)
    mock_console.reset_mock()
    
    reporter.finish_batch()
    
    # Should print success summary
    calls = mock_console.print.call_args_list
    assert len(calls) == 2  # Empty line + summary
    
    summary_call = calls[1][0][0]
    assert "✓ Batch completed successfully: 2/2 transfers" in summary_call


@pytest.mark.ux
def test_simple_mode_finish_batch_with_failures():
    """Test batch completion output in simple mode - with failures."""
    mock_console = Mock()
    reporter = BatchProgressReporter(console=mock_console, simple_mode=True)
    batch_request = create_test_batch_request()
    
    reporter.start_batch(batch_request)
    reporter.start_transfer("transfer_0")
    reporter.complete_transfer("transfer_0", success=True)
    reporter.start_transfer("transfer_1")
    reporter.complete_transfer("transfer_1", success=False, error_message="Failed")
    mock_console.reset_mock()
    
    reporter.finish_batch()
    
    # Should print warning summary
    calls = mock_console.print.call_args_list
    summary_call = calls[1][0][0]
    assert "⚠ Batch completed with errors: 1/2 successful, 1 failed" in summary_call


@pytest.mark.ux
def test_complex_mode_still_works():
    """Test that complex mode (original behavior) still functions."""
    mock_console = Mock()
    reporter = BatchProgressReporter(console=mock_console, simple_mode=False)
    batch_request = create_test_batch_request()
    
    reporter.start_batch(batch_request)
    
    # Complex mode should show status lines and rich formatting
    calls = mock_console.print.call_args_list
    # Should have status lines for each transfer plus headers
    assert len(calls) >= 2  # At least the transfer status lines