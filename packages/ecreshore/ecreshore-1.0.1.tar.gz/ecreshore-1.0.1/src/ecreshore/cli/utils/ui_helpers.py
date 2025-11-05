"""Shared UI helper functions for CLI commands."""

from rich.console import Console

from ...terminal_detection import get_terminal_info, should_use_rich_ui

console = Console()


def determine_ui_mode(simple: bool, rich: bool, output: str, verbose: int) -> bool:
    """Determine UI mode based on flags and terminal capabilities.

    Args:
        simple: Force simple UI mode flag
        rich: Force rich UI mode flag
        output: Output mode ("console" or "log")
        verbose: Verbosity level

    Returns:
        True if rich UI should be used, False for simple mode
    """
    if output == "log":
        return False

    if not simple and not rich:
        use_rich_ui = should_use_rich_ui()
        if verbose >= 2:  # Debug mode
            terminal_info = get_terminal_info()
            console.print(f"[dim]Terminal detection: {terminal_info}[/dim]")
            console.print(
                f"[dim]Auto-selected UI mode: {'rich' if use_rich_ui else 'simple'}[/dim]"
            )
        return use_rich_ui
    else:
        return rich and not simple
