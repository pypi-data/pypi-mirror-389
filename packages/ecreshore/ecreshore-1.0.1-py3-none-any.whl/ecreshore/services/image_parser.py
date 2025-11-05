"""Business logic functions for parsing image URLs and inferring repository names."""

from typing import Tuple, Optional
import re


def parse_image_with_tag(image_url: str) -> Tuple[str, Optional[str]]:
    """Parse image URL to extract repository and tag.

    Supports standard Docker image URL formats:
    - registry.com/org/repo:tag
    - org/repo:tag
    - repo:tag
    - repo (no tag)

    Args:
        image_url: Full image URL that may include a tag

    Returns:
        Tuple of (repository_without_tag, tag_or_none)

    Examples:
        >>> parse_image_with_tag("ghcr.io/fluxcd/helm-controller:v1.3.0")
        ("ghcr.io/fluxcd/helm-controller", "v1.3.0")

        >>> parse_image_with_tag("nginx:latest")
        ("nginx", "latest")

        >>> parse_image_with_tag("nginx")
        ("nginx", None)

        >>> parse_image_with_tag("myregistry.com/org/app:v2.1")
        ("myregistry.com/org/app", "v2.1")
    """
    # Check for tag delimiter
    if ":" not in image_url:
        return image_url, None

    # Split on the last colon to handle registry URLs like registry.com:5000/repo:tag
    # We need to be careful not to split on port numbers in registry URLs

    # If there are multiple colons, we need to determine if the last part is a tag or port
    parts = image_url.rsplit(":", 1)
    if len(parts) != 2:
        return image_url, None

    repository, potential_tag = parts

    # Check if the potential_tag looks like a port number (registry.com:5000 case)
    # Port numbers are typically 1-5 digits and don't contain letters, dots, or hyphens
    if re.match(r"^\d{1,5}$", potential_tag):
        # This looks like a port number, not a tag
        return image_url, None

    # If potential_tag contains path separators, it's likely not a tag
    # Example: registry.com:5000/repo should not be split
    if "/" in potential_tag:
        return image_url, None

    return repository, potential_tag


def infer_target_repository_name(source_image: str) -> str:
    """Infer target repository name from source image path.

    Extracts the last component of the image path to use as repository name.

    Args:
        source_image: Source image path (without tag)

    Returns:
        Inferred repository name (last path component)

    Examples:
        >>> infer_target_repository_name("ghcr.io/fluxcd/helm-controller")
        "helm-controller"

        >>> infer_target_repository_name("nginx")
        "nginx"

        >>> infer_target_repository_name("myregistry.com/org/app")
        "app"

        >>> infer_target_repository_name("registry.com:5000/namespace/project")
        "project"
    """
    # Remove any registry port specification (e.g., registry.com:5000/repo -> repo)
    # Handle cases like registry.com:5000/namespace/repo

    # First, split on / to get path components
    path_parts = source_image.split("/")

    if len(path_parts) == 1:
        # Single component like "nginx" - return as-is
        return path_parts[0]

    # Multiple components - return the last one
    return path_parts[-1]


def validate_image_tag_conflict(
    image_url: str, explicit_source_tag: Optional[str]
) -> Optional[str]:
    """Validate that image URL tag and explicit --source-tag don't conflict.

    Args:
        image_url: Image URL that may contain a tag
        explicit_source_tag: Explicit --source-tag option value

    Returns:
        Error message if there's a conflict, None if valid

    Examples:
        >>> validate_image_tag_conflict("nginx:latest", "v1.0")
        "Cannot use both image:tag syntax ('nginx:latest') and --source-tag flag ('v1.0') simultaneously"

        >>> validate_image_tag_conflict("nginx:latest", None)
        None

        >>> validate_image_tag_conflict("nginx", "v1.0")
        None
    """
    _, parsed_tag = parse_image_with_tag(image_url)

    # If both tag formats are used, that's an error
    if parsed_tag and explicit_source_tag and explicit_source_tag != "latest":
        return (
            f"Cannot use both image:tag syntax ('{image_url}') and --source-tag flag ('{explicit_source_tag}') simultaneously. "
            f"Use either '{image_url}' OR '{parse_image_with_tag(image_url)[0]} --source-tag {explicit_source_tag}'"
        )

    return None


def resolve_final_source_tag(
    image_url: str, explicit_source_tag: str = "latest"
) -> str:
    """Resolve the final source tag from image URL and explicit option.

    Priority order:
    1. Tag from image URL (if present)
    2. Explicit --source-tag option
    3. Default "latest"

    Args:
        image_url: Image URL that may contain a tag
        explicit_source_tag: Explicit --source-tag value (default "latest")

    Returns:
        Final resolved source tag

    Examples:
        >>> resolve_final_source_tag("nginx:v1.21", "latest")
        "v1.21"

        >>> resolve_final_source_tag("nginx", "v1.20")
        "v1.20"

        >>> resolve_final_source_tag("nginx", "latest")
        "latest"
    """
    _, parsed_tag = parse_image_with_tag(image_url)

    # Use parsed tag if available, otherwise use explicit tag
    return parsed_tag or explicit_source_tag
