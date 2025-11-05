"""ECR repository purge command."""

import sys
from dataclasses import dataclass
from typing import Optional

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from ...ecr_auth import ECRAuthenticationError
from ...services.progress_reporter import ProgressReporter
from ..utils.completion import complete_aws_regions

console = Console()


@dataclass
class PurgeOptions:
    """Validated purge operation parameters."""

    repository_name: Optional[str]
    all_repositories: bool
    region: Optional[str]
    registry_id: Optional[str]
    name_filter: Optional[str]
    exclude_repositories: set[str]
    keep_latest: bool
    dry_run: bool


@dataclass
class ImageRowData:
    """Formatted data for displaying an image in a table row.

    Pure data structure extracted from ECRImage formatting logic.
    """

    tags_str: str
    digest_short: str
    pushed_str: str
    size_mb: str


def _display_purge_preview(result, progress_reporter, keep_latest):
    """Display purge preview results in a comprehensive table format."""
    # Filter repositories that have actionable images
    displayable_results = [
        purge_result
        for purge_result in result.success_results + result.failed_results
        if _should_display_repository(purge_result)
    ]

    if not displayable_results:
        progress_reporter.info("No images found to purge")
        return

    # Update messaging based on displayable repositories
    if len(displayable_results) == 1:
        repo_name = displayable_results[0].repository_name
        progress_reporter.success(f"Found repository with images to purge: {repo_name}")
    else:
        progress_reporter.success(
            f"Found {len(displayable_results)} repositories with images to purge"
        )

    console.print()

    # Create main purge table
    table = Table(
        title="[bold cyan]🗑️  ECR Purge Preview[/bold cyan]",
        show_header=True,
        header_style="bold white",
        border_style="cyan",
        title_justify="center",
    )

    table.add_column("Repository", style="bright_cyan", max_width=18)
    table.add_column("Image Tags", style="bright_white", max_width=20)
    table.add_column("Digest", style="bright_black", max_width=12)
    table.add_column("Pushed", style="bright_yellow", max_width=12)
    table.add_column("Size", style="bright_magenta", justify="right", max_width=6)
    table.add_column("Action", justify="center", max_width=8)

    total_delete = 0
    total_keep = 0

    for purge_result in displayable_results:
        repo_name = purge_result.repository_name
        total_delete += purge_result.images_deleted
        total_keep += purge_result.images_kept

        # Add deleted images
        for image in purge_result.deleted_images:
            tags_str = (
                ", ".join(image.image_tags)
                if image.image_tags
                else "[dim italic]<untagged>[/dim italic]"
            )
            digest_short = (
                image.image_digest.split(":")[1][:12]
                if ":" in image.image_digest
                else image.image_digest[:12]
            )
            pushed_str = (
                image.pushed_at.strftime("%m-%d %H:%M")
                if image.pushed_at
                else "unknown"
            )
            size_mb = (
                f"{image.size_bytes / (1024 * 1024):.1f}" if image.size_bytes else "?"
            )

            table.add_row(
                f"[bright_cyan]{repo_name}[/bright_cyan]",
                f"[bright_white]{tags_str}[/bright_white]",
                f"[bright_black]{digest_short}[/bright_black]",
                f"[bright_yellow]{pushed_str}[/bright_yellow]",
                f"[bright_magenta]{size_mb}[/bright_magenta]",
                "[bold red]DELETE[/bold red]",
            )

        # Add kept images
        for image in purge_result.kept_images:
            tags_str = (
                ", ".join(image.image_tags)
                if image.image_tags
                else "[dim italic]<untagged>[/dim italic]"
            )
            digest_short = (
                image.image_digest.split(":")[1][:12]
                if ":" in image.image_digest
                else image.image_digest[:12]
            )
            pushed_str = (
                image.pushed_at.strftime("%m-%d %H:%M")
                if image.pushed_at
                else "unknown"
            )
            size_mb = (
                f"{image.size_bytes / (1024 * 1024):.1f}" if image.size_bytes else "?"
            )

            table.add_row(
                f"[bright_cyan]{repo_name}[/bright_cyan]",
                f"[bright_white]{tags_str}[/bright_white]",
                f"[bright_black]{digest_short}[/bright_black]",
                f"[bright_yellow]{pushed_str}[/bright_yellow]",
                f"[bright_magenta]{size_mb}[/bright_magenta]",
                "[bold green]KEEP[/bold green]",
            )

    console.print(table)
    console.print()

    # Summary information displayed directly
    if keep_latest and total_keep > 0:
        console.print(f"[bold red]Images to delete: {total_delete}[/bold red]")
        console.print(f"[bold green]Images to keep: {total_keep}[/bold green]")
    else:
        console.print(f"[bold red]Images to delete: {total_delete}[/bold red]")

    console.print()
    console.print("[yellow]⚠️  This is a DRY RUN - no images were deleted[/yellow]")
    console.print("[dim]Remove --dry-run to execute the purge operation[/dim]")


