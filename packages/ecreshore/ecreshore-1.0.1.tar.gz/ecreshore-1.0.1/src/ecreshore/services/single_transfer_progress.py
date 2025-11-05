"""Single transfer progress reporting with identical rich UI as batch operations."""

import logging
import time
from typing import Optional

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

from .progress_reporter import ProgressReporter
from .transfer_service import TransferRequest
from .output_modes import OUTPUT_MODE_CONSOLE

logger = logging.getLogger(__name__)


class SingleTransferProgressReporter:
    """Progress reporter for single transfer operations with identical rich UI as batch."""

    def __init__(
        self,
        console: Optional[Console] = None,
        verbose: bool = False,
        simple_mode: bool = False,
        output_mode: str = OUTPUT_MODE_CONSOLE,
    ):
        """Initialize single transfer progress reporter.

        Args:
            console: Rich console instance
            verbose: Enable verbose logging
            simple_mode: Use simplified output without rich components
            output_mode: Output mode ('console' or 'log')
        """
        self.console = console or Console()
        self.verbose = verbose
        self.simple_mode = simple_mode
        self.output_mode = output_mode
        self.base_reporter = ProgressReporter(console, verbose)

        # Progress tracking
        self.transfer_request: Optional[TransferRequest] = None
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None
        self.current_operation: str = ""
        self.success: Optional[bool] = None
        self.error_message: Optional[str] = None

        # Rich progress components (only used in rich mode)
        self.progress: Optional[Progress] = None
        self.live: Optional[Live] = None
        self.transfer_task: Optional[int] = None
        self.overall_task: Optional[int] = None

    def _console_output(self, message, **rich_kwargs) -> None:
        """Output to console for console output mode."""
        if self.output_mode == OUTPUT_MODE_CONSOLE:
            self.console.print(message, **rich_kwargs)

    def start_transfer(self, request: TransferRequest) -> None:
        """Start single transfer operation tracking.

        Args:
            request: Transfer request to track
        """
        self.transfer_request = request
        self.start_time = time.time()
        self.end_time = None
        self.current_operation = "Starting"

        if self.simple_mode:
            # Simple mode: just show basic info
            self._console_output(
                f"Starting transfer: {request.source_image}:{request.source_tag} → {request.target_repository}:{request.target_tag}"
            )
        else:
            # Rich mode: setup identical progress display as batch
            self._console_output(
                f"[bold blue]Starting transfer: {request.source_image}:{request.source_tag} → {request.target_repository}:{request.target_tag}[/bold blue]"
            )
            self._console_output("")

            # Initialize identical rich progress display as BatchProgressReporter
            self.progress = Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(bar_width=20),
                "[progress.percentage]{task.percentage:>3.0f}%",
                TextColumn("[dim]{task.completed}/{task.total}"),
                TimeElapsedColumn(),
                console=self.console,
                transient=False,
            )

            # Add overall progress task (1 transfer)
            self.overall_task = self.progress.add_task(
                "[bold cyan]Overall Progress", total=1, completed=0
            )

            # Add individual transfer task
            description = f"Transfer 1: {request.source_image}:{request.source_tag} → {request.target_repository}:{request.target_tag}"
            self.transfer_task = self.progress.add_task(
                description,
                total=100,
                completed=0,
                visible=False,  # Initially hidden, show when started
            )

            # Start the live display
            self.live = Live(self.progress, console=self.console, refresh_per_second=10)
            self.live.start()

            # Show the transfer task as started
            if self.transfer_task is not None:
                self.progress.update(self.transfer_task, visible=True, completed=0)
                self.progress.update(
                    self.transfer_task,
                    description=f"[yellow]▶ Transfer 1: {request.source_image}:{request.source_tag} → {request.target_repository}:{request.target_tag}",
                )

        if self.verbose:
            self.base_reporter.start_transfer(
                request.source_image,
                request.target_repository,
                request.source_tag,
                request.target_tag,
            )

    def update_operation(self, operation: str, progress_pct: int = 0) -> None:
        """Update current operation for the transfer.

        Args:
            operation: Current operation description
            progress_pct: Progress percentage (0-100)
        """
        if not self.transfer_request:
            return

        self.current_operation = operation

        # Update rich progress bar in rich mode
        if not self.simple_mode and self.progress and self.transfer_task is not None:
            req = self.transfer_request

            # Update progress bar with current operation - identical to batch formatting
            self.progress.update(
                self.transfer_task,
                completed=progress_pct,
                description=f"[yellow]▶ Transfer 1: {operation} - {req.source_image}:{req.source_tag}",
            )

    def _build_transfer_description(
        self, req: TransferRequest, duration: float, success: bool
    ) -> str:
        """Build transfer description string - pure function.

        Args:
            req: Transfer request with source/target info
            duration: Transfer duration in seconds
            success: Whether transfer succeeded

        Returns:
            Formatted description string
        """
        duration_str = f"{duration:.1f}s"
        source_ref = f"{req.source_image}:{req.source_tag}"
        target_ref = f"{req.target_repository}:{req.target_tag}"

        if success:
            return f"✓ Completed {source_ref} → {target_ref} ({duration_str})"
        else:
            return f"✗ Failed {source_ref} → {target_ref} ({duration_str})"

    def _format_completion_status_simple(
        self, success: bool, error_message: Optional[str], duration: float
    ) -> list[str]:
        """Format simple mode completion status - pure function.

        Args:
            success: Whether transfer succeeded
            error_message: Error message if failed
            duration: Transfer duration in seconds

        Returns:
            List of status message lines
        """
        lines = []
        duration_str = f"{duration:.1f}s"

        if success:
            lines.append(f"✓ Completed ({duration_str})")
        else:
            lines.append(f"✗ Failed ({duration_str})")
            if error_message:
                lines.append(f"    Error: {error_message}")

        return lines

    def _format_rich_progress_description(
        self, req: TransferRequest, duration: float, success: bool
    ) -> str:
        """Format Rich progress bar description - pure function.

        Args:
            req: Transfer request with source/target info
            duration: Transfer duration in seconds
            success: Whether transfer succeeded

        Returns:
            Formatted Rich description with markup
        """
        duration_str = f"{duration:.1f}s"
        source_ref = f"{req.source_image}:{req.source_tag}"
        target_ref = f"{req.target_repository}:{req.target_tag}"

        if success:
            return f"[green]✓ Transfer 1: {source_ref} → {target_ref} ({duration_str})"
        else:
            return f"[red]✗ Transfer 1: {source_ref} → {target_ref} (Failed)"

    def complete_transfer(
        self, success: bool, error_message: Optional[str] = None
    ) -> None:
        """Mark transfer as completed.

        Args:
            success: Whether transfer succeeded
            error_message: Error message if failed
        """
        if not self.transfer_request:
            return

        self.end_time = time.time()
        self.success = success
        self.error_message = error_message

        req = self.transfer_request
        duration = self.end_time - (self.start_time or self.end_time)

        if self.simple_mode:
            # Simple mode: use extracted helper for formatting
            description = self._build_transfer_description(req, duration, success)
            self._console_output(description)

            if not success and error_message:
                self._console_output(f"    Error: {error_message}")
        else:
            # Rich mode: update progress bar using extracted helper
            if self.progress and self.transfer_task is not None:
                description = self._format_rich_progress_description(req, duration, success)
                self.progress.update(
                    self.transfer_task,
                    completed=100,
                    description=description,
                )

                # Update overall progress
                if self.overall_task is not None:
                    self.progress.update(self.overall_task, completed=1)

        if self.verbose:
            self.base_reporter.transfer_complete(
                req.source_image,
                req.target_repository,
                req.source_tag,
                req.target_tag,
                success,
            )
            if not success and error_message:
                self.base_reporter.error(error_message)

    def finish_transfer(self) -> None:
        """Complete transfer operation tracking and show summary."""
        if not self.transfer_request:
            return

        duration = (self.end_time or time.time()) - (self.start_time or time.time())

        if self.simple_mode:
            # Simple mode: minimal summary
            self._console_output("")
            if self.success:
                self._console_output(
                    f"✓ Transfer completed successfully in {duration:.1f}s"
                )
            else:
                self._console_output(f"✗ Transfer failed in {duration:.1f}s")
                if self.error_message:
                    self._console_output(f"Error: {self.error_message}")
        else:
            # Rich mode: stop live display and show identical summary as batch
            if self.live:
                self.live.stop()

            self._console_output("")
            if self.success:
                self._console_output(
                    "[bold green]✓ Transfer completed successfully![/bold green]"
                )
                self._console_output(f"[dim]Total time: {duration:.1f} seconds[/dim]")
            else:
                self._console_output("[bold red]✗ Transfer failed[/bold red]")
                self._console_output(f"[dim]Total time: {duration:.1f} seconds[/dim]")
                if self.error_message:
                    self._console_output(f"[red]Error: {self.error_message}[/red]")

            # Show identical summary table as batch
            summary_table = Table(show_header=False, box=None, padding=(0, 1))
            summary_table.add_row(
                "Completed:", f"[green]{1 if self.success else 0}[/green]"
            )
            summary_table.add_row("Failed:", f"[red]{0 if self.success else 1}[/red]")
            summary_table.add_row("Total:", "1")
            summary_table.add_row("Duration:", f"{duration:.1f}s")

            from rich import box

            self._console_output(
                Panel(summary_table, title="Transfer Summary", box=box.ROUNDED)
            )

    def skip_transfer(self, skip_reason: str) -> None:
        """Mark transfer as skipped.

        Args:
            skip_reason: Reason why transfer was skipped
        """
        if not self.transfer_request:
            return

        self.end_time = time.time()
        self.success = True  # Skipped is considered successful
        self.error_message = skip_reason

        req = self.transfer_request

        if self.simple_mode:
            # Simple mode: show skip status
            self._console_output(
                f"‥ Skipped {req.source_image}:{req.source_tag} → {req.target_repository}:{req.target_tag}"
            )
            self._console_output(f"    Reason: {skip_reason}")
        else:
            # Rich mode: update progress bar to show skipped - identical to batch formatting
            if self.progress and self.transfer_task is not None:
                self.progress.update(
                    self.transfer_task,
                    completed=100,
                    description=f"[yellow]‥ Transfer 1: {req.source_image}:{req.source_tag} → {req.target_repository}:{req.target_tag} (Skipped)",
                )

                # Update overall progress
                if self.overall_task is not None:
                    self.progress.update(self.overall_task, completed=1)

    def show_detailed_status(self) -> None:
        """Show detailed status of the transfer."""
        if not self.transfer_request:
            self._console_output("No transfer to show")
            return

        req = self.transfer_request
        source = f"{req.source_image}:{req.source_tag}"
        target = f"{req.target_repository}:{req.target_tag}"

        # Status with color
        if self.success is None:
            status_text = "[blue]running[/blue]"
        elif self.success:
            status_text = "[green]completed[/green]"
        else:
            status_text = "[red]failed[/red]"

        # Duration
        duration_text = ""
        if self.start_time and self.end_time:
            duration = self.end_time - self.start_time
            duration_text = f"{duration:.1f}s"

        # Error message
        error_text = self.error_message or ""
        if len(error_text) > 40:
            error_text = error_text[:37] + "..."

        table = Table(
            title="Transfer Status", show_header=True, header_style="bold blue"
        )
        table.add_column("Source", style="dim")
        table.add_column("Target", style="dim")
        table.add_column("Status")
        table.add_column("Duration", justify="right")
        table.add_column("Error", style="red")

        table.add_row(source, target, status_text, duration_text, error_text)

        self._console_output(table)
