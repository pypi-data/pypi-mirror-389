"""Container image copy command."""

import asyncio
import sys
from typing import Optional

import click
from rich.console import Console

from ...async_docker_client import AsyncDockerClientError
from ...ecr_auth import ECRAuthenticationError
from ...services.hybrid_transfer_service import HybridTransferService
from ...services.platform_models import BuildxError
from ...services.progress_reporter import ProgressReporter
from ...services.transfer_request_builder import TransferRequestBuilder
from ...services.transfer_service import (
    DockerClientError,
    TransferRequest,
    TransferResult,
)
from ...terminal_detection import get_terminal_info, should_use_rich_ui
from ..utils.completion import complete_aws_regions
from ..utils.ui_helpers import determine_ui_mode

console = Console()


async def _async_copy_image_enhanced(
    region: Optional[str],
    registry_id: Optional[str],
    request: TransferRequest,
    verbose: int,
    use_rich_ui: bool = True,
) -> TransferResult:
    """Execute enhanced async image copy operation with multi-arch support.

    Args:
        region: AWS region
        registry_id: AWS registry ID
        request: Transfer request with all parameters
        verbose: Verbose output level
        use_rich_ui: Whether to use rich UI for progress display

    Returns:
        TransferResult with operation result
    """
    # Initialize services
    transfer_service = HybridTransferService(
        region_name=region, registry_id=registry_id
    )

    # Create progress reporter with identical rich UI as batch operations
    from ...services.single_transfer_progress import SingleTransferProgressReporter

    single_progress = SingleTransferProgressReporter(
        console=console,
        verbose=bool(verbose),
        simple_mode=not use_rich_ui,  # Use simple mode when rich UI is disabled
        output_mode="console",
    )

    # Keep base progress reporter for backwards compatibility
    progress_reporter = ProgressReporter(console=console, verbose=bool(verbose))

    # Execute pure business logic
    result_data = await transfer_service.copy_image_enhanced(request)

    # Handle UI based on business logic results
    if not result_data["prerequisites_valid"]:
        progress_reporter.error(result_data["error_message"])
        sys.exit(1)

    progress_reporter.info("Prerequisites validated successfully")
    progress_reporter.info(f"Target ECR registry: {result_data['ecr_registry_url']}")

    # Show multi-arch info if available
    platform_info = result_data["platform_info"]
    if platform_info:
        if use_rich_ui:
            # Rich UI: Show architectures in a nicer format
            progress_reporter.info("[dim]Source image architectures:[/dim]")
            for platform in platform_info.platforms:
                progress_reporter.info(f"  [cyan]•[/cyan] {platform}")
        else:
            # Simple mode: Basic list
            progress_reporter.info(
                f"Source image has {len(platform_info.platforms)} architectures:"
            )
            for platform in platform_info.platforms:
                progress_reporter.info(f"  - {platform}")

    # Start transfer UI with identical rich display as batch
    single_progress.start_transfer(request)

    # Show transfer progress using single transfer progress reporter
    single_progress.update_operation("Transferring image", progress_pct=50)

    # Brief pause to show the progress display (business logic already executed)
    await asyncio.sleep(0.1)

    # Get the transfer result
    result = result_data["transfer_result"]

    # Report results using single transfer progress reporter
    if result.success:
        # Handle skip scenarios
        if result.skipped:
            single_progress.skip_transfer(
                result.skip_reason or "Image already present with matching digest"
            )
        else:
            # Normal transfer completion
            single_progress.complete_transfer(success=True, error_message=None)

            # Show additional info about multi-arch transfers
            if result.platforms_copied:
                if use_rich_ui:
                    # Rich UI: Enhanced multi-arch success display
                    progress_reporter.info(
                        f"[dim]Copied {len(result.platforms_copied)} architectures:[/dim]"
                    )
                    for platform in result.platforms_copied:
                        progress_reporter.info(f"  [green]•[/green] {platform}")
                    # Add blank line below architectures segment in rich mode
                    console.print("")
                else:
                    # Simple mode: Basic multi-arch success
                    progress_reporter.info(
                        f"Copied {len(result.platforms_copied)} architectures:"
                    )
                    for platform in result.platforms_copied:
                        progress_reporter.info(f"  - {platform}")
                    # Add blank line below architectures segment in simple mode too
                    console.print("")
    else:
        # Transfer failed
        single_progress.complete_transfer(
            success=False, error_message=result.error_message
        )

    # Show final summary (identical to batch display)
    single_progress.finish_transfer()

    # Report digest verification results after progress display with separator lines
    if (
        result.success
        and request.verify_digest
        and result.source_digest
        and result.target_digest
    ):
        # Add separator line above
        if use_rich_ui:
            progress_reporter.info("[dim]" + "─" * 60 + "[/dim]")
        else:
            progress_reporter.info("─" * 60)

        progress_reporter.verification_progress(
            result.source_digest, result.target_digest
        )

        # Add separator line below
        if use_rich_ui:
            progress_reporter.info("[dim]" + "─" * 60 + "[/dim]")
        else:
            progress_reporter.info("─" * 60)

    return result