def _format_image_row_data(image) -> ImageRowData:
    """Format ECRImage data for table display - pure function.

    Extracts and formats image metadata into displayable strings.
    No Rich dependencies - pure data transformation.

    Args:
        image: ECRImage instance with metadata

    Returns:
        ImageRowData with formatted strings for display
    """
    tags_str = (
        ", ".join(image.image_tags)
        if image.image_tags
        else "[dim italic]<untagged>[/dim italic]"
    )

    digest_short = (
        image.image_digest.split(":")[1][:12]
        if ":" in image.image_digest
        else image.image_digest[:12]
    )

    pushed_str = (
        image.pushed_at.strftime("%m-%d %H:%M")
        if image.pushed_at
        else "unknown"
    )

    size_mb = (
        f"{image.size_bytes / (1024 * 1024):.1f}" if image.size_bytes else "?"
    )

    return ImageRowData(
        tags_str=tags_str,
        digest_short=digest_short,
        pushed_str=pushed_str,
        size_mb=size_mb
    )


def _build_purge_summary_lines(result, displayable_count: int) -> list[str]:
    """Build summary text lines for purge results - pure function.

    Args:
        result: PurgeSummary with operation results
        displayable_count: Number of repositories with actionable results

    Returns:
        List of formatted summary strings
    """
    summary_lines = []

    if result.overall_success:
        summary_lines.append(
            "[bold green]✅ Purge completed successfully![/bold green]"
        )
        summary_lines.append(f"Images deleted: {result.total_images_deleted}")
        if result.total_images_kept > 0:
            summary_lines.append(f"Images kept: {result.total_images_kept}")
        summary_lines.append(f"Repositories processed: {displayable_count}")
    else:
        summary_lines.append("[bold yellow]⚠️  Purge partially completed[/bold yellow]")
        summary_lines.append(f"Images deleted: {result.total_images_deleted}")
        if result.total_images_failed > 0:
            summary_lines.append(f"Images failed: {result.total_images_failed}")
        if result.total_images_kept > 0:
            summary_lines.append(f"Images kept: {result.total_images_kept}")
        if result.repositories_failed > 0:
            summary_lines.append(f"Repositories failed: {result.repositories_failed}")
        summary_lines.append(f"Repositories processed: {displayable_count}")

    return summary_lines


def _should_display_repository(purge_result):
    """Determine if a repository should be displayed in output.

    A repository should be shown if it has:
    - Images to delete, OR
    - Images to keep (when using keep_latest), OR
    - Failed images, OR
    - An error message
    """
    return (
        len(purge_result.deleted_images) > 0
        or len(purge_result.kept_images) > 0
        or len(purge_result.failed_images) > 0
        or purge_result.error_message is not None
    )


