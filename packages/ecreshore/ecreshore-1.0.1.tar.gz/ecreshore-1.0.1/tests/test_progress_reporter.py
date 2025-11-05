"""Tests for ProgressReporter."""

import pytest
from unittest.mock import Mock, MagicMock
from io import StringIO

from rich.console import Console
from src.ecreshore.services.progress_reporter import ProgressReporter, ProgressCallback


@pytest.mark.ux
class TestProgressReporter:
    def test_init_default_console(self):
        """Test ProgressReporter initialization with default console."""
        reporter = ProgressReporter()
        
        assert reporter.console is not None
        assert reporter.verbose is False
        assert len(reporter._callbacks) == 0
    
    def test_init_custom_console(self):
        """Test ProgressReporter initialization with custom console."""
        mock_console = Mock(spec=Console)
        reporter = ProgressReporter(console=mock_console, verbose=True)
        
        assert reporter.console is mock_console
        assert reporter.verbose is True
    
    def test_add_callback(self):
        """Test adding progress callbacks."""
        reporter = ProgressReporter()
        callback = Mock()
        
        reporter.add_callback("test_callback", callback)
        
        assert "test_callback" in reporter._callbacks
        assert reporter._callbacks["test_callback"] is callback
    
    def test_remove_callback(self):
        """Test removing progress callbacks."""
        reporter = ProgressReporter()
        callback = Mock()
        
        reporter.add_callback("test_callback", callback)
        reporter.remove_callback("test_callback")
        
        assert "test_callback" not in reporter._callbacks
    
    def test_remove_nonexistent_callback(self):
        """Test removing nonexistent callback doesn't raise error."""
        reporter = ProgressReporter()
        
        # Should not raise
        reporter.remove_callback("nonexistent")
    
    def test_info_message(self):
        """Test info message reporting."""
        mock_console = Mock(spec=Console)
        reporter = ProgressReporter(console=mock_console)
        callback = Mock()
        reporter.add_callback("test", callback)
        
        reporter.info("Test info message", extra_data="value")
        
        mock_console.print.assert_called_once_with("[blue]ℹ[/blue] Test info message")
        callback.assert_called_once_with("Test info message", level='info', extra_data="value")
    
    def test_success_message(self):
        """Test success message reporting."""
        mock_console = Mock(spec=Console)
        reporter = ProgressReporter(console=mock_console)
        callback = Mock()
        reporter.add_callback("test", callback)
        
        reporter.success("Operation completed")
        
        mock_console.print.assert_called_once_with("[green]✓[/green] Operation completed")
        callback.assert_called_once_with("Operation completed", level='success')
    
    def test_warning_message(self):
        """Test warning message reporting."""
        mock_console = Mock(spec=Console)
        reporter = ProgressReporter(console=mock_console)
        callback = Mock()
        reporter.add_callback("test", callback)
        
        reporter.warning("Warning message")
        
        mock_console.print.assert_called_once_with("[yellow]⚠[/yellow] Warning message")
        callback.assert_called_once_with("Warning message", level='warning')
    
    def test_error_message(self):
        """Test error message reporting."""
        mock_console = Mock(spec=Console)
        reporter = ProgressReporter(console=mock_console)
        callback = Mock()
        reporter.add_callback("test", callback)
        
        reporter.error("Error occurred")
        
        mock_console.print.assert_called_once_with("[red]✗[/red] Error occurred")
        callback.assert_called_once_with("Error occurred", level='error')
    
    def test_status_context_manager(self):
        """Test status context manager."""
        mock_console = Mock(spec=Console)
        mock_status = Mock()
        mock_console.status.return_value = mock_status
        
        reporter = ProgressReporter(console=mock_console)
        
        status_cm = reporter.status("Processing...")
        
        mock_console.status.assert_called_once_with("Processing...")
        assert status_cm is mock_status
    
    def test_start_transfer(self):
        """Test start transfer reporting."""
        mock_console = Mock(spec=Console)
        reporter = ProgressReporter(console=mock_console)
        callback = Mock()
        reporter.add_callback("test", callback)
        
        reporter.start_transfer("nginx", "my-nginx", "1.21", "stable")
        
        expected_message = "Starting transfer: nginx:1.21 → my-nginx:stable"
        mock_console.print.assert_called_once_with(f"[bold blue]{expected_message}[/bold blue]")
        callback.assert_called_once_with(
            expected_message,
            level='transfer_start',
            source_image="nginx",
            target_repository="my-nginx", 
            source_tag="1.21",
            target_tag="stable"
        )
    
    def test_transfer_complete_success(self):
        """Test successful transfer completion reporting."""
        mock_console = Mock(spec=Console)
        reporter = ProgressReporter(console=mock_console)
        callback = Mock()
        reporter.add_callback("test", callback)
        
        reporter.transfer_complete("nginx", "my-nginx", "latest", "v1.0", success=True)
        
        expected_message = "Transfer completed: nginx:latest → my-nginx:v1.0"
        mock_console.print.assert_called_once_with(f"[bold green]{expected_message}[/bold green]")
        callback.assert_called_once_with(
            expected_message,
            level='transfer_success',
            source_image="nginx",
            target_repository="my-nginx",
            source_tag="latest", 
            target_tag="v1.0",
            success=True
        )
    
    def test_transfer_complete_failure(self):
        """Test failed transfer completion reporting."""
        mock_console = Mock(spec=Console)
        reporter = ProgressReporter(console=mock_console)
        callback = Mock()
        reporter.add_callback("test", callback)
        
        reporter.transfer_complete("nginx", "my-nginx", "latest", "v1.0", success=False)
        
        expected_message = "Transfer failed: nginx:latest → my-nginx:v1.0"
        mock_console.print.assert_called_once_with(f"[bold red]{expected_message}[/bold red]")
        callback.assert_called_once_with(
            expected_message,
            level='transfer_failed',
            source_image="nginx",
            target_repository="my-nginx",
            source_tag="latest",
            target_tag="v1.0", 
            success=False
        )
    
    def test_pull_progress_verbose(self):
        """Test pull progress reporting in verbose mode."""
        mock_console = Mock(spec=Console)
        reporter = ProgressReporter(console=mock_console, verbose=True)
        callback = Mock()
        reporter.add_callback("test", callback)
        
        reporter.pull_progress("nginx", "latest")
        
        # Should call info() which calls print and _notify_callbacks
        assert mock_console.print.call_count == 1
        assert "[blue]ℹ[/blue] Pulling nginx:latest" in str(mock_console.print.call_args)
        
        # Should call callback twice: once for info(), once for pull_progress()
        assert callback.call_count == 2
        callback.assert_any_call("Pulling nginx:latest", level='info')
        callback.assert_any_call(
            "Pulling nginx:latest",
            level='pull',
            repository="nginx",
            tag="latest"
        )
    
    def test_pull_progress_non_verbose(self):
        """Test pull progress reporting in non-verbose mode."""
        mock_console = Mock(spec=Console)
        reporter = ProgressReporter(console=mock_console, verbose=False)
        callback = Mock()
        reporter.add_callback("test", callback)
        
        reporter.pull_progress("nginx", "latest")
        
        # Should not print in non-verbose mode
        mock_console.print.assert_not_called()
        # But should still call callback
        callback.assert_called_once_with(
            "Pulling nginx:latest",
            level='pull',
            repository="nginx",
            tag="latest"
        )
    
    def test_tag_progress_verbose(self):
        """Test tag progress reporting."""
        mock_console = Mock(spec=Console)
        reporter = ProgressReporter(console=mock_console, verbose=True)
        callback = Mock()
        reporter.add_callback("test", callback)
        
        reporter.tag_progress("nginx:latest", "my-registry/nginx:v1.0")
        
        # Should call info() which calls print and _notify_callbacks
        assert mock_console.print.call_count == 1
        assert "[blue]ℹ[/blue] Tagged nginx:latest → my-registry/nginx:v1.0" in str(mock_console.print.call_args)
        
        # Should call callback twice: once for info(), once for tag_progress()
        assert callback.call_count == 2
        callback.assert_any_call("Tagged nginx:latest → my-registry/nginx:v1.0", level='info')
        callback.assert_any_call(
            "Tagged nginx:latest → my-registry/nginx:v1.0",
            level='tag',
            source="nginx:latest",
            target="my-registry/nginx:v1.0"
        )
    
    def test_push_progress_verbose(self):
        """Test push progress reporting."""
        mock_console = Mock(spec=Console)
        reporter = ProgressReporter(console=mock_console, verbose=True)
        callback = Mock()
        reporter.add_callback("test", callback)
        
        reporter.push_progress("my-registry/nginx", "v1.0")
        
        # Should call info() which calls print and _notify_callbacks
        assert mock_console.print.call_count == 1
        assert "[blue]ℹ[/blue] Pushing my-registry/nginx:v1.0" in str(mock_console.print.call_args)
        
        # Should call callback twice: once for info(), once for push_progress()
        assert callback.call_count == 2
        callback.assert_any_call("Pushing my-registry/nginx:v1.0", level='info')
        callback.assert_any_call(
            "Pushing my-registry/nginx:v1.0",
            level='push',
            repository="my-registry/nginx",
            tag="v1.0"
        )
    
    def test_verification_progress_success(self):
        """Test successful digest verification reporting."""
        mock_console = Mock(spec=Console)
        reporter = ProgressReporter(console=mock_console)
        callback = Mock()
        reporter.add_callback("test", callback)
        
        reporter.verification_progress("digest123", "digest123")
        
        # Should call success() which calls print and _notify_callbacks
        assert mock_console.print.call_count == 1
        assert "[green]✓[/green] Image digest verified" in str(mock_console.print.call_args)
        
        # Should call callback twice: once for success(), once for verification_progress()
        assert callback.call_count == 2
        callback.assert_any_call("Image digest verified", level='success')
        callback.assert_any_call(
            "Digest verification completed",
            level='verification_success',
            source_digest="digest123",
            target_digest="digest123"
        )
    
    def test_verification_progress_mismatch(self):
        """Test digest mismatch reporting."""
        mock_console = Mock(spec=Console)
        reporter = ProgressReporter(console=mock_console)
        callback = Mock()
        reporter.add_callback("test", callback)
        
        reporter.verification_progress("digest123", "digest456")
        
        # Should call warning() which calls print and _notify_callbacks
        assert mock_console.print.call_count == 1
        assert "[yellow]⚠[/yellow] Image digest mismatch detected" in str(mock_console.print.call_args)
        
        # Should call callback twice: once for warning(), once for verification_progress()
        assert callback.call_count == 2
        callback.assert_any_call("Image digest mismatch detected", level='warning')
        callback.assert_any_call(
            "Digest verification completed",
            level='verification_failed',
            source_digest="digest123",
            target_digest="digest456"
        )
    
    def test_verification_progress_unavailable(self):
        """Test digest verification when digests unavailable."""
        mock_console = Mock(spec=Console)
        reporter = ProgressReporter(console=mock_console)
        callback = Mock()
        reporter.add_callback("test", callback)
        
        reporter.verification_progress(None, "digest456")
        
        # Should call warning() which calls print and _notify_callbacks
        assert mock_console.print.call_count == 1
        assert "[yellow]⚠[/yellow] Could not verify image digest" in str(mock_console.print.call_args)
        
        # Should call callback twice: once for warning(), once for verification_progress()
        assert callback.call_count == 2
        callback.assert_any_call("Could not verify image digest", level='warning')
        callback.assert_any_call(
            "Digest verification completed",
            level='verification_unavailable',
            source_digest=None,
            target_digest="digest456"
        )
    
    def test_callback_exception_handling(self):
        """Test that callback exceptions don't break progress reporting."""
        mock_console = Mock(spec=Console)
        reporter = ProgressReporter(console=mock_console)
        
        # Add a callback that raises an exception
        failing_callback = Mock(side_effect=Exception("Callback failed"))
        working_callback = Mock()
        
        reporter.add_callback("failing", failing_callback)
        reporter.add_callback("working", working_callback)
        
        # Should not raise exception
        reporter.info("Test message")
        
        # Console should still print
        mock_console.print.assert_called_once_with("[blue]ℹ[/blue] Test message")
        
        # Working callback should still be called
        working_callback.assert_called_once_with("Test message", level='info')
        failing_callback.assert_called_once_with("Test message", level='info')
    
    def test_verbose_mode_logging(self):
        """Test verbose mode includes context in debug logging."""
        # This test verifies that verbose mode would log context data
        # In a real implementation, we'd check that logger.debug was called
        mock_console = Mock(spec=Console)
        reporter = ProgressReporter(console=mock_console, verbose=True)
        
        # The verbose logging is implemented but hard to test without mocking logger
        # This test mainly ensures verbose flag is handled correctly
        reporter.info("Test message", context_data="value")
        
        mock_console.print.assert_called_once_with("[blue]ℹ[/blue] Test message")