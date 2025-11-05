"""Terminal capability detection information command."""

import click
from rich.console import Console
from rich.table import Table

from ...terminal_detection import get_terminal_info

console = Console()


@click.command()
@click.pass_context
def terminal_info(ctx):
    """Show terminal capability detection information.

    This command helps debug terminal detection issues and shows
    what UI mode will be selected automatically.

    Environment variables that affect detection:
    - ECRESHORE_SIMPLE_MODE: Force simple mode
    - ECRESHORE_RICH_MODE: Force rich mode
    - NO_COLOR: Disable colors
    - FORCE_COLOR: Force colors
    - CI: Indicates CI environment
    """
    terminal_info_data = get_terminal_info()

    # Create summary table
    info_table = Table(
        title="Terminal Detection Information",
        show_header=True,
        header_style="bold blue",
    )
    info_table.add_column("Property", style="cyan", width=20)
    info_table.add_column("Value", style="white", width=30)
    info_table.add_column("Description", style="dim", width=40)

    info_table.add_row(
        "TTY", str(terminal_info_data["is_tty"]), "Is output connected to a terminal"
    )
    info_table.add_row(
        "TERM", terminal_info_data["term"], "Terminal type environment variable"
    )
    info_table.add_row(
        "COLORTERM", terminal_info_data["colorterm"], "Color terminal capabilities"
    )
    info_table.add_row(
        "Platform", terminal_info_data["platform"], "Operating system platform"
    )
    info_table.add_row(
        "CI Detected",
        str(terminal_info_data["ci_detected"]),
        "CI/CD environment detected",
    )
    info_table.add_row(
        "NO_COLOR", str(terminal_info_data["no_color"]), "NO_COLOR environment variable"
    )
    info_table.add_row(
        "FORCE_COLOR",
        str(terminal_info_data["force_color"]),
        "FORCE_COLOR environment variable",
    )

    if terminal_info_data["platform"] == "win32":
        info_table.add_row(
            "WT Session",
            str(terminal_info_data["wt_session"]),
            "Windows Terminal detected",
        )
        info_table.add_row(
            "ConEmu ANSI", str(terminal_info_data["conemu_ansi"]), "ConEmu ANSI support"
        )

    info_table.add_row("", "", "")
    info_table.add_row(
        "[bold]ANSI Support[/bold]",
        str(terminal_info_data["supports_ansi"]),
        "Terminal supports ANSI colors",
    )
    info_table.add_row(
        "[bold]Default UI Mode[/bold]",
        "Rich" if terminal_info_data["should_use_rich"] else "Simple",
        "Automatically selected UI mode",
    )

    console.print(info_table)

    # Show override instructions
    console.print("\n[bold]Environment Variable Overrides:[/bold]")
    console.print("  [cyan]ECRESHORE_SIMPLE_MODE=1[/cyan] - Force simple mode")
    console.print("  [cyan]ECRESHORE_RICH_MODE=1[/cyan] - Force rich mode")
    console.print("  [cyan]NO_COLOR=1[/cyan] - Disable colors")
    console.print("  [cyan]FORCE_COLOR=1[/cyan] - Force colors")
