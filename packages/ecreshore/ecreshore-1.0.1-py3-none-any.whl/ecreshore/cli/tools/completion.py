"""Shell completion script generation command."""

import os
import subprocess
import sys
from typing import Optional

import click
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax

console = Console()


@click.command()
@click.option(
    "--shell",
    type=click.Choice(["bash", "zsh", "fish"]),
    help="Generate completion script for specific shell (auto-detected if not specified)",
)
@click.option(
    "--install",
    is_flag=True,
    help="Show installation instructions instead of outputting script",
)
@click.pass_context
def completion(ctx, shell: Optional[str], install: bool):
    """Generate shell completion scripts or show installation instructions.

    This command generates shell completion scripts for Bash, Zsh, and Fish shells.
    The completion scripts enable tab completion for commands, options, and file paths.

    By default, the shell type is auto-detected from your environment. Use --shell
    to generate scripts for a specific shell.

    Examples:
      # Generate completion script for current shell
      ecreshore completion

      # Generate Bash completion script
      ecreshore completion --shell bash

      # Show installation instructions
      ecreshore completion --install

      # Install completion for current user (Bash example)
      ecreshore completion --shell bash > ~/.bash_completion.d/ecreshore
      source ~/.bash_completion.d/ecreshore
    """
    # Auto-detect shell if not specified
    if not shell:
        shell_env = os.environ.get("SHELL", "")
        if "bash" in shell_env:
            shell = "bash"
        elif "zsh" in shell_env:
            shell = "zsh"
        elif "fish" in shell_env:
            shell = "fish"
        else:
            console.print(
                "[yellow]Could not auto-detect shell. Please specify --shell option.[/yellow]"
            )
            console.print("Supported shells: bash, zsh, fish")
            sys.exit(1)

    if install:
        _show_completion_installation_instructions(shell)
        return

    # Generate completion script using Click's built-in functionality
    env_var = "_ECRESHORE_COMPLETE"
    completion_type = f"{shell}_source"

    try:
        # Generate the completion script
        env = os.environ.copy()
        env[env_var] = completion_type

        result = subprocess.run(
            ["ecreshore"], env=env, capture_output=True, text=True, timeout=10
        )

        if result.returncode == 0:
            console.print(result.stdout, end="")
        else:
            console.print(
                f"[red]Error generating completion script:[/red] {result.stderr}"
            )
            sys.exit(1)

    except subprocess.TimeoutExpired:
        console.print("[red]Error:[/red] Completion script generation timed out")
        sys.exit(1)
    except FileNotFoundError:
        console.print("[red]Error:[/red] ecreshore command not found in PATH")
        console.print("Make sure ecreshore is properly installed")
        sys.exit(1)


def _show_completion_installation_instructions(shell: str) -> None:
    """Display shell-specific installation instructions."""
    console.print(f"\n[bold]Shell Completion Installation for {shell.upper()}[/bold]\n")

    if shell == "bash":
        script_content = """# Generate and install completion script
ecreshore completion --shell bash > ~/.bash_completion.d/ecreshore

# Source the completion (add to ~/.bashrc for permanent installation)
source ~/.bash_completion.d/ecreshore

# Alternative: Add to ~/.bashrc for automatic loading
echo 'eval "$(_ECRESHORE_COMPLETE=bash_source ecreshore)"' >> ~/.bashrc"""

        console.print("[bold cyan]Option 1: Static script (recommended)[/bold cyan]")
        console.print(
            Syntax(script_content, "bash", theme="monokai", line_numbers=False)
        )

        console.print("\n[bold cyan]Option 2: Dynamic loading[/bold cyan]")
        dynamic_content = 'eval "$(_ECRESHORE_COMPLETE=bash_source ecreshore)"'
        console.print(
            Syntax(
                f"# Add this line to ~/.bashrc\n{dynamic_content}",
                "bash",
                theme="monokai",
                line_numbers=False,
            )
        )

    elif shell == "zsh":
        script_content = """# Create completion directory if it doesn't exist
mkdir -p ~/.zsh/completions

# Generate and install completion script
ecreshore completion --shell zsh > ~/.zsh/completions/_ecreshore

# Add completion directory to fpath (add to ~/.zshrc)
echo 'fpath=(~/.zsh/completions $fpath)' >> ~/.zshrc
echo 'autoload -U compinit && compinit' >> ~/.zshrc"""

        console.print("[bold cyan]Option 1: Static script (recommended)[/bold cyan]")
        console.print(
            Syntax(script_content, "bash", theme="monokai", line_numbers=False)
        )

        console.print("\n[bold cyan]Option 2: Dynamic loading[/bold cyan]")
        dynamic_content = 'eval "$(_ECRESHORE_COMPLETE=zsh_source ecreshore)"'
        console.print(
            Syntax(
                f"# Add this line to ~/.zshrc\n{dynamic_content}",
                "bash",
                theme="monokai",
                line_numbers=False,
            )
        )

    elif shell == "fish":
        script_content = """# Create completion directory if it doesn't exist
mkdir -p ~/.config/fish/completions

# Generate and install completion script
ecreshore completion --shell fish > ~/.config/fish/completions/ecreshore.fish

# Reload Fish completions
fish -c "source ~/.config/fish/completions/ecreshore.fish" """

        console.print("[bold cyan]Option 1: Static script (recommended)[/bold cyan]")
        console.print(
            Syntax(script_content, "bash", theme="monokai", line_numbers=False)
        )

        console.print("\n[bold cyan]Option 2: Dynamic loading[/bold cyan]")
        dynamic_content = "ecreshore completion --shell fish | source"
        console.print(
            Syntax(
                f"# Add this line to ~/.config/fish/config.fish\n{dynamic_content}",
                "bash",
                theme="monokai",
                line_numbers=False,
            )
        )

    # Common notes
    notes_panel = Panel(
        "[dim]• Static scripts load faster than dynamic evaluation\n"
        "• Restart your shell or source the configuration file after installation\n"
        "• Tab completion will work for commands, options, and file paths\n"
        "• Use 'ecreshore completion --shell <shell>' to regenerate scripts[/dim]",
        title="[bold]Installation Notes[/bold]",
        border_style="blue",
    )
    console.print(notes_panel)
