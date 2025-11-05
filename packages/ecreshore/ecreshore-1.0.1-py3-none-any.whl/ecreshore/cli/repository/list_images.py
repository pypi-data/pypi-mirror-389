"""List ECR repository images command."""

import asyncio
import sys
from typing import Optional

import click
from rich.console import Console
from rich.table import Table

from ...ecr_auth import ECRAuthenticationError
from ...services.progress_reporter import ProgressReporter
from ..utils.completion import complete_aws_regions, complete_ecr_repositories

console = Console()


def _filter_digest_images(images: list, show_digests: bool) -> tuple[list, int]:
    """Filter out digest-tagged images unless explicitly requested.

    PURE FUNCTION: No I/O, easily testable.

    Args:
        images: List of image objects
        show_digests: Whether to include SHA256-tagged digest entries

    Returns:
        Tuple of (filtered_images, digest_count)
    """
    if show_digests:
        return images, 0

    tagged_images = [img for img in images if not img.is_digest_tag]
    digest_count = len(images) - len(tagged_images)
    return tagged_images, digest_count


async def _load_images(
    ecr_service,
    repository_name: str,
    tag_filter: Optional[str],
    max_results: int,
    brief: bool,
    progress_reporter,
):
    """Load images from ECR repository with optional architecture detection.

    SERVICE LAYER: Testable with mocked ECR service.

    Args:
        ecr_service: ECR repository service instance
        repository_name: Name of the repository
        tag_filter: Optional tag pattern to filter images
        max_results: Maximum number of images to retrieve
        brief: If True, skip architecture detection
        progress_reporter: Progress reporter for user feedback

    Returns:
        List of image objects
    """
    progress_reporter.info(f"Loading images from repository '{repository_name}'...")

    if not brief:
        progress_reporter.info("Detecting image architectures...")
        images = await ecr_service.list_images_with_architectures(
            repository_name, tag_filter=tag_filter, max_results=max_results
        )
    else:
        images = ecr_service.list_images(
            repository_name, tag_filter=tag_filter, max_results=max_results
        )

    return images


def _display_image_summary(
    images: list,
    digest_count: int,
    show_digests: bool,
    progress_reporter,
    verbose: bool,
) -> None:
    """Display summary of loaded images with digest information.

    DISPLAY HELPER: Testable with mocked progress reporter.

    Args:
        images: List of filtered images
        digest_count: Number of digest entries that were filtered out
        show_digests: Whether digest entries were included
        progress_reporter: Progress reporter for user feedback
        verbose: Whether to show verbose hints
    """
    if not show_digests and digest_count > 0:
        progress_reporter.success(
            f"Found {len(images)} tagged images ({digest_count} digest entries hidden)"
        )
        if verbose:
            progress_reporter.info(
                "Use --show-digests to include SHA256-tagged entries"
            )
    else:
        progress_reporter.success(f"Found {len(images)} images")


def _build_images_table(repository_name: str, images: list, brief: bool) -> Table:
    """Build Rich table for displaying images.

    PURE FUNCTION: No I/O, deterministic output.

    Args:
        repository_name: Name of the repository
        images: List of image objects to display
        brief: Whether to use brief display mode (excludes architecture column)

    Returns:
        Configured Rich Table with all image data
    """
    table = Table(
        title=f"Images in {repository_name}",
        show_header=True,
        header_style="bold blue",
    )
    table.add_column("Tag", style="green")
    table.add_column("Digest", style="dim", max_width=20)
    table.add_column("Size", justify="right")
    table.add_column("Pushed", style="dim")

    if not brief:
        table.add_column("Architectures", style="cyan", max_width=40)

    for image in images:
        tag_display = image.primary_tag
        digest_display = (
            image.image_digest.split(":")[1][:12]
            if ":" in image.image_digest
            else image.image_digest[:12]
        )
        size_display = f"{image.size_mb:.0f}MB"
        pushed_display = image.pushed_at.strftime("%Y-%m-%d %H:%M")

        # Show multiple tags if available - cache length to avoid repeated calls
        tag_count = len(image.image_tags)
        if tag_count > 1:
            other_tags = ", ".join(image.image_tags[1:3])  # Show up to 2 more tags
            if tag_count > 3:
                other_tags += f" (+{tag_count - 3} more)"
            tag_display = f"{tag_display}\n[dim]{other_tags}[/dim]"

        if not brief:
            arch_display = image.architectures_detailed
            table.add_row(
                tag_display,
                digest_display,
                size_display,
                pushed_display,
                arch_display,
            )
        else:
            table.add_row(tag_display, digest_display, size_display, pushed_display)

    return table


