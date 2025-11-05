"""Kubernetes cluster scanning command."""

import sys

import click
from rich.console import Console

from ...services.progress_reporter import ProgressReporter
from .scan_helpers import (
    _initialize_cluster_scanner,
    _validate_and_prepare_scan_params,
    _perform_cluster_scan,
    _adjust_output_format_for_export,
)
from .scan_formatters import _handle_scan_output

stderr_console = Console(stderr=True)


@click.command()
@click.option("-n", "--namespace", multiple=True, help="Scan specific namespaces")
@click.option("-N", "--exclude-namespace", multiple=True, help="Exclude namespaces")
@click.option(
    "-A",
    "--all-namespaces",
    is_flag=True,
    help="Scan all namespaces (overrides default exclusions)",
)
@click.option(
    "--target-registry",
    help="Target ECR registry for batch config generation (auto-detected if not provided)",
)
@click.option(
    "--output",
    type=click.Choice(["report", "batch-config", "yaml", "json"]),
    default="report",
    help="Output format",
)
@click.option("--export", help="Export results to file")
@click.pass_context
def scan(
    ctx, namespace, exclude_namespace, all_namespaces, target_registry, output, export
):
    """Scan Kubernetes cluster for non-ECR container images.

    This command scans all workload objects (Deployments, DaemonSets, StatefulSets,
    Jobs, CronJobs, and standalone Pods) to identify container images that are not
    hosted in AWS ECR registries (private or public ECR).

    When using --export without specifying --output, the scan results will be exported
    as a batch-config format, ready for use with 'ecreshore batch'.
    """
    verbose = ctx.obj.get("verbose", False)
    progress_reporter = ProgressReporter(console=stderr_console, verbose=verbose)

    try:
        # Initialize scanner and validate arguments
        scanner = _initialize_cluster_scanner(progress_reporter)
        scan_params = _validate_and_prepare_scan_params(
            namespace, exclude_namespace, all_namespaces, progress_reporter
        )

        # Perform cluster scan
        scan_result = _perform_cluster_scan(scanner, scan_params, progress_reporter)

        # Handle output format adjustment for export
        adjusted_output = _adjust_output_format_for_export(
            output, export, progress_reporter
        )

        # Generate and display/export results
        _handle_scan_output(
            scan_result,
            adjusted_output,
            target_registry,
            export,
            progress_reporter,
            verbose,
        )

    except KeyboardInterrupt:
        progress_reporter.warning("Cluster scan cancelled by user")
        sys.exit(1)
    except Exception as e:
        progress_reporter.error(f"Cluster scan failed: {e}")
        if verbose:
            import traceback
            from rich.console import Console

            console = Console()
            console.print(traceback.format_exc())
        sys.exit(1)