@click.command()
@click.argument("source_image")
@click.argument("target_repository", required=False)
@click.option(
    "--source-tag", default="latest", help="Source image tag (default: latest)"
)
@click.option(
    "--target-tag",
    default=None,
    help="Target image tag (defaults to source tag if not specified)",
)
@click.option(
    "--region",
    shell_complete=complete_aws_regions,
    help="AWS region for ECR registry (also respects AWS_DEFAULT_REGION, AWS_REGION, ~/.aws/config)",
)
@click.option("--registry-id", help="AWS account ID for ECR registry")
@click.option(
    "--verify-digest", is_flag=True, default=True, help="Verify image digest after copy"
)
@click.option(
    "--platforms",
    help="Comma-separated list of platforms (e.g., linux/amd64,linux/arm64)",
)
@click.option(
    "-A",
    "--all-architectures",
    is_flag=True,
    default=False,
    help="Copy all detected architectures (no platform limits)",
)
@click.option(
    "--no-auto-detect",
    is_flag=True,
    default=False,
    help="Disable automatic multi-architecture detection and preservation",
)
@click.option(
    "--force",
    is_flag=True,
    default=False,
    help="Force transfer even if target image already exists with matching content",
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
@click.pass_context
def copy(
    ctx,
    source_image: str,
    target_repository: Optional[str],
    source_tag: str,
    target_tag: Optional[str],
    region: Optional[str],
    registry_id: Optional[str],
    verify_digest: bool,
    platforms: Optional[str],
    all_architectures: bool,
    no_auto_detect: bool,
    force: bool,
    simple: bool,
    rich: bool,
):
    """Copy a container image to ECR registry with smart multi-architecture handling.

    SOURCE_IMAGE: Source image repository (e.g. nginx:latest, myregistry.com/app:v1.0)
    TARGET_REPOSITORY: Optional target ECR repository name (defaults to last path component of source)

    By default, ecreshore automatically detects multi-architecture images and preserves
    all architectures when Docker Buildx is available. Use --no-auto-detect to disable
    this smart behavior and only copy the current platform's architecture.

    Skip-if-present is enabled by default - if the target image already exists with
    matching content, the transfer will be skipped. Use --force to override this behavior.

    ECReshore automatically detects your terminal capabilities and chooses
    the best UI mode. Use --simple or --rich to override auto-detection.

    Examples:
      # New simplified syntax with automatic repository inference
      ecreshore copy ghcr.io/fluxcd/helm-controller:v1.3.0

      # Original explicit syntax still supported
      ecreshore copy nginx my-nginx-repo

      # Copy specific tag with inferred repository
      ecreshore copy nginx:1.21

      # Copy all detected architectures with tag in URL
      ecreshore copy nginx:latest -A

      # Copy specific architectures with custom target repository
      ecreshore copy nginx:alpine custom-nginx --platforms linux/amd64,linux/arm64

      # Force single-arch copy (disable auto-detection)
      ecreshore copy nginx:latest --no-auto-detect

      # Copy with custom target tag (original tag syntax)
      ecreshore copy nginx my-nginx-repo --source-tag 1.21 --target-tag stable

      # Copy from private registry with all architectures
      ecreshore copy myregistry.com/app:v2.0 -A

      # Force transfer even if target image already exists
      ecreshore copy ghcr.io/fluxcd/helm-controller:v1.3.0 --force

      # Force simple progress display (no rich UI)
      ecreshore copy nginx:latest --simple

      # Force rich UI progress display
      ecreshore copy nginx:latest --rich
    """
    verbose = ctx.obj.get("verbose", False)

    # Validate conflicting platform options
    if all_architectures and platforms:
        progress_reporter = ProgressReporter(console=console, verbose=bool(verbose))
        progress_reporter.error(
            "Cannot use both --platforms and -A/--all-architectures flags together"
        )
        sys.exit(1)

    # Handle conflicting flags
    if simple and rich:
        progress_reporter = ProgressReporter(console=console, verbose=bool(verbose))
        progress_reporter.error("Cannot use both --simple and --rich flags")
        sys.exit(1)

    # Determine UI mode
    use_rich_ui = determine_ui_mode(simple, rich, "console", verbose)

    # Validate conflicting tag specification methods
    from ...services.image_parser import (
        infer_target_repository_name,
        parse_image_with_tag,
        resolve_final_source_tag,
        validate_image_tag_conflict,
    )

    tag_conflict_error = validate_image_tag_conflict(source_image, source_tag)
    if tag_conflict_error:
        progress_reporter = ProgressReporter(console=console, verbose=bool(verbose))
        progress_reporter.error(tag_conflict_error)
        sys.exit(1)

    # Parse image URL and resolve final parameters
    source_image_without_tag, _url_tag = parse_image_with_tag(source_image)
    final_source_tag = resolve_final_source_tag(source_image, source_tag)

    # Default target_tag to resolved source_tag if not specified
    if target_tag is None:
        target_tag = final_source_tag

    # Infer target repository if not provided
    final_target_repository = target_repository
    if not target_repository:
        final_target_repository = infer_target_repository_name(source_image_without_tag)

    # Build enhanced transfer request using builder pattern
    request = TransferRequestBuilder.for_cli_copy(
        source_image=source_image_without_tag,
        target_repository=final_target_repository,
        source_tag=final_source_tag,
        target_tag=target_tag,
        verify_digest=verify_digest,
        platforms=platforms,
        all_architectures=all_architectures,
        no_auto_detect=no_auto_detect,
        force=force,
    )

    try:
        # Execute enhanced async transfer
        result = asyncio.run(
            _async_copy_image_enhanced(
                region, registry_id, request, verbose, use_rich_ui
            )
        )

        # Report results handled in async function
        if not result.success:
            sys.exit(1)

    except (
        DockerClientError,
        AsyncDockerClientError,
        ECRAuthenticationError,
        BuildxError,
    ) as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        if "progress_reporter" in locals():
            progress_reporter.warning("Operation cancelled by user")
        else:
            console.print("\n[yellow]Operation cancelled[/yellow]")
        sys.exit(1)