@click.command()
@click.argument("repository_name", shell_complete=complete_ecr_repositories)
@click.option(
    "--region",
    shell_complete=complete_aws_regions,
    help="AWS region for ECR registry (also respects AWS_DEFAULT_REGION, AWS_REGION, ~/.aws/config)",
)
@click.option("--registry-id", help="AWS account ID for ECR registry")
@click.option("--filter", help="Filter images by tag pattern")
@click.option("--max-results", default=20, help="Maximum images to list")
@click.option(
    "--brief",
    is_flag=True,
    help="Show minimal display without architecture information",
)
@click.option(
    "--show-digests",
    is_flag=True,
    help="Include SHA256-tagged digest entries in output",
)
@click.pass_context
def list_images(
    ctx,
    repository_name: str,
    region: Optional[str],
    registry_id: Optional[str],
    filter: Optional[str],
    max_results: int,
    brief: bool,
    show_digests: bool,
):
    """List images in an ECR repository with detailed architecture information by default.

    REPOSITORY_NAME: ECR repository name

    By default, shows detailed architecture information for all images and hides
    SHA256-tagged digest entries. Use --brief for minimal display without architecture
    detection, or --show-digests to include all manifest entries.

    Examples:
      # Default: detailed architectures for tagged images
      ecreshore list-images my-repo

      # Minimal display without architecture detection
      ecreshore list-images my-repo --brief

      # Include SHA256 digest entries with architectures
      ecreshore list-images my-repo --show-digests

      # Brief display with digest entries
      ecreshore list-images my-repo --brief --show-digests
    """
    verbose = ctx.obj.get("verbose", False)

    async def _async_list_images():
        from ...services.ecr_repository import ECRRepositoryService

        progress_reporter = ProgressReporter(console=console, verbose=bool(verbose))
        ecr_service = ECRRepositoryService(region_name=region, registry_id=registry_id)

        # 1. Load images from ECR (with optional architecture detection)
        images = await _load_images(
            ecr_service,
            repository_name,
            tag_filter=filter,
            max_results=max_results,
            brief=brief,
            progress_reporter=progress_reporter,
        )

        if not images:
            progress_reporter.info("No images found")
            return

        # 2. Filter digest-tagged images unless explicitly requested
        filtered_images, digest_count = _filter_digest_images(images, show_digests)

        # 3. Display summary
        if filtered_images:
            _display_image_summary(
                filtered_images, digest_count, show_digests, progress_reporter, verbose
            )
        else:
            progress_reporter.info(
                "No tagged images found (use --show-digests to show digest entries)"
            )
            return

        console.print()

        # 4. Build and display table
        table = _build_images_table(repository_name, filtered_images, brief)
        console.print(table)

        # 5. Show verbose statistics if requested
        if verbose:
            total_size_gb = sum(i.size_mb for i in filtered_images) / 1024
            console.print(
                f"\nTotal: {len(filtered_images)} images, {total_size_gb:.1f}GB"
            )

    try:
        asyncio.run(_async_list_images())

    except ECRAuthenticationError as e:
        progress_reporter = ProgressReporter(console=console, verbose=bool(verbose))
        progress_reporter.error(str(e))
        sys.exit(1)
    except Exception as e:
        progress_reporter = ProgressReporter(console=console, verbose=bool(verbose))
        progress_reporter.error(f"Failed to list images: {e}")
        sys.exit(1)