def _display_purge_summary(result, progress_reporter, keep_latest):
    """Display purge operation summary before confirmation in table format."""
    # Filter repositories that have actionable images
    displayable_results = [
        purge_result
        for purge_result in result.success_results + result.failed_results
        if _should_display_repository(purge_result)
    ]

    if not displayable_results:
        console.print("\n[dim]No images to purge[/dim]")
        return

    console.print()

    # Create main purge table
    table = Table(
        title="[bold yellow]⚠️  ECR Purge Summary[/bold yellow]",
        show_header=True,
        header_style="bold white",
        border_style="yellow",
        title_justify="center",
    )

    table.add_column("Repository", style="bright_cyan", max_width=18)
    table.add_column("Image Tags", style="bright_white", max_width=20)
    table.add_column("Digest", style="bright_black", max_width=12)
    table.add_column("Pushed", style="bright_yellow", max_width=12)
    table.add_column("Size", style="bright_magenta", justify="right", max_width=6)
    table.add_column("Action", justify="center", max_width=8)

    total_delete = 0
    total_keep = 0

    for purge_result in displayable_results:
        repo_name = purge_result.repository_name
        total_delete += purge_result.images_deleted
        total_keep += purge_result.images_kept

        # Add deleted images
        for image in purge_result.deleted_images:
            tags_str = (
                ", ".join(image.image_tags)
                if image.image_tags
                else "[dim italic]<untagged>[/dim italic]"
            )
            digest_short = (
                image.image_digest.split(":")[1][:12]
                if ":" in image.image_digest
                else image.image_digest[:12]
            )
            pushed_str = (
                image.pushed_at.strftime("%m-%d %H:%M")
                if image.pushed_at
                else "unknown"
            )
            size_mb = (
                f"{image.size_bytes / (1024 * 1024):.1f}" if image.size_bytes else "?"
            )

            table.add_row(
                f"[bright_cyan]{repo_name}[/bright_cyan]",
                f"[bright_white]{tags_str}[/bright_white]",
                f"[bright_black]{digest_short}[/bright_black]",
                f"[bright_yellow]{pushed_str}[/bright_yellow]",
                f"[bright_magenta]{size_mb}[/bright_magenta]",
                "[bold red]DELETE[/bold red]",
            )

        # Add kept images
        for image in purge_result.kept_images:
            tags_str = (
                ", ".join(image.image_tags)
                if image.image_tags
                else "[dim italic]<untagged>[/dim italic]"
            )
            digest_short = (
                image.image_digest.split(":")[1][:12]
                if ":" in image.image_digest
                else image.image_digest[:12]
            )
            pushed_str = (
                image.pushed_at.strftime("%m-%d %H:%M")
                if image.pushed_at
                else "unknown"
            )
            size_mb = (
                f"{image.size_bytes / (1024 * 1024):.1f}" if image.size_bytes else "?"
            )

            table.add_row(
                f"[bright_cyan]{repo_name}[/bright_cyan]",
                f"[bright_white]{tags_str}[/bright_white]",
                f"[bright_black]{digest_short}[/bright_black]",
                f"[bright_yellow]{pushed_str}[/bright_yellow]",
                f"[bright_magenta]{size_mb}[/bright_magenta]",
                "[bold green]KEEP[/bold green]",
            )

    console.print(table)
    console.print()

    # Summary panel
    summary_lines = []
    if keep_latest and total_keep > 0:
        summary_lines.append(f"[bold red]Images to delete: {total_delete}[/bold red]")
        summary_lines.append(f"[bold green]Images to keep: {total_keep}[/bold green]")
    else:
        summary_lines.append(f"[bold red]Images to delete: {total_delete}[/bold red]")

    if keep_latest:
        summary_lines.append("")
        summary_lines.append(
            "[dim]The most recent image in each repository will be preserved[/dim]"
        )

    summary_panel = Panel(
        "\n".join(summary_lines),
        title="[bold]Operation Summary[/bold]",
        border_style="yellow",
        padding=(1, 2),
    )
    console.print(summary_panel)


def _display_purge_results(result, progress_reporter, verbose):
    """Display final purge operation results in table format."""
    console.print()

    # Filter repositories that have actionable results
    displayable_results = [
        purge_result
        for purge_result in result.success_results + result.failed_results
        if _should_display_repository(purge_result)
    ]

    if not displayable_results:
        progress_reporter.info("No operations were performed")
        return

    # Create results table
    table = Table(
        title="[bold green]✅ ECR Purge Results[/bold green]",
        show_header=True,
        header_style="bold white",
        border_style="green" if result.overall_success else "red",
        title_justify="center",
    )

    table.add_column("Repository", style="cyan", min_width=20)
    table.add_column("Image Tags", style="white", min_width=25)
    table.add_column("Digest", style="dim", max_width=15)
    table.add_column("Pushed", style="dim", min_width=12)
    table.add_column("Size (MB)", style="dim", justify="right", min_width=8)
    table.add_column("Result", justify="center", min_width=10)

    for purge_result in displayable_results:
        repo_name = purge_result.repository_name

        # Add successfully deleted images
        for image in purge_result.deleted_images:
            row_data = _format_image_row_data(image)
            table.add_row(
                f"[bright_cyan]{repo_name}[/bright_cyan]",
                f"[bright_white]{row_data.tags_str}[/bright_white]",
                f"[bright_black]{row_data.digest_short}[/bright_black]",
                f"[bright_yellow]{row_data.pushed_str}[/bright_yellow]",
                f"[bright_magenta]{row_data.size_mb}[/bright_magenta]",
                "[bold green]DELETED[/bold green]",
            )

        # Add kept images
        for image in purge_result.kept_images:
            row_data = _format_image_row_data(image)
            table.add_row(
                f"[bright_cyan]{repo_name}[/bright_cyan]",
                f"[bright_white]{row_data.tags_str}[/bright_white]",
                f"[bright_black]{row_data.digest_short}[/bright_black]",
                f"[bright_yellow]{row_data.pushed_str}[/bright_yellow]",
                f"[bright_magenta]{row_data.size_mb}[/bright_magenta]",
                "[bold cyan]KEPT[/bold cyan]",
            )

        # Add failed images
        for image in purge_result.failed_images:
            row_data = _format_image_row_data(image)
            table.add_row(
                f"[bright_cyan]{repo_name}[/bright_cyan]",
                f"[bright_white]{row_data.tags_str}[/bright_white]",
                f"[bright_black]{row_data.digest_short}[/bright_black]",
                f"[bright_yellow]{row_data.pushed_str}[/bright_yellow]",
                f"[bright_magenta]{row_data.size_mb}[/bright_magenta]",
                "[bold red]FAILED[/bold red]",
            )

    console.print(table)
    console.print()

    # Build and display results summary panel
    summary_lines = _build_purge_summary_lines(result, len(displayable_results))
    panel_style = "green" if result.overall_success else "yellow"
    results_panel = Panel(
        "\n".join(summary_lines),
        title="[bold]Final Results[/bold]",
        border_style=panel_style,
        padding=(1, 2),
    )
    console.print(results_panel)

    # Show error details for repositories that failed completely
    error_results = [
        failed
        for failed in result.failed_results
        if failed.error_message and not _should_display_repository(failed)
    ]

    if error_results:
        console.print()
        console.print("[bold red]Repository Errors:[/bold red]")
        for failed in error_results:
            console.print(
                f"  [red]{failed.repository_name}[/red]: {failed.error_message}"
            )


