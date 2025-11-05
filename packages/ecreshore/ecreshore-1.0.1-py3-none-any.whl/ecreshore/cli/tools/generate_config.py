"""Generate example batch configuration file command."""

import sys

import click
from rich.console import Console

from ...services.batch_config import BatchConfigService

console = Console()


@click.command()
@click.argument("output_file", default="batch-config.yml")
def generate_config(output_file: str):
    """Generate example batch configuration file.

    OUTPUT_FILE: Output file path (default: batch-config.yml)
    """
    try:
        example_config = BatchConfigService.generate_example_config()

        with open(output_file, "w", encoding="utf-8") as f:
            f.write(example_config)

        console.print(f"[green]Generated example configuration:[/green] {output_file}")
        console.print(
            f"Edit this file and run: [bold]ecreshore batch {output_file}[/bold]"
        )

    except OSError as e:
        console.print(f"[bold red]Error writing file:[/bold red] {e}")
        sys.exit(1)
