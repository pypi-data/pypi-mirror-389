"""Batch processing command for executing multiple image transfers."""

import asyncio
import sys
from dataclasses import dataclass

import click
from rich.console import Console

from ...terminal_detection import get_terminal_info, should_use_rich_ui
from ..utils.logging_setup import setup_structured_logging
from ..utils.ui_helpers import determine_ui_mode

console = Console()


# ============================================================================
# Validation and Configuration Helpers
# ============================================================================


@dataclass
class BatchExecutionConfig:
    """Validated batch execution configuration.

    This dataclass encapsulates all validated flags and settings for batch execution.
    Created by _validate_batch_flags() to ensure type safety and clear parameter passing.
    """

    config_file: str
    dry_run: bool
    output: str  # "console" or "log"
    use_rich_ui: bool
    force: bool
    verbose: int
    debug_skip_decisions: bool
    skip_audit_trail: bool
    explain_skips: bool

    @property
    def skip_debug_enabled(self) -> bool:
        """Check if any skip debug flag is enabled."""
        return self.debug_skip_decisions or self.skip_audit_trail or self.explain_skips


def _validate_batch_flags(
    simple: bool,
    rich: bool,
    output: str,
    debug_skip_decisions: bool,
    skip_audit_trail: bool,
    explain_skips: bool,
) -> None:
    """Validate batch command flag combinations.

    PURE FUNCTION: No I/O, easily testable.

    Args:
        simple: Force simple UI mode flag
        rich: Force rich UI mode flag
        output: Output mode ("console" or "log")
        debug_skip_decisions: Enable skip decision debugging
        skip_audit_trail: Enable skip audit trail
        explain_skips: Enable skip explanations

    Raises:
        ValueError: If flag combination is invalid

    Examples:
        >>> _validate_batch_flags(simple=True, rich=True, output="console",
        ...                       debug_skip_decisions=False, skip_audit_trail=False,
        ...                       explain_skips=False)
        Traceback (most recent call last):
        ValueError: Cannot use both --simple and --rich flags

        >>> _validate_batch_flags(simple=False, rich=False, output="log",
        ...                       debug_skip_decisions=True, skip_audit_trail=False,
        ...                       explain_skips=False)
        Traceback (most recent call last):
        ValueError: Skip debug flags are not compatible with --output log
    """
    # Check for conflicting UI mode flags
    if simple and rich:
        raise ValueError("Cannot use both --simple and --rich flags")

    # Check for incompatible skip debug + log output
    skip_debug_enabled = any([debug_skip_decisions, skip_audit_trail, explain_skips])
    if skip_debug_enabled and output == "log":
        raise ValueError("Skip debug flags are not compatible with --output log")


def _setup_skip_debug_environment(config: BatchExecutionConfig) -> None:
    """Configure environment variables for skip debug modes.

    SIDE-EFFECT FUNCTION: Sets environment variables for service layer to pick up.

    Args:
        config: Validated batch execution configuration

    Note:
        This function is testable by mocking os.environ or checking env var values.
    """
    import os

    if config.debug_skip_decisions:
        os.environ["ECRESHORE_DEBUG_SKIP_DECISIONS"] = "1"
    if config.skip_audit_trail:
        os.environ["ECRESHORE_SKIP_AUDIT_TRAIL"] = "1"
    if config.explain_skips:
        os.environ["ECRESHORE_EXPLAIN_SKIPS"] = "1"




def _configure_output_mode(output: str, verbose: int) -> None:
    """Configure structured logging and console suppression for output mode."""
    if output == "log":
        setup_structured_logging()


