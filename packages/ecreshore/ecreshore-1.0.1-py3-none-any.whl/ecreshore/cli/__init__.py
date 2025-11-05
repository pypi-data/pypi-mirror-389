"""CLI interface for ecreshore container image copying tool.

This module provides a modular CLI structure that breaks down the large monolithic
cli.py file into manageable, focused modules organized by functionality.
"""

import click

from .. import __version__ as version
from .tools.completion import completion
from .tools.generate_config import generate_config
from .tools.terminal_info import terminal_info
from .repository.list_repositories import list_repositories
from .repository.list_images import list_images
from .repository.purge import purge
from .cluster.scan import scan
from .cluster.inspect import inspect
from .core.auth_test import auth_test
from .core.copy import copy
from .core.batch import batch
from .utils.logging_setup import setup_logging


@click.group()
@click.option(
    "--verbose",
    "-v",
    count=True,
    help="Increase verbosity (-v for INFO, -vv for DEBUG)",
)
@click.version_option(version=version)
@click.pass_context
def cli(ctx, verbose: int):
    """ecreshore - Copy container images between registries with ease.

    This tool simplifies copying container images between different registries,
    with special support for AWS ECR. It handles authentication, multi-architecture
    images, and provides both simple and rich terminal interfaces.

    Examples:
      # Copy a single image to ECR
      ecreshore copy nginx:latest my-repo

      # Process multiple images from a config file
      ecreshore batch images.yml

      # List ECR repositories
      ecreshore list-repositories
    """
    # Store verbose in context for subcommands
    ctx.ensure_object(dict)
    ctx.obj["verbose"] = verbose

    # Configure logging based on output mode
    setup_logging(verbose)


# Add modularized commands
cli.add_command(generate_config, name="generate-config")
cli.add_command(completion)
cli.add_command(terminal_info, name="terminal-info")
cli.add_command(list_repositories, name="list-repositories")
cli.add_command(list_images, name="list-images")
cli.add_command(purge)
cli.add_command(scan)
cli.add_command(inspect)
cli.add_command(auth_test, name="auth-test")
cli.add_command(copy)
cli.add_command(batch)


if __name__ == "__main__":
    cli()