def _validate_purge_options(
    repository_name: Optional[str],
    all_repositories: bool,
    name_filter: Optional[str],
    exclude: tuple[str, ...],
    region: Optional[str],
    registry_id: Optional[str],
    keep_latest: bool,
    dry_run: bool,
) -> PurgeOptions:
    """Validate purge options and return structured config.

    Args:
        repository_name: Specific repository to purge
        all_repositories: Purge all repositories
        name_filter: Filter pattern for repository names
        exclude: Repositories to exclude
        region: AWS region
        registry_id: AWS registry ID
        keep_latest: Keep the latest image
        dry_run: Preview mode

    Returns:
        PurgeOptions with validated parameters

    Raises:
        ValueError: If validation fails
    """
    # Must specify either repo name or --all
    if not repository_name and not all_repositories:
        raise ValueError("Must specify either a repository name or -A/--all")

    # Can't specify both
    if repository_name and all_repositories:
        raise ValueError("Cannot specify both repository name and -A/--all")

    # Filter/exclude only valid with --all
    if repository_name and (name_filter or exclude):
        raise ValueError("--filter and --exclude can only be used with -A/--all")

    return PurgeOptions(
        repository_name=repository_name,
        all_repositories=all_repositories,
        region=region,
        registry_id=registry_id,
        name_filter=name_filter,
        exclude_repositories=set(exclude) if exclude else set(),
        keep_latest=keep_latest,
        dry_run=dry_run,
    )


def _execute_dry_run(service, options: PurgeOptions, reporter) -> None:
    """Execute dry run and display preview.

    Args:
        service: ECRPurgeService instance
        options: Validated purge options
        reporter: ProgressReporter instance
    """
    reporter.info("Getting purge preview...")

    result = service.purge(
        repository_name=options.repository_name,
        all_repositories=options.all_repositories,
        keep_latest=options.keep_latest,
        dry_run=True,
        name_filter=options.name_filter,
        exclude_repositories=options.exclude_repositories,
    )

    if result.repositories_processed == 0:
        reporter.info("No repositories found to purge")
        return

    _display_purge_preview(result, reporter, options.keep_latest)


