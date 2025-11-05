"""ECR authentication test command."""

import asyncio
import sys
from typing import Optional

import click
from rich.console import Console

from ...async_docker_client import AsyncDockerClientError
from ...ecr_auth import ECRAuthenticationError
from ...services.async_transfer_service import AsyncTransferService
from ...services.progress_reporter import ProgressReporter
from ...services.transfer_service import DockerClientError
from ..utils.completion import complete_aws_regions

console = Console()


async def _async_auth_test(
    region: Optional[str],
    registry_id: Optional[str],
    verbose: int,
) -> bool:
    """Execute async ECR authentication test.

    Args:
        region: AWS region
        registry_id: AWS registry ID
        verbose: Verbose output level

    Returns:
        True if authentication successful
    """
    # Initialize async service
    transfer_service = AsyncTransferService(region_name=region, registry_id=registry_id)
    progress_reporter = ProgressReporter(console=console, verbose=bool(verbose))

    # Test authentication
    if not transfer_service.validate_prerequisites():
        progress_reporter.error("ECR authentication failed")
        return False

    progress_reporter.success("ECR authentication successful!")
    progress_reporter.info(f"Registry URL: {transfer_service.get_ecr_registry_url()}")
    return True


@click.command()
@click.option(
    "--region",
    shell_complete=complete_aws_regions,
    help="AWS region for ECR registry (also respects AWS_DEFAULT_REGION, AWS_REGION, ~/.aws/config)",
)
@click.option("--registry-id", help="AWS account ID for ECR registry")
@click.pass_context
def auth_test(ctx, region: Optional[str], registry_id: Optional[str]):
    """Test AWS ECR authentication."""
    verbose = ctx.obj.get("verbose", False)

    try:
        # Execute async authentication test
        result = asyncio.run(_async_auth_test(region, registry_id, verbose))
        if not result:
            sys.exit(1)

    except (DockerClientError, AsyncDockerClientError, ECRAuthenticationError) as e:
        console.print(f"[bold red]Authentication error:[/bold red] {e}")
        sys.exit(1)
