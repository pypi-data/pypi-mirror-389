"""Helper functions for Kubernetes cluster scanning."""

import sys


def _initialize_cluster_scanner(progress_reporter):
    """Initialize the Kubernetes cluster scanner."""
    from ...services.k8s_scanner import KubernetesClusterScanner

    progress_reporter.info("Initializing Kubernetes cluster scanner...")

    try:
        return KubernetesClusterScanner()
    except RuntimeError as e:
        progress_reporter.error(f"Failed to initialize Kubernetes client: {e}")
        progress_reporter.info(
            "Make sure you have a valid kubeconfig file and cluster access"
        )
        sys.exit(1)


def _validate_and_prepare_scan_params(
    namespace, exclude_namespace, all_namespaces, progress_reporter
):
    """Validate namespace arguments and prepare scan parameters."""
    # Handle namespace options
    if all_namespaces and namespace:
        progress_reporter.error(
            "Cannot use both --all-namespaces and --namespace options together"
        )
        sys.exit(1)

    # Convert to lists for processing
    target_namespaces = list(namespace) if namespace else None
    excluded_namespaces = list(exclude_namespace) if exclude_namespace else None

    # Override exclusions if --all-namespaces is specified
    if all_namespaces:
        excluded_namespaces = []

    return {"namespaces": target_namespaces, "exclude_namespaces": excluded_namespaces}


def _perform_cluster_scan(scanner, scan_params, progress_reporter):
    """Execute the cluster scan operation."""
    progress_reporter.info("Scanning cluster for container images...")
    with progress_reporter.status("Scanning workloads..."):
        return scanner.scan_cluster(**scan_params)


def _adjust_output_format_for_export(output, export, progress_reporter):
    """Adjust output format when export is specified."""
    if export and output == "report":
        progress_reporter.info(
            f"Using batch-config output format for export to {export}"
        )
        return "batch-config"
    return output