def _execute_with_confirmation(service, options: PurgeOptions, reporter) -> None:
    """Execute purge with user confirmation.

    Args:
        service: ECRPurgeService instance
        options: Validated purge options
        reporter: ProgressReporter instance
    """
    # Get preview first
    preview = service.purge(
        repository_name=options.repository_name,
        all_repositories=options.all_repositories,
        keep_latest=options.keep_latest,
        dry_run=True,
        name_filter=options.name_filter,
        exclude_repositories=options.exclude_repositories,
    )

    if preview.repositories_processed == 0:
        reporter.info("No repositories found to purge")
        return

    # Show preview and get confirmation
    _display_purge_summary(preview, reporter, options.keep_latest)

    # Request confirmation
    console.print()
    console.print("[bold red]WARNING: This is a DESTRUCTIVE operation![/bold red]")

    if options.repository_name:
        console.print(
            f"This will permanently delete images from repository: [cyan]{options.repository_name}[/cyan]"
        )
    else:
        # Count repositories that actually have actionable images
        actionable_repos = [
            purge_result
            for purge_result in preview.success_results + preview.failed_results
            if _should_display_repository(purge_result)
        ]
        console.print(
            f"This will permanently delete images from [cyan]{len(actionable_repos)}[/cyan] repositories"
        )

    if options.keep_latest:
        console.print(
            "[green]The most recent image in each repository will be preserved.[/green]"
        )

    console.print()

    # Ask for explicit confirmation
    if not click.confirm("Do you want to proceed with this destructive operation?"):
        reporter.info("Purge cancelled by user")
        return

    console.print()
    console.print("[red]Starting purge operation...[/red]")

    # Execute actual purge
    with reporter.status("Purging repositories..."):
        result = service.purge(
            repository_name=options.repository_name,
            all_repositories=options.all_repositories,
            keep_latest=options.keep_latest,
            dry_run=False,
            name_filter=options.name_filter,
            exclude_repositories=options.exclude_repositories,
        )

    # Report final results
    _display_purge_results(result, reporter, reporter.verbose)


@click.command()
@click.argument("repository_name", required=False)
@click.option("-A", "--all", is_flag=True, help="Purge all repositories")
@click.option(
    "--region",
    shell_complete=complete_aws_regions,
    help="AWS region for ECR registry (also respects AWS_DEFAULT_REGION, AWS_REGION, ~/.aws/config)",
)
@click.option("--registry-id", help="AWS account ID for ECR registry")
@click.option("--filter", help="Filter repositories by name pattern (only with --all)")
@click.option(
    "--exclude",
    multiple=True,
    help="Exclude specific repository names (only with --all)",
)
@click.option(
    "--keep-latest",
    is_flag=True,
    help="Keep the most recently pushed image in each repository",
)
@click.option(
    "--dry-run", is_flag=True, help="Preview what would be deleted without executing"
)
@click.pass_context
def purge(
    ctx,
    repository_name: Optional[str],
    all: bool,
    region: Optional[str],
    registry_id: Optional[str],
    filter: Optional[str],
    exclude: tuple[str, ...],
    keep_latest: bool,
    dry_run: bool,
):
    """Purge images from ECR repositories.

    Either specify a REPOSITORY_NAME to purge a specific repository,
    or use -A/--all to purge all repositories.

    WARNING: This is a DESTRUCTIVE operation that will permanently delete
    container images from ECR repositories.

    Use --dry-run first to preview what would be deleted.
    Use --keep-latest to preserve the most recently pushed image in each repository.

    \\b
    Examples:
      # Preview deletion for a specific repository
      ecreshore purge my-repo --dry-run

      # Purge specific repository, keeping latest image
      ecreshore purge my-repo --keep-latest

      # Preview deletion for all repositories
      ecreshore purge -A --dry-run

      # Purge repositories matching pattern, keeping latest
      ecreshore purge -A --filter my-app --keep-latest

      # Purge all repositories except excluded ones
      ecreshore purge -A --exclude important-repo
    """
    verbose = ctx.obj.get("verbose", False)
    progress_reporter = ProgressReporter(console=console, verbose=bool(verbose))

    # 1. Validate and build options
    try:
        options = _validate_purge_options(
            repository_name=repository_name,
            all_repositories=all,
            name_filter=filter,
            exclude=exclude,
            region=region,
            registry_id=registry_id,
            keep_latest=keep_latest,
            dry_run=dry_run,
        )
    except ValueError as e:
        progress_reporter.error(str(e))
        console.print("\nExamples:")
        console.print("  ecreshore purge my-repo --dry-run")
        console.print("  ecreshore purge -A --dry-run")
        sys.exit(1)

    # 2. Execute purge operation
    try:
        from ...services.purge_service import ECRPurgeService

        purge_service = ECRPurgeService(
            region_name=options.region, registry_id=options.registry_id
        )

        if options.dry_run:
            _execute_dry_run(purge_service, options, progress_reporter)
        else:
            _execute_with_confirmation(purge_service, options, progress_reporter)

    except ECRAuthenticationError as e:
        progress_reporter.error(str(e))
        sys.exit(1)
    except KeyboardInterrupt:
        progress_reporter.warning("Purge cancelled by user")
        sys.exit(1)
    except Exception as e:
        progress_reporter.error(f"Purge failed: {e}")
        if verbose:
            import traceback

            console.print(traceback.format_exc())
        sys.exit(1)