def _configure_skip_debug_logging(
    debug_skip_decisions: bool,
    skip_audit_trail: bool,
    explain_skips: bool,
    verbose: int,
) -> None:
    """Configure skip-specific debug logging."""
    import logging

    # Enable debug level for skip decision logger
    skip_logger = logging.getLogger("skip_decisions")
    skip_logger.setLevel(logging.DEBUG)

    # Enable debug level for image presence checker
    presence_logger = logging.getLogger("ecreshore.services.image_presence_checker")
    presence_logger.setLevel(logging.DEBUG)

    # Set up structlog for skip decisions if not already configured
    try:
        import structlog

        # Configure skip decision context
        if debug_skip_decisions or skip_audit_trail:
            console.print("[dim]Skip decision debug logging enabled[/dim]")
        if explain_skips:
            console.print("[dim]Human-readable skip analysis enabled[/dim]")
    except ImportError:
        console.print(
            "[yellow]Warning: structlog not available, using standard logging[/yellow]"
        )


def _show_config_loading_messages(
    result_data, output: str, verbose: int, progress_reporter
):
    """Show configuration loading status messages."""
    if output == "log":
        return

    # Show config loading results
    progress_reporter.info("Configuration loaded successfully")
    if verbose:
        config_stats = result_data.get("config_stats", {})
        transfers_count = config_stats.get("total_transfers", 0)
        progress_reporter.info(f"Found {transfers_count} transfers to process")


def _handle_batch_ui_output(
    result_data,
    output: str,
    verbose: int,
    use_rich_ui: bool,
    dry_run: bool,
    progress_reporter,
):
    """Handle output for batch results based on the output mode."""
    if output == "log":
        # Log mode - minimal output, results already logged
        return

    # Console mode - show summary
    if progress_reporter:
        # Extract counts from batch result
        batch_result = result_data.get("batch_result")
        if batch_result:
            success_count = batch_result.success_count
            failure_count = batch_result.failure_count
            # Count skipped transfers from progress reporter
            skip_count = progress_reporter.get_batch_statistics().get("skipped", 0)
        else:
            # Fallback for dry run or other cases
            success_count = result_data.get("success_count", 0)
            skip_count = result_data.get("skip_count", 0)
            failure_count = result_data.get("failure_count", 0)

        if dry_run:
            progress_reporter.info(
                f"Dry run completed: {success_count + skip_count + failure_count} transfers analyzed"
            )
        else:
            progress_reporter.success(
                f"Batch processing completed: {success_count} transferred, "
                f"{skip_count} skipped, {failure_count} failed"
            )


def _handle_keyboard_interrupt(output: str) -> None:
    """Handle keyboard interrupt based on output mode."""
    if output == "log":
        import structlog

        logger = structlog.get_logger()
        logger.warning("Batch operation cancelled by user")
    else:
        console.print("\n[yellow]Batch operation cancelled by user[/yellow]")
    sys.exit(1)


def _handle_unexpected_error(error: Exception, output: str) -> None:
    """Handle unexpected errors based on output mode."""
    if output == "log":
        import structlog

        logger = structlog.get_logger()
        logger.error("Batch operation failed", error=str(error))
    else:
        console.print(f"[bold red]Batch operation failed:[/bold red] {error}")
    sys.exit(1)


