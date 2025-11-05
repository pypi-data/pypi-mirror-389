"""Enhanced progress reporting for batch operations with rich UI components."""

import logging
import time
from dataclasses import dataclass
from enum import Enum
from typing import Dict, Optional, Any
from contextlib import contextmanager

import structlog
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import (
    Progress,
    BarColumn,
    TextColumn,
    TimeElapsedColumn,
    SpinnerColumn,
)
from rich.live import Live
from rich import box as rich_box

from .progress_reporter import ProgressReporter
from .batch_config import BatchRequest, BatchTransferRequest
from .output_modes import OUTPUT_MODE_CONSOLE, OUTPUT_MODE_LOG
from .batch_error_aggregator import BatchErrorAggregator, ErrorSummary
from .error_handler import ErrorCategory

logger = logging.getLogger(__name__)
struct_logger = structlog.get_logger()


class TransferStatus(Enum):
    """Status of individual transfer operations."""

    PENDING = "pending"
    RUNNING = "running"
    RETRYING = "retrying"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


STATUS_SYMBOLS = {
    TransferStatus.PENDING: "⏳",
    TransferStatus.RUNNING: "🔄",
    TransferStatus.RETRYING: "🔁",
    TransferStatus.COMPLETED: "✅",
    TransferStatus.FAILED: "❌",
    TransferStatus.SKIPPED: "‥",
}


@dataclass
class TransferProgress:
    """Progress tracking for individual transfer."""

    request: BatchTransferRequest
    status: TransferStatus = TransferStatus.PENDING
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    retry_count: int = 0
    error_message: Optional[str] = None
    current_operation: str = ""

    @property
    def duration(self) -> Optional[float]:
        """Get transfer duration in seconds."""
        if self.start_time is None:
            return None
        end = self.end_time or time.time()
        return end - self.start_time

    @property
    def is_complete(self) -> bool:
        """Check if transfer is complete (success, failure, or skipped)."""
        return self.status in {
            TransferStatus.COMPLETED,
            TransferStatus.FAILED,
            TransferStatus.SKIPPED,
        }


@dataclass
class BatchSummary:
    """Summary statistics for completed batch operation."""

    completed: int
    failed: int
    skipped: int
    total: int
    duration: float
    total_retries: int
    batch_end_time: float


