"""Output formatting functions for cluster scan results."""

import json
import sys

from rich.console import Console
from rich.table import Table

console = Console()


# ============================================================================
# Pure Helper Functions for Scan Report Display
# ============================================================================


def _build_image_namespace_map(workload_details):
    """Build mapping of image URLs to namespaces where they're used.

    PURE FUNCTION: No I/O, no side effects.

    Args:
        workload_details: List of workload objects with non_ecr_images and namespace attributes

    Returns:
        Dict mapping image_url (str) -> set of namespace names (str)

    Example:
        >>> workloads = [
        ...     Workload(namespace="prod", non_ecr_images=[ImageRef("nginx:latest")]),
        ...     Workload(namespace="staging", non_ecr_images=[ImageRef("nginx:latest")])
        ... ]
        >>> result = _build_image_namespace_map(workloads)
        >>> result["nginx:latest"] == {"prod", "staging"}
        True
    """
    image_namespace_map = {}
    for workload in workload_details:
        for image_ref in workload.non_ecr_images:
            if image_ref.image_url not in image_namespace_map:
                image_namespace_map[image_ref.image_url] = set()
            image_namespace_map[image_ref.image_url].add(workload.namespace)
    return image_namespace_map


def _format_namespace_list(namespaces):
    """Format set of namespaces as sorted, comma-separated string.

    PURE FUNCTION: No I/O, no side effects.

    Args:
        namespaces: Set or iterable of namespace strings

    Returns:
        Comma-separated string of sorted namespace names

    Examples:
        >>> _format_namespace_list({"prod", "staging", "dev"})
        'dev, prod, staging'
        >>> _format_namespace_list(set())
        ''
        >>> _format_namespace_list({"single"})
        'single'
    """
    return ", ".join(sorted(namespaces))


def _format_truncated_image_list(image_urls, max_length=50):
    """Format list of image URLs as comma-separated string, truncating if needed.

    PURE FUNCTION: No I/O, no side effects.

    Optimized to avoid O(n²) string concatenation by pre-checking estimated length.

    Args:
        image_urls: List of image URL strings
        max_length: Maximum length before truncation (default 50)

    Returns:
        Comma-separated string, possibly truncated with "..." suffix

    Examples:
        >>> _format_truncated_image_list(["nginx:latest", "redis:7"])
        'nginx:latest, redis:7'
        >>> _format_truncated_image_list(["a" * 30, "b" * 30], max_length=20)
        'aaaaaaaaaaaaaaaaaaaaa...'
        >>> _format_truncated_image_list([])
        ''
    """
    if not image_urls:
        return ""

    # Estimate full string length: sum of URLs + separators (", " = 2 chars each)
    full_estimate = sum(len(url) for url in image_urls) + (len(image_urls) - 1) * 2

    if full_estimate <= max_length:
        # Short enough - build and return directly
        return ", ".join(image_urls)

    # Build full string once (O(n)), then truncate
    full_string = ", ".join(image_urls)
    if len(full_string) > max_length:
        return full_string[:max_length] + "..."
    return full_string


def _build_image_row_data(image_url, image_namespace_map):
    """Build table row data for a single image.

    PURE FUNCTION: No I/O, no side effects.

    Args:
        image_url: Image URL string to format
        image_namespace_map: Dict mapping image URLs to namespace sets

    Returns:
        Tuple of (image_url, registry, repository, tag, namespace_display)

    Example:
        >>> from ecreshore.services.k8s_models import ImageReference
        >>> namespace_map = {"nginx:latest": {"prod", "dev"}}
        >>> row = _build_image_row_data("nginx:latest", namespace_map)
        >>> row[0]  # image_url
        'nginx:latest'
        >>> row[4]  # namespace_display (sorted)
        'dev, prod'
    """
    from ...services.k8s_models import ImageReference

    img_ref = ImageReference.parse(image_url)
    namespaces = image_namespace_map.get(image_url, set())
    namespace_display = _format_namespace_list(namespaces)

    # Prefer tag over digest for display (tag is more human-readable)
    tag_display = img_ref.tag if img_ref.tag else (f"@{img_ref.digest}" if img_ref.digest else "latest")

    return (
        image_url,
        img_ref.registry or "docker.io",
        img_ref.repository,
        tag_display,
        namespace_display,
    )


def _handle_scan_output(
    scan_result, output, target_registry, export, progress_reporter, verbose
):
    """Handle output generation and display/export based on format."""
    if output == "report":
        _display_scan_report(scan_result, progress_reporter, verbose)
    elif output == "json":
        _handle_json_output(scan_result, target_registry, export, progress_reporter)
    elif output == "yaml":
        _handle_yaml_output(scan_result, target_registry, export, progress_reporter)
    elif output == "batch-config":
        _handle_batch_config_output(
            scan_result, target_registry, export, progress_reporter
        )


def _handle_json_output(scan_result, target_registry, export, progress_reporter):
    """Handle JSON output format."""
    from ...services.k8s_config import K8sConfigGenerator

    if target_registry:
        config_gen = K8sConfigGenerator(target_registry)
        result_data = config_gen.generate_scan_results_json(scan_result)
    else:
        result_data = _scan_result_to_dict(scan_result)

    json_output = json.dumps(result_data, indent=2)
    if export:
        _write_output_to_file(json_output, export)
        progress_reporter.success(f"JSON results exported to {export}")
    else:
        console.print(json_output)


