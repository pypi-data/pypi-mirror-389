"""Container image inspection command."""

import asyncio
import json
import sys
from dataclasses import asdict
from typing import Optional

import click
from rich.console import Console
from rich.table import Table

from ...services.hybrid_transfer_service import HybridTransferService
from ...services.platform_models import BuildxError
from ..utils.completion import complete_aws_regions

console = Console()


@click.command()
@click.argument("image_ref")
@click.option(
    "--region",
    shell_complete=complete_aws_regions,
    help="AWS region for ECR registry (also respects AWS_DEFAULT_REGION, AWS_REGION, ~/.aws/config)",
)
@click.option("--registry-id", help="AWS account ID for ECR registry")
@click.option(
    "--format",
    type=click.Choice(["table", "json", "platforms"]),
    default="table",
    help="Output format",
)
@click.pass_context
def inspect(
    ctx, image_ref: str, region: Optional[str], registry_id: Optional[str], format: str
):
    """Inspect container image architecture information.

    IMAGE_REF: Image reference in format repository:tag (e.g., nginx:latest)

    Examples:
      # Show platform table
      ecreshore inspect nginx:latest

      # Show as JSON
      ecreshore inspect nginx:latest --format json

      # Show platforms only
      ecreshore inspect nginx:latest --format platforms
    """
    try:
        # Parse image reference
        if ":" in image_ref:
            repository, tag = image_ref.rsplit(":", 1)
        else:
            repository, tag = image_ref, "latest"

        async def _async_inspect():
            service = HybridTransferService(region_name=region, registry_id=registry_id)
            return await service.inspect_image_platforms(repository, tag)

        result = asyncio.run(_async_inspect())

        if not result:
            console.print(
                "[yellow]Unable to inspect image platforms - buildx not available[/yellow]"
            )
            sys.exit(1)

        if format == "table":
            _display_platform_table(result)
        elif format == "json":
            console.print(json.dumps(asdict(result), indent=2, default=str))
        else:  # platforms
            for platform in result.platforms:
                console.print(str(platform))

    except BuildxError as e:
        console.print(f"[bold red]Inspection failed:[/bold red] {e}")
        sys.exit(1)
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        sys.exit(1)


def _display_platform_table(platform_info):
    """Display platform information in table format."""
    table = Table(
        title=f"Image: {platform_info.repository}:{platform_info.tag}",
        show_header=True,
        header_style="bold blue",
    )
    table.add_column("OS", style="cyan")
    table.add_column("Architecture", style="green")
    table.add_column("Variant", style="yellow")

    for platform in platform_info.platforms:
        table.add_row(platform.os, platform.architecture, platform.variant or "-")

    console.print(table)

    if platform_info.is_multiarch:
        console.print(
            f"\n[green]Multi-architecture image with {len(platform_info.platforms)} platforms[/green]"
        )
    else:
        console.print("\n[yellow]Single-architecture image[/yellow]")