class BatchProgressReporter:
    """Enhanced progress reporter for batch transfer operations."""

    def __init__(
        self,
        console: Optional[Console] = None,
        verbose: bool = False,
        simple_mode: bool = True,
        output_mode: str = OUTPUT_MODE_CONSOLE,
    ):
        """Initialize batch progress reporter.

        Args:
            console: Rich console instance
            verbose: Enable verbose logging
            simple_mode: Use simplified output without ANSI manipulation
            output_mode: Output mode ('console' or 'log')
        """
        self.console = console or Console()
        self.verbose = verbose
        self.simple_mode = simple_mode
        self.output_mode = output_mode
        self.base_reporter = ProgressReporter(console, verbose)

        # Progress tracking
        self.transfers: Dict[str, TransferProgress] = {}
        self.batch_start_time: Optional[float] = None
        self.batch_end_time: Optional[float] = None

        # Status line tracking (only used in complex mode)
        self.transfer_lines: Dict[str, int] = {}
        self.current_line: int = 0

        # Rich progress components for complex mode
        self.progress: Optional[Progress] = None
        self.live: Optional[Live] = None
        self.transfer_tasks: Dict[str, int] = {}
        self.overall_task: Optional[int] = None

        # Error aggregation for clean reporting
        self.error_aggregator = BatchErrorAggregator()

        # Error buffering during Live display to prevent interleaving
        self._buffered_errors: list[tuple[str, dict]] = []

    def _log_structured(self, event: str, **kwargs) -> None:
        """Log structured event for log output mode."""
        if self.output_mode == OUTPUT_MODE_LOG:
            struct_logger.info(event, **kwargs)

    def _console_output(self, message, **rich_kwargs) -> None:
        """Output to console for console output mode."""
        if self.output_mode == OUTPUT_MODE_CONSOLE:
            self.console.print(message, **rich_kwargs)

    def success(self, message: str, **kwargs) -> None:
        """Report success message - delegates to base reporter."""
        self.base_reporter.success(message, **kwargs)

    def info(self, message: str, **kwargs) -> None:
        """Report info message - delegates to base reporter."""
        self.base_reporter.info(message, **kwargs)

    def warning(self, message: str, **kwargs) -> None:
        """Report warning message - delegates to base reporter."""
        self.base_reporter.warning(message, **kwargs)

    def error(self, message: str, **kwargs) -> None:
        """Report error message - buffered during live display to prevent interleaving."""
        if self.live and self.live.is_started:
            # Buffer errors during live display
            self._buffered_errors.append((message, kwargs))
        else:
            self.base_reporter.error(message, **kwargs)

    def start_batch(self, batch_request: BatchRequest) -> None:
        """Start batch operation tracking.

        Args:
            batch_request: Batch request to track
        """
        self.batch_start_time = time.time()
        self.batch_end_time = None

        # Initialize transfer progress tracking
        for i, transfer in enumerate(batch_request.transfers):
            transfer_id = f"transfer_{i}"
            self.transfers[transfer_id] = TransferProgress(request=transfer)

        # Log batch start event
        self._log_structured(
            "batch_started",
            transfer_count=len(batch_request.transfers),
            concurrent_transfers=batch_request.settings.concurrent_transfers,
            retry_attempts=batch_request.settings.retry_attempts,
            verify_digests=batch_request.settings.verify_digests,
            timestamp=self.batch_start_time,
        )

        if self.simple_mode:
            # Simple mode: just show basic info
            self._console_output(
                f"Starting batch transfer of {len(batch_request.transfers)} images"
            )
            if batch_request.settings.concurrent_transfers > 1:
                self._console_output(
                    f"Concurrent transfers: {batch_request.settings.concurrent_transfers}"
                )
        else:
            # Complex mode: setup rich progress bars
            self._console_output(
                f"[bold blue]Starting batch transfer of {len(batch_request.transfers)} images[/bold blue]"
            )

            if batch_request.settings.concurrent_transfers > 1:
                self._console_output(
                    f"[dim]Concurrent transfers: {batch_request.settings.concurrent_transfers}[/dim]"
                )
            if batch_request.settings.retry_attempts > 0:
                self._console_output(
                    f"[dim]Max retry attempts: {batch_request.settings.retry_attempts}[/dim]"
                )

            self._console_output("")

            # Initialize rich progress display
            self.progress = Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(bar_width=20),
                "[progress.percentage]{task.percentage:>3.0f}%",
                TextColumn("[dim]{task.completed}/{task.total}"),
                TimeElapsedColumn(),
                console=self.console,
                transient=True,  # Progress bars disappear when Live stops
            )

            # Add overall progress task
            self.overall_task = self.progress.add_task(
                "[bold cyan]Overall Progress",
                total=len(batch_request.transfers),
                completed=0,
            )

            # Add individual transfer tasks
            for i, (transfer_id, progress_obj) in enumerate(self.transfers.items()):
                req = progress_obj.request
                description = f"Transfer {i + 1}: {req.source}:{req.source_tag} → {req.target}:{req.target_tag}"

                task_id = self.progress.add_task(
                    description,
                    total=100,
                    completed=0,
                    visible=False,  # Initially hidden, show when started
                )
                self.transfer_tasks[transfer_id] = task_id

            # Start the live display
            self.live = Live(self.progress, console=self.console, refresh_per_second=10)
            self.live.start()

    def start_transfer(self, transfer_id: str) -> None:
        """Mark transfer as started.

        Args:
            transfer_id: Transfer identifier
        """
        if transfer_id not in self.transfers:
            return

        progress = self.transfers[transfer_id]
        progress.status = TransferStatus.RUNNING
        progress.start_time = time.time()
        progress.current_operation = "Starting"

        req = progress.request
        transfer_num = int(transfer_id.split("_")[1]) + 1
        total = len(self.transfers)

        # Log structured event
        self._log_structured(
            "transfer_started",
            transfer_id=transfer_id,
            transfer_num=transfer_num,
            total_transfers=total,
            source=req.source,
            source_tag=req.source_tag,
            target=req.target,
            target_tag=req.target_tag,
            timestamp=progress.start_time,
        )

        if self.simple_mode:
            # Simple mode: just show which transfer started
            self._console_output(
                f"[{transfer_num}/{total}] Starting {req.source}:{req.source_tag} → {req.target}:{req.target_tag}"
            )
        else:
            # Complex mode: show progress bar for this transfer
            if self.progress and transfer_id in self.transfer_tasks:
                task_id = self.transfer_tasks[transfer_id]
                self.progress.update(task_id, visible=True, completed=0)
                self.progress.update(
                    task_id,
                    description=f"[yellow]▶ Transfer {transfer_num}: {req.source}:{req.source_tag} → {req.target}:{req.target_tag}",
                )
            self._update_status_line(transfer_id)

        if self.verbose:
            req = progress.request
            self.base_reporter.start_transfer(
                req.source, req.target, req.source_tag, req.target_tag
            )

    def update_transfer_operation(
        self, transfer_id: str, operation: str, progress_pct: int = 0
    ) -> None:
        """Update current operation for a transfer.

        Args:
            transfer_id: Transfer identifier
            operation: Current operation description
            progress_pct: Progress percentage (0-100)
        """
        if transfer_id not in self.transfers:
            return

        self.transfers[transfer_id].current_operation = operation

        # Update rich progress bar in complex mode
        if (
            not self.simple_mode
            and self.progress
            and transfer_id in self.transfer_tasks
        ):
            task_id = self.transfer_tasks[transfer_id]
            transfer_num = int(transfer_id.split("_")[1]) + 1
            req = self.transfers[transfer_id].request

            # Update progress bar with current operation
            self.progress.update(
                task_id,
                completed=progress_pct,
                description=f"[yellow]▶ Transfer {transfer_num}: {operation} - {req.source}:{req.source_tag}",
            )

        self._update_status_line(transfer_id)

    def retry_transfer(
        self, transfer_id: str, retry_count: int, error_message: str
    ) -> None:
        """Mark transfer as retrying.

        Args:
            transfer_id: Transfer identifier
            retry_count: Current retry attempt number
            error_message: Error that triggered retry
        """
        if transfer_id not in self.transfers:
            return

        progress = self.transfers[transfer_id]
        progress.status = TransferStatus.RETRYING
        progress.retry_count = retry_count
        progress.current_operation = f"Retrying (attempt {retry_count})"

        if self.simple_mode:
            # Simple mode: show retry attempt
            req = progress.request
            transfer_num = int(transfer_id.split("_")[1]) + 1
            total = len(self.transfers)
            self._console_output(
                f"[{transfer_num}/{total}] Retrying {req.source}:{req.source_tag} (attempt {retry_count})"
            )
        else:
            self._update_status_line(transfer_id)

        if self.verbose:
            self.base_reporter.warning(
                f"Retrying transfer (attempt {retry_count}): {error_message}"
            )

    def _update_transfer_status(
        self,
        progress: TransferProgress,
        success: bool,
        error_message: Optional[str],
    ) -> None:
        """Update transfer status fields.

        Args:
            progress: Transfer progress object to update
            success: Whether transfer succeeded
            error_message: Error message if failed
        """
        progress.status = TransferStatus.COMPLETED if success else TransferStatus.FAILED
        progress.end_time = time.time()
        progress.error_message = error_message
        progress.current_operation = "Complete" if success else "Failed"

    def _log_transfer_completion(
        self,
        transfer_id: str,
        progress: TransferProgress,
        success: bool,
        error_message: Optional[str],
    ) -> None:
        """Log structured completion event.

        Args:
            transfer_id: Transfer identifier
            progress: Transfer progress object
            success: Whether transfer succeeded
            error_message: Error message if failed
        """
        req = progress.request
        transfer_num = int(transfer_id.split("_")[1]) + 1

        self._log_structured(
            "transfer_completed",
            transfer_id=transfer_id,
            transfer_num=transfer_num,
            total_transfers=len(self.transfers),
            source=req.source,
            source_tag=req.source_tag,
            target=req.target,
            target_tag=req.target_tag,
            success=success,
            duration=progress.duration or 0.0,
            error_message=error_message,
            timestamp=progress.end_time,
        )

    def _record_transfer_error(
        self, transfer_id: str, progress: TransferProgress, error_message: str
    ) -> None:
        """Record error in aggregator.

        Args:
            transfer_id: Transfer identifier
            progress: Transfer progress object
            error_message: Error message to record
        """
        try:
            req = progress.request
            error_exception = Exception(error_message)
            self.error_aggregator.add_transfer_error(
                transfer_id=transfer_id,
                source_image=req.source,
                target_repository=req.target,
                source_tag=req.source_tag,
                target_tag=req.target_tag,
                error=error_exception,
                retry_count=progress.retry_count,
                timestamp=progress.end_time,
            )
        except Exception as e:
            logger.warning(f"Failed to add error to aggregator: {e}")

    def _display_simple_completion(
        self,
        transfer_id: str,
        progress: TransferProgress,
        success: bool,
        error_message: Optional[str],
    ) -> None:
        """Display completion message in simple mode.

        Args:
            transfer_id: Transfer identifier
            progress: Transfer progress object
            success: Whether transfer succeeded
            error_message: Error message if failed
        """
        req = progress.request
        transfer_num = int(transfer_id.split("_")[1]) + 1
        total = len(self.transfers)
        duration_str = f"{progress.duration:.1f}s" if progress.duration else "0.0s"

        if success:
            self._console_output(
                f"[{transfer_num}/{total}] ✓ Completed "
                f"{req.source}:{req.source_tag} → {req.target}:{req.target_tag} "
                f"({duration_str})"
            )
        else:
            self._console_output(
                f"[{transfer_num}/{total}] ✗ Failed "
                f"{req.source}:{req.source_tag} → {req.target}:{req.target_tag} "
                f"({duration_str})"
            )
            if error_message:
                self._console_output(f"    Error: {error_message}")

            if self.output_mode == OUTPUT_MODE_LOG:
                self._log_structured(
                    "transfer_error",
                    transfer_id=transfer_id,
                    error_message=error_message or "Unknown error",
                    timestamp=time.time(),
                )

    def _display_complex_completion(
        self,
        transfer_id: str,
        progress: TransferProgress,
        success: bool,
    ) -> None:
        """Display completion in complex mode with progress bars.

        Args:
            transfer_id: Transfer identifier
            progress: Transfer progress object
            success: Whether transfer succeeded
        """
        if not self.progress or transfer_id not in self.transfer_tasks:
            return

        task_id = self.transfer_tasks[transfer_id]
        req = progress.request
        transfer_num = int(transfer_id.split("_")[1]) + 1
        duration_str = f"{progress.duration:.1f}s" if progress.duration else "0.0s"

        if success:
            self.progress.update(
                task_id,
                completed=100,
                description=f"[green]✓ Transfer {transfer_num}: {req.source}:{req.source_tag} → {req.target}:{req.target_tag} ({duration_str})",
            )
        else:
            self.progress.update(
                task_id,
                completed=100,
                description=f"[red]✗ Transfer {transfer_num}: {req.source}:{req.source_tag} → {req.target}:{req.target_tag} (Failed)",
            )

        # Update overall progress
        if self.overall_task is not None:
            completed_count = sum(1 for p in self.transfers.values() if p.is_complete)
            self.progress.update(self.overall_task, completed=completed_count)

    def complete_transfer(
        self, transfer_id: str, success: bool, error_message: Optional[str] = None
    ) -> None:
        """Mark transfer as completed.

        Args:
            transfer_id: Transfer identifier
            success: Whether transfer succeeded
            error_message: Error message if failed
        """
        if transfer_id not in self.transfers:
            return

        progress = self.transfers[transfer_id]

        # 1. Update status
        self._update_transfer_status(progress, success, error_message)

        # 2. Log event
        self._log_transfer_completion(transfer_id, progress, success, error_message)

        # 3. Handle errors
        if not success and error_message:
            self._record_transfer_error(transfer_id, progress, error_message)

        # 4. Display completion
        if self.simple_mode:
            self._display_simple_completion(
                transfer_id, progress, success, error_message
            )
        else:
            self._display_complex_completion(transfer_id, progress, success)
            self._update_status_line(transfer_id)

        # 5. Verbose reporting
        if self.verbose:
            req = progress.request
            self.base_reporter.transfer_complete(
                req.source, req.target, req.source_tag, req.target_tag, success
            )
            if not success and error_message:
                self.base_reporter.error(error_message)

    def _calculate_batch_summary(self) -> BatchSummary:
        """Calculate batch summary statistics - PURE CALCULATION.

        Returns:
            BatchSummary with all statistics
        """
        completed = sum(
            1 for p in self.transfers.values() if p.status == TransferStatus.COMPLETED
        )
        failed = sum(
            1 for p in self.transfers.values() if p.status == TransferStatus.FAILED
        )
        skipped = sum(
            1 for p in self.transfers.values() if p.status == TransferStatus.SKIPPED
        )
        total = len(self.transfers)
        duration = self.batch_end_time - (
            self.batch_start_time or self.batch_end_time
        )
        total_retries = sum(p.retry_count for p in self.transfers.values())

        return BatchSummary(
            completed=completed,
            failed=failed,
            skipped=skipped,
            total=total,
            duration=duration,
            total_retries=total_retries,
            batch_end_time=self.batch_end_time,
        )

    def _build_transfer_history(self) -> list[str]:
        """Build transfer history for complex mode display.

        Returns:
            List of formatted status lines
        """
        transfer_history = []
        for i, (transfer_id, progress) in enumerate(sorted(self.transfers.items())):
            req = progress.request
            symbol = STATUS_SYMBOLS.get(progress.status, "")

            if progress.status == TransferStatus.COMPLETED:
                status_text = f"[green]{symbol} Transfer {i + 1}: {req.source}:{req.source_tag} → {req.target}:{req.target_tag} (Completed)[/green]"
            elif progress.status == TransferStatus.FAILED:
                status_text = f"[red]{symbol} Transfer {i + 1}: {req.source}:{req.source_tag} → {req.target}:{req.target_tag} (Failed)[/red]"
            elif progress.status == TransferStatus.SKIPPED:
                status_text = f"[dim]{symbol} Transfer {i + 1}: {req.source}:{req.source_tag} → {req.target}:{req.target_tag} (Skipped)[/dim]"
            else:
                status_text = f"{symbol} Transfer {i + 1}: {req.source}:{req.source_tag} → {req.target}:{req.target_tag} ({progress.status.value})"

            transfer_history.append(status_text)
        return transfer_history

    def _display_simple_summary(self, summary: BatchSummary) -> None:
        """Display batch summary in simple mode.

        Args:
            summary: BatchSummary containing all statistics
        """
        self._console_output("")

        if summary.failed == 0:
            if summary.skipped == 0:
                self._console_output(
                    f"✓ Batch completed successfully: {summary.completed}/{summary.total} transfers in {summary.duration:.1f}s"
                )
            else:
                self._console_output(
                    f"✓ Batch completed: {summary.completed}/{summary.total} transferred, {summary.skipped} skipped in {summary.duration:.1f}s"
                )
        else:
            if summary.skipped == 0:
                self._console_output(
                    f"⚠ Batch completed with errors: {summary.completed}/{summary.total} successful, {summary.failed} failed in {summary.duration:.1f}s"
                )
            else:
                self._console_output(
                    f"⚠ Batch completed: {summary.completed} successful, {summary.failed} failed, {summary.skipped} skipped in {summary.duration:.1f}s"
                )

        if summary.total_retries > 0:
            self._console_output(f"Total retries: {summary.total_retries}")

        if summary.failed > 0:
            self._show_error_summary(simple_mode=True)

    def _display_rich_summary(self, summary: BatchSummary) -> None:
        """Display batch summary in rich mode with progress bars and tables.

        Args:
            summary: BatchSummary containing all statistics
        """
        # Handle live display and transfer history
        if self.live:
            transfer_history = self._build_transfer_history()
            self.live.stop()

            # Flush buffered errors
            if self._buffered_errors:
                self._console_output("")
                for msg, kwargs in self._buffered_errors:
                    self.base_reporter.error(msg, **kwargs)
                self._buffered_errors.clear()

            # Print permanent transfer summary
            self._console_output("")
            self._console_output("[bold]Transfer Summary:[/bold]")
            for line in transfer_history:
                self._console_output(f"  {line}")

        # Display status message
        self._console_output("")
        if summary.failed == 0:
            if summary.skipped == 0:
                self._console_output(
                    f"[bold green]✓ All {summary.completed} transfers completed successfully![/bold green]"
                )
            else:
                self._console_output(
                    f"[bold green]✓ Batch completed![/bold green] {summary.completed} transferred, {summary.skipped} skipped"
                )
            self._console_output(f"[dim]Total time: {summary.duration:.1f} seconds[/dim]")
        else:
            self._console_output(
                "[bold yellow]⚠ Batch partially completed[/bold yellow]"
            )
            parts = [
                f"[green]Successful: {summary.completed}[/green]",
                f"[red]Failed: {summary.failed}[/red]",
            ]
            if summary.skipped > 0:
                parts.append(f"[yellow]Skipped: {summary.skipped}[/yellow]")
            self._console_output(", ".join(parts))
            self._console_output(f"[dim]Total time: {summary.duration:.1f} seconds[/dim]")

        # Summary table
        summary_table = Table(show_header=False, box=None, padding=(0, 1))
        summary_table.add_row("Completed:", f"[green]{summary.completed}[/green]")
        summary_table.add_row(
            "Failed:", f"[red]{summary.failed}[/red]" if summary.failed > 0 else "0"
        )
        if summary.skipped > 0:
            summary_table.add_row("Skipped:", f"[yellow]{summary.skipped}[/yellow]")
        summary_table.add_row("Total:", str(summary.total))
        summary_table.add_row("Duration:", f"{summary.duration:.1f}s")
        if summary.total_retries > 0:
            summary_table.add_row(
                "Total retries:", f"[yellow]{summary.total_retries}[/yellow]"
            )

        self._console_output(
            Panel(summary_table, title="Batch Summary", box=rich_box.ROUNDED)
        )

        if summary.failed > 0:
            self._show_error_summary(simple_mode=False)

    def finish_batch(self) -> None:
        """Complete batch operation tracking."""
        self.batch_end_time = time.time()

        # Calculate summary statistics
        summary = self._calculate_batch_summary()

        # Update error aggregator
        self.error_aggregator.set_transfer_counts(
            summary.total, summary.completed, summary.failed, summary.skipped
        )

        # Log structured summary
        self._log_structured(
            "batch_completed",
            total_transfers=summary.total,
            completed=summary.completed,
            failed=summary.failed,
            skipped=summary.skipped,
            total_retries=summary.total_retries,
            duration=summary.duration,
            timestamp=summary.batch_end_time,
        )

        # Display appropriate summary
        if self.simple_mode:
            self._display_simple_summary(summary)
        else:
            self._display_rich_summary(summary)

    def _format_category_name(self, category: ErrorCategory) -> str:
        """Format error category enum to human-readable string.

        Args:
            category: ErrorCategory enum value

        Returns:
            Formatted category name (e.g., "Network Error")
        """
        return category.value.replace("_", " ").title()

    def _display_simple_error_summary(
        self,
        error_summary: Dict[ErrorCategory, ErrorSummary],
        recommendations: list[str]
    ) -> None:
        """Display error summary in simple mode (plain text).

        Args:
            error_summary: Dictionary of error categories and their summaries
            recommendations: List of actionable recommendations
        """
        self._console_output("Error Summary:")

        for category, summary in error_summary.items():
            category_name = self._format_category_name(category)
            self._console_output(f"  • {category_name}: {summary.count} error(s)")

            # Show user guidance for this category
            if summary.user_guidance:
                self._console_output(f"    → {summary.user_guidance}")

        # Show actionable recommendations
        if recommendations:
            self._console_output("")
            self._console_output("Recommended Actions:")
            for i, recommendation in enumerate(recommendations, 1):
                self._console_output(f"  {i}. {recommendation}")

        # Show retry suggestion if applicable
        if self.error_aggregator.should_suggest_retry():
            self._console_output("")
            self._console_output(
                "💡 Most errors appear to be temporary - consider retrying the failed transfers"
            )

    def _display_rich_error_summary(
        self,
        error_summary: Dict[ErrorCategory, ErrorSummary],
        recommendations: list[str]
    ) -> None:
        """Display error summary in rich mode (tables and panels).

        Args:
            error_summary: Dictionary of error categories and their summaries
            recommendations: List of actionable recommendations
        """
        self._console_output("[bold red]Error Analysis[/bold red]")

        # Error category table
        error_table = Table(
            title="Errors by Category", show_header=True, header_style="bold red"
        )
        error_table.add_column("Category", style="red")
        error_table.add_column("Count", justify="center")
        error_table.add_column("Retryable", justify="center")
        error_table.add_column("User Action Required", justify="center")

        for category, summary in error_summary.items():
            category_name = self._format_category_name(category)
            retryable = "✓" if summary.is_retryable else "✗"
            user_action = "✓" if summary.requires_user_action else "✗"

            error_table.add_row(
                category_name,
                str(summary.count),
                f"[green]{retryable}[/green]"
                if summary.is_retryable
                else f"[red]{retryable}[/red]",
                f"[yellow]{user_action}[/yellow]"
                if summary.requires_user_action
                else f"[green]{user_action}[/green]",
            )

        self._console_output(error_table)

        # Recommendations panel
        if recommendations:
            self._console_output("")
            rec_text = "\n".join(f"• {rec}" for rec in recommendations)
            self._console_output(
                Panel(
                    rec_text,
                    title="[bold yellow]Recommended Actions[/bold yellow]",
                    box=rich_box.ROUNDED,
                )
            )

        # Retry suggestion
        if self.error_aggregator.should_suggest_retry():
            self._console_output("")
            self._console_output(
                Panel(
                    "Most errors appear to be temporary issues that may resolve on retry.",
                    title="[bold green]💡 Retry Suggestion[/bold green]",
                    box=rich_box.ROUNDED,
                    border_style="green",
                )
            )

    def _display_failed_transfer_details(
        self, error_summary: Dict[ErrorCategory, ErrorSummary]
    ) -> None:
        """Display individual failed transfer details in rich mode.

        Args:
            error_summary: Dictionary of error categories and their summaries
        """
        self._console_output("")
        self._console_output("[bold red]Failed Transfers Details:[/bold red]")

        for category, summary in error_summary.items():
            if summary.errors:
                category_name = self._format_category_name(category)
                self._console_output(
                    f"\n[red]{category_name} ({len(summary.errors)} errors):[/red]"
                )

                for error in summary.errors[:3]:  # Show first 3 errors per category
                    self._console_output(
                        f"  [red]✗[/red] {error.source_image}:{error.source_tag} → {error.target_repository}:{error.target_tag}"
                    )

                if len(summary.errors) > 3:
                    self._console_output(
                        f"  [dim]... and {len(summary.errors) - 3} more[/dim]"
                    )

    def _show_error_summary(self, simple_mode: bool = False) -> None:
        """Show categorized error summary with actionable guidance.

        Orchestrates error display by delegating to mode-specific helpers.

        Args:
            simple_mode: Whether to show simplified or rich error display
        """
        error_summary = self.error_aggregator.get_error_summary()
        recommendations = self.error_aggregator.get_actionable_recommendations()

        if not error_summary:
            return

        self._console_output("")

        if simple_mode:
            self._display_simple_error_summary(error_summary, recommendations)
        else:
            self._display_rich_error_summary(error_summary, recommendations)
            self._display_failed_transfer_details(error_summary)

    @contextmanager
    def live_display(self):
        """Context manager for static progress display (no screen clearing)."""
        try:
            yield self
        finally:
            pass

    def get_batch_statistics(self) -> Dict[str, Any]:
        """Get batch operation statistics.

        Returns:
            Dictionary with batch statistics
        """
        completed = sum(
            1 for p in self.transfers.values() if p.status == TransferStatus.COMPLETED
        )
        failed = sum(
            1 for p in self.transfers.values() if p.status == TransferStatus.FAILED
        )
        skipped = sum(
            1 for p in self.transfers.values() if p.status == TransferStatus.SKIPPED
        )
        running = sum(
            1 for p in self.transfers.values() if p.status == TransferStatus.RUNNING
        )
        pending = sum(
            1 for p in self.transfers.values() if p.status == TransferStatus.PENDING
        )

        duration = None
        if self.batch_start_time:
            end_time = self.batch_end_time or time.time()
            duration = end_time - self.batch_start_time

        # Cache length calculation to avoid repeated calls
        total_transfers = len(self.transfers)

        return {
            "total_transfers": total_transfers,
            "completed": completed,
            "failed": failed,
            "skipped": skipped,
            "running": running,
            "pending": pending,
            "success_rate": completed / total_transfers if total_transfers else 0,
            "duration_seconds": duration,
            "total_retries": sum(p.retry_count for p in self.transfers.values()),
            "avg_duration_per_transfer": sum(
                p.duration or 0 for p in self.transfers.values()
            )
            / total_transfers
            if total_transfers
            else 0,
        }

    def skip_transfer(self, transfer_id: str, skip_reason: str) -> None:
        """Mark transfer as skipped.

        Args:
            transfer_id: Transfer identifier
            skip_reason: Reason why transfer was skipped
        """
        if transfer_id not in self.transfers:
            return

        progress = self.transfers[transfer_id]
        progress.status = TransferStatus.SKIPPED
        progress.end_time = time.time()
        progress.error_message = skip_reason

        req = progress.request
        transfer_num = int(transfer_id.split("_")[1]) + 1
        total = len(self.transfers)

        # Log structured event
        self._log_structured(
            "transfer_skipped",
            transfer_id=transfer_id,
            transfer_num=transfer_num,
            total_transfers=total,
            source=req.source,
            source_tag=req.source_tag,
            target=req.target,
            target_tag=req.target_tag,
            skip_reason=skip_reason,
            timestamp=progress.end_time,
        )

        if self.simple_mode:
            # Simple mode: show skip status
            self._console_output(
                f"[{transfer_num}/{total}] ‥ Skipped {req.source}:{req.source_tag} → {req.target}:{req.target_tag}"
            )
            self._console_output(f"    Reason: {skip_reason}")
        else:
            # Complex mode: update progress bar to show skipped
            if self.progress and transfer_id in self.transfer_tasks:
                task_id = self.transfer_tasks[transfer_id]

                self.progress.update(
                    task_id,
                    completed=100,
                    description=f"[yellow]‥ Transfer {transfer_num}: {req.source}:{req.source_tag} → {req.target}:{req.target_tag} (Skipped)",
                )

                # Update overall progress
                if self.overall_task is not None:
                    completed_count = sum(
                        1 for p in self.transfers.values() if p.is_complete
                    )
                    self.progress.update(self.overall_task, completed=completed_count)

            self._update_status_line(transfer_id)

    def show_detailed_status(self) -> None:
        """Show detailed status of all transfers."""
        if not self.transfers:
            self._console_output("No transfers to show")
            return

        table = Table(
            title="Transfer Status", show_header=True, header_style="bold blue"
        )
        table.add_column("Source", style="dim")
        table.add_column("Target", style="dim")
        table.add_column("Status")
        table.add_column("Retries", justify="center")
        table.add_column("Duration", justify="right")
        table.add_column("Error", style="red")

        for progress in self.transfers.values():
            req = progress.request
            source = f"{req.source}:{req.source_tag}"
            target = f"{req.target}:{req.target_tag}"

            # Status with color
            status_colors = {
                TransferStatus.PENDING: "white",
                TransferStatus.RUNNING: "blue",
                TransferStatus.RETRYING: "yellow",
                TransferStatus.COMPLETED: "green",
                TransferStatus.FAILED: "red",
                TransferStatus.SKIPPED: "yellow",
            }
            status_color = status_colors[progress.status]
            status_text = f"[{status_color}]{progress.status.value}[/{status_color}]"

            # Duration
            duration_text = ""
            if progress.duration is not None:
                duration_text = f"{progress.duration:.1f}s"

            # Retry count
            retry_text = str(progress.retry_count) if progress.retry_count > 0 else "-"

            # Error message - optimize string handling to avoid concatenation
            error_text = progress.error_message or ""
            if len(error_text) > 40:
                # Use f-string for better performance than + concatenation
                error_text = f"{error_text[:37]}..."

            table.add_row(
                source, target, status_text, retry_text, duration_text, error_text
            )

        self._console_output(table)

    def _update_status_line(self, transfer_id: str) -> None:
        """Update status line for a transfer using ANSI cursor positioning.

        Args:
            transfer_id: Transfer identifier
        """
        if transfer_id not in self.transfers or transfer_id not in self.transfer_lines:
            return

        progress = self.transfers[transfer_id]
        req = progress.request

        # Get current status symbol
        symbol = STATUS_SYMBOLS.get(progress.status, "❓")

        # Build status line
        status_line = (
            f"{symbol} {req.source}:{req.source_tag} → {req.target}:{req.target_tag}"
        )

        # Add retry count if applicable
        if progress.retry_count > 0:
            status_line += f" (retry {progress.retry_count})"

        # Add current operation if running
        if progress.status == TransferStatus.RUNNING and progress.current_operation:
            status_line += f" - {progress.current_operation}"

        # Add error message if failed
        if progress.status == TransferStatus.FAILED and progress.error_message:
            error_msg = progress.error_message
            if len(error_msg) > 50:
                error_msg = error_msg[:47] + "..."
            status_line += f" - {error_msg}"

        # Calculate lines to move up from current position
        line_index = self.transfer_lines[transfer_id]
        lines_up = self.current_line - line_index

        # Move cursor up, update line, move cursor back down (only in console mode)
        if self.output_mode == OUTPUT_MODE_CONSOLE:
            if lines_up > 0:
                self.console.print(
                    f"\033[{lines_up}A\r{status_line}\033[{lines_up}B", end=""
                )
            else:
                self.console.print(f"\r{status_line}", end="")

            # Ensure we're at the correct position for next output
            self.console.print("", end="", flush=True)