def _handle_yaml_output(scan_result, target_registry, export, progress_reporter):
    """Handle YAML output format."""
    from ...services.k8s_config import K8sConfigGenerator

    if target_registry:
        config_gen = K8sConfigGenerator(target_registry)
        yaml_output = config_gen.generate_scan_results_yaml(scan_result)
    else:
        yaml_output = _generate_basic_yaml(scan_result)

    if export:
        _write_output_to_file(yaml_output, export)
        progress_reporter.success(f"YAML results exported to {export}")
    else:
        console.print(yaml_output)


def _handle_batch_config_output(
    scan_result, target_registry, export, progress_reporter
):
    """Handle batch-config output format."""
    from ...services.k8s_config import K8sConfigGenerator

    try:
        config_gen = K8sConfigGenerator(target_registry)
        batch_config = config_gen.generate_batch_config_yaml(scan_result)

        # Show resolved registry if it was auto-detected
        resolved_registry = config_gen.get_target_registry()
        if not target_registry:
            progress_reporter.info(f"Using ECR registry: {resolved_registry}")

        if export:
            _write_output_to_file(batch_config, export)
            progress_reporter.success(f"Batch configuration exported to {export}")
        else:
            console.print(batch_config)
    except RuntimeError as e:
        progress_reporter.error(str(e))
        progress_reporter.info(
            "Provide --target-registry explicitly or ensure AWS credentials are configured"
        )
        sys.exit(1)


def _display_scan_report(scan_result, progress_reporter, verbose):
    """Display scan results as a console report.

    Complexity: 4 (was 12 before refactoring)

    Responsibilities:
    - Display summary statistics
    - Create and populate Rich tables for images and workloads
    - Delegate data transformation to pure helper functions
    """
    # Summary
    progress_reporter.success("Cluster scan completed")
    console.print()

    console.print(f"[bold]Cluster:[/bold] {scan_result.cluster_name or 'Unknown'}")
    console.print(
        f"[bold]Scan time:[/bold] {scan_result.scan_timestamp.strftime('%Y-%m-%d %H:%M:%S')}"
    )
    console.print(
        f"[bold]Total workloads scanned:[/bold] {scan_result.total_workloads_scanned}"
    )
    console.print(
        f"[bold]Workloads with non-ECR images:[/bold] {scan_result.workloads_with_non_ecr_images}"
    )
    console.print(
        f"[bold]Unique non-ECR images:[/bold] {scan_result.total_unique_non_ecr_images}"
    )

    if scan_result.total_unique_non_ecr_images == 0:
        progress_reporter.success("All container images are already hosted in ECR!")
        return

    console.print()

    # Unique images table with usage information
    console.print("[bold]Non-ECR Images Found:[/bold]")
    images_table = Table(show_header=True, header_style="bold blue")
    images_table.add_column("Image", style="cyan")
    images_table.add_column("Registry", style="dim")
    images_table.add_column("Repository", style="green")
    images_table.add_column("Tag", style="yellow")
    images_table.add_column("Used in Namespaces", style="magenta")

    # Build namespace usage map using pure helper
    image_namespace_map = _build_image_namespace_map(scan_result.workload_details)

    # Populate images table using pure helper for row data
    for image_url in sorted(scan_result.unique_non_ecr_images):
        row_data = _build_image_row_data(image_url, image_namespace_map)
        images_table.add_row(*row_data)

    console.print(images_table)

    if verbose:
        console.print()
        console.print("[bold]Workload Details:[/bold]")

        workloads_table = Table(show_header=True, header_style="bold blue")
        workloads_table.add_column("Namespace", style="cyan")
        workloads_table.add_column("Name", style="green")
        workloads_table.add_column("Type", style="yellow")
        workloads_table.add_column("Non-ECR Images", style="dim")

        for workload in scan_result.workload_details:
            image_urls = [img.image_url for img in workload.non_ecr_images]
            # Use pure helper for optimized truncation logic
            display_text = _format_truncated_image_list(image_urls, max_length=50)

            workloads_table.add_row(
                workload.namespace,
                workload.name,
                workload.workload_type,
                display_text,
            )

        console.print(workloads_table)


def _scan_result_to_dict(scan_result):
    """Convert scan result to basic dictionary."""
    # Build namespace usage map for each image
    image_namespace_map = {}
    for workload in scan_result.workload_details:
        for image_ref in workload.non_ecr_images:
            if image_ref.image_url not in image_namespace_map:
                image_namespace_map[image_ref.image_url] = set()
            image_namespace_map[image_ref.image_url].add(workload.namespace)

    # Convert to sorted list with namespaces
    unique_images_with_namespaces = []
    for image_url in sorted(scan_result.unique_non_ecr_images):
        namespaces = sorted(image_namespace_map.get(image_url, set()))
        unique_images_with_namespaces.append(
            {"image_url": image_url, "namespaces": namespaces}
        )

    return {
        "cluster_name": scan_result.cluster_name,
        "scan_timestamp": scan_result.scan_timestamp.isoformat(),
        "total_workloads_scanned": scan_result.total_workloads_scanned,
        "workloads_with_non_ecr_images": scan_result.workloads_with_non_ecr_images,
        "total_unique_non_ecr_images": scan_result.total_unique_non_ecr_images,
        "unique_non_ecr_images": unique_images_with_namespaces,
    }


def _generate_basic_yaml(scan_result):
    """Generate basic YAML output without K8sConfigGenerator."""
    from yaml_for_humans import dumps

    return dumps(_scan_result_to_dict(scan_result))


def _write_output_to_file(content, filepath):
    """Write content to file."""
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