@click.command()
@click.argument("config_file")
@click.option(
    "--dry-run", is_flag=True, help="Show what would be transferred without executing"
)
@click.option(
    "--output",
    type=click.Choice(["console", "log"]),
    default="console",
    help="Output format: console (default, rich UI) or log (JSON structured logs)",
)
@click.option(
    "--simple",
    is_flag=True,
    help="Force simple progress display (auto-detected by default)",
)
@click.option(
    "--rich",
    is_flag=True,
    help="Force rich UI progress display (auto-detected by default)",
)
@click.option(
    "--force",
    is_flag=True,
    help="Force transfer even if image already exists in target",
)
@click.option(
    "--debug-skip-decisions",
    is_flag=True,
    help="Enable detailed skip decision logging for troubleshooting",
)
@click.option(
    "--skip-audit-trail",
    is_flag=True,
    help="Show complete decision path for each skip evaluation",
)
@click.option(
    "--explain-skips",
    is_flag=True,
    help="Human-readable skip analysis with recommendations",
)
@click.pass_context
def batch(
    ctx,
    config_file: str,
    dry_run: bool,
    output: str,
    simple: bool,
    rich: bool,
    force: bool,
    debug_skip_decisions: bool,
    skip_audit_trail: bool,
    explain_skips: bool,
):
    """Execute batch transfers from YAML configuration file.

    CONFIG_FILE: Path to YAML configuration file

    ECReshore automatically detects your terminal capabilities and chooses
    the best UI mode. Use --simple or --rich to override auto-detection.

    Run 'ecreshore terminal-info' to see your terminal's capabilities.

    Examples:
      # Execute batch transfers from config file
      ecreshore batch transfers.yml

      # Preview what would be transferred without executing
      ecreshore batch transfers.yml --dry-run

      # Debug skip-if-present issues with detailed logging
      ecreshore batch transfers.yml --debug-skip-decisions

      # Human-readable skip analysis
      ecreshore batch transfers.yml --explain-skips

      # Complete decision path tracking for troubleshooting
      ecreshore batch transfers.yml --skip-audit-trail

      # Force simple progress display (no rich UI)
      ecreshore batch transfers.yml --simple

      # Force rich UI progress display
      ecreshore batch transfers.yml --rich

      # Output structured logs instead of progress UI
      ecreshore batch transfers.yml --output log
    """
    verbose = ctx.obj.get("verbose", False)

    # 1. Validate flags (pure function - testable without Click)
    try:
        _validate_batch_flags(
            simple=simple,
            rich=rich,
            output=output,
            debug_skip_decisions=debug_skip_decisions,
            skip_audit_trail=skip_audit_trail,
            explain_skips=explain_skips,
        )
    except ValueError as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        sys.exit(1)

    # 2. Determine UI mode
    use_rich_ui = determine_ui_mode(simple, rich, output, verbose)

    # 3. Build configuration object
    config = BatchExecutionConfig(
        config_file=config_file,
        dry_run=dry_run,
        output=output,
        use_rich_ui=use_rich_ui,
        force=force,
        verbose=verbose,
        debug_skip_decisions=debug_skip_decisions,
        skip_audit_trail=skip_audit_trail,
        explain_skips=explain_skips,
    )

    # 4. Configure skip debug logging and environment
    if config.skip_debug_enabled:
        _configure_skip_debug_logging(
            debug_skip_decisions, skip_audit_trail, explain_skips, verbose
        )
        _setup_skip_debug_environment(config)

    # 5. Configure output mode
    _configure_output_mode(output, verbose)

    # 6. Create progress reporter for real-time skip tracking
    progress_reporter = None
    if output == "console":
        from ...services.batch_progress import BatchProgressReporter

        progress_reporter = BatchProgressReporter(
            console=console,
            verbose=bool(verbose),
            simple_mode=not use_rich_ui,  # Invert: rich UI means NOT simple mode
            output_mode="console",
        )

    # 7. Execute batch with connected progress reporter
    from ...services.batch_processor import BatchProcessor

    batch_processor = BatchProcessor()

    async def run_enhanced_batch():
        return await batch_processor.execute_batch_enhanced(
            config_file,
            dry_run,
            use_rich_ui=use_rich_ui,
            force=force,
            progress_reporter=progress_reporter,
        )

    try:
        # First, show configuration loading (without executing batch yet)
        temp_result_data = asyncio.run(
            batch_processor.load_and_validate_config(config_file)
        )

        # Create proper ProgressReporter for config loading messages
        from ...services.progress_reporter import ProgressReporter

        config_progress_reporter = ProgressReporter(
            console=console, verbose=bool(verbose)
        )
        _show_config_loading_messages(
            temp_result_data, output, verbose, config_progress_reporter
        )

        # Now execute the actual batch
        result_data = asyncio.run(run_enhanced_batch())
        _handle_batch_ui_output(
            result_data, output, verbose, use_rich_ui, dry_run, progress_reporter
        )

    except KeyboardInterrupt:
        _handle_keyboard_interrupt(output)
    except Exception as e:
        _handle_unexpected_error(e, output)
