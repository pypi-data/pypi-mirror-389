"""List ECR repositories command."""

import sys
from typing import Optional

import click
from rich.console import Console
from rich.table import Table

from ...ecr_auth import ECRAuthenticationError
from ...services.progress_reporter import ProgressReporter
from ..utils.completion import complete_aws_regions

console = Console()


@click.command()
@click.option(
    "--region",
    shell_complete=complete_aws_regions,
    help="AWS region for ECR registry (also respects AWS_DEFAULT_REGION, AWS_REGION, ~/.aws/config)",
)
@click.option("--registry-id", help="AWS account ID for ECR registry")
@click.option("--filter", help="Filter repositories by name pattern")
@click.option("--max-results", default=50, help="Maximum repositories to list")
@click.pass_context
def list_repositories(
    ctx,
    region: Optional[str],
    registry_id: Optional[str],
    filter: Optional[str],
    max_results: int,
):
    """List ECR repositories in your account."""
    verbose = ctx.obj.get("verbose", False)

    try:
        from ...services.ecr_repository import ECRRepositoryService

        progress_reporter = ProgressReporter(console=console, verbose=bool(verbose))
        ecr_service = ECRRepositoryService(region_name=region, registry_id=registry_id)

        progress_reporter.info("Loading ECR repositories...")
        repositories = ecr_service.list_repositories(
            name_filter=filter, max_results=max_results
        )

        if not repositories:
            progress_reporter.info("No repositories found")
            return

        progress_reporter.success(f"Found {len(repositories)} repositories")
        console.print()

        # Create table
        table = Table(
            title="ECR Repositories", show_header=True, header_style="bold blue"
        )
        table.add_column("Repository", style="cyan", no_wrap=True)
        table.add_column("Images", justify="center")
        table.add_column("Size", justify="right")
        table.add_column("Latest Tag", style="green")
        table.add_column("URI", style="dim")

        for repo in repositories:
            size_display = (
                f"{repo.size_gb:.1f}GB"
                if repo.size_gb >= 1
                else f"{repo.size_mb:.0f}MB"
            )
            latest_tag_display = repo.latest_tag or "-"

            # Use dim color for empty repositories, bright for those with images
            repo_name_display = (
                repo.name if repo.image_count > 0 else f"[dim]{repo.name}[/dim]"
            )

            table.add_row(
                repo_name_display,
                str(repo.image_count),
                size_display,
                latest_tag_display,
                repo.uri,
            )

        console.print(table)

        if verbose:
            total_size_gb = sum(r.size_gb for r in repositories)
            total_images = sum(r.image_count for r in repositories)
            console.print(
                f"\nTotal: {len(repositories)} repositories, {total_images} images, {total_size_gb:.1f}GB"
            )

    except ECRAuthenticationError as e:
        progress_reporter.error(str(e))
        sys.exit(1)
    except Exception as e:
        progress_reporter.error(f"Failed to list repositories: {e}")
        sys.exit(1)
