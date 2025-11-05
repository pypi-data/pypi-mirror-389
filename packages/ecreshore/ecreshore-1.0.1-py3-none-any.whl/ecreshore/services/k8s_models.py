"""Data models for Kubernetes cluster scanning."""

import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Set, Tuple


@dataclass
class ImageReference:
    """Represents a container image reference found in a Kubernetes workload."""

    image_url: str
    registry: Optional[str]
    repository: str
    tag: Optional[str]
    digest: Optional[str]
    is_ecr: bool

    @classmethod
    def parse(cls, image_url: str) -> "ImageReference":
        """Parse an image URL into components."""
        registry, repository, tag, digest = parse_image_reference(image_url)
        is_ecr = is_ecr_registry(registry) if registry else False

        return cls(
            image_url=image_url,
            registry=registry,
            repository=repository,
            tag=tag,
            digest=digest,
            is_ecr=is_ecr,
        )


@dataclass
class WorkloadImageInfo:
    """Information about images used in a Kubernetes workload."""

    name: str
    namespace: str
    workload_type: str  # Deployment, DaemonSet, etc.
    labels: Dict[str, str]
    annotations: Dict[str, str]
    images: List[ImageReference]
    non_ecr_images: List[ImageReference] = field(init=False)

    def __post_init__(self):
        """Filter non-ECR images after initialization."""
        self.non_ecr_images = [img for img in self.images if not img.is_ecr]


@dataclass
class ClusterScanResult:
    """Results of scanning a Kubernetes cluster for non-ECR images."""

    cluster_name: Optional[str]
    scan_timestamp: datetime
    total_workloads_scanned: int
    workloads_with_non_ecr_images: int
    total_unique_non_ecr_images: int
    workload_details: List[WorkloadImageInfo]
    unique_non_ecr_images: Set[str] = field(init=False)

    def __post_init__(self):
        """Calculate unique non-ECR images."""
        self.unique_non_ecr_images = set()
        for workload in self.workload_details:
            for image in workload.non_ecr_images:
                self.unique_non_ecr_images.add(image.image_url)

        self.total_unique_non_ecr_images = len(self.unique_non_ecr_images)


def parse_image_reference(image_ref: str) -> Tuple[Optional[str], str, Optional[str], Optional[str]]:
    """Parse an image reference into registry, repository, tag, and digest components.

    Returns:
        Tuple of (registry, repository, tag, digest) where tag and digest can both be present.
    """

    # Step 1: Extract digest if present (image@sha256:...)
    digest = None
    if "@" in image_ref:
        image_part, digest_part = image_ref.rsplit("@", 1)
        digest = digest_part  # Store without @ prefix
    else:
        image_part = image_ref

    # Step 2: Extract tag from image_part
    tag = None
    if ":" in image_part:
        # Check if this is registry:port/image or image:tag
        parts = image_part.split("/")
        if len(parts) == 1:
            # No slash, must be image:tag
            if ":" in parts[0]:
                image_part, tag = parts[0].rsplit(":", 1)
            else:
                # No tag in image, will default later if no digest
                pass
        else:
            # Has slash - check if last part has tag
            last_part = parts[-1]
            if ":" in last_part and not re.match(r".*:\d+$", last_part):
                # Has tag, not port
                image_part = (
                    "/".join(parts[:-1]) + "/" + last_part.rsplit(":", 1)[0]
                )
                tag = last_part.rsplit(":", 1)[1]
            # else: No tag found, will default later if no digest

    # Set default tag only if neither tag nor digest was found
    if tag is None and digest is None:
        tag = "latest"

    # Step 3: Split registry from repository
    parts = image_part.split("/")

    if len(parts) == 1:
        # Just image name, no explicit registry
        return None, parts[0], tag, digest

    # Check if first part is registry (contains . or :)
    if "." in parts[0] or ":" in parts[0]:
        registry = parts[0]
        repository = "/".join(parts[1:])
    else:
        # No explicit registry
        registry = None
        repository = image_part

    return registry, repository, tag, digest


def is_ecr_registry(registry: str) -> bool:
    """Check if a registry hostname is an AWS ECR registry (private or public)."""
    if not registry:
        return False

    # Private ECR registry pattern: account-id.dkr.ecr.region.amazonaws.com
    private_ecr_pattern = r"^\d{12}\.dkr\.ecr\.[a-z0-9-]+\.amazonaws\.com$"

    # Public ECR registry pattern: public.ecr.aws
    public_ecr_pattern = r"^public\.ecr\.aws$"

    return bool(
        re.match(private_ecr_pattern, registry)
        or re.match(public_ecr_pattern, registry)
    )
