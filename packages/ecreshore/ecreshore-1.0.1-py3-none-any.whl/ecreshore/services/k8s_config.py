"""Configuration generator for Kubernetes scan results."""

import re
from collections import defaultdict
from typing import Dict, Any, Optional

import boto3
from yaml_for_humans import dumps

from .k8s_models import ClusterScanResult, ImageReference
from ..aws_utils import resolve_aws_region

DEFAULT_CONCURRENT_TRANSFERS = 3
DEFAULT_RETRY_ATTEMPTS = 3
DEFAULT_VERIFY_DIGESTS = True


class K8sConfigGenerator:
    """Generates ecreshore batch configurations and YAML output from scan results."""

    def __init__(
        self,
        target_registry: Optional[str] = None,
        default_region: Optional[str] = None,
    ):
        """Initialize with target ECR registry information.

        Args:
            target_registry: ECR registry URL. If None, will be derived from AWS credentials
            default_region: AWS region override. If None, uses standard boto3 region resolution
        """
        self.target_registry = target_registry
        self.default_region = default_region
        self._resolved_registry: Optional[str] = None

    def get_target_registry(self) -> str:
        """Get the target ECR registry, deriving it from AWS if not provided."""
        if self._resolved_registry:
            return self._resolved_registry

        if self.target_registry:
            self._resolved_registry = self.target_registry
            return self._resolved_registry

        # Derive ECR registry from AWS credentials
        try:
            # Get AWS account ID and region
            sts_client = boto3.client("sts")
            account_id = sts_client.get_caller_identity()["Account"]

            # Get region using standard boto3 resolution
            region = resolve_aws_region(self.default_region)

            self._resolved_registry = f"{account_id}.dkr.ecr.{region}.amazonaws.com"
            return self._resolved_registry

        except Exception as e:
            raise RuntimeError(
                f"Failed to derive ECR registry from AWS credentials: {e}"
            )

    def generate_batch_config_yaml(self, scan_result: ClusterScanResult) -> str:
        """Generate a ecreshore batch configuration YAML from scan results."""

        # Ensure we have a registry
        target_registry = self.get_target_registry()

        # Extract region from registry URL for settings
        if "ecr." in target_registry and ".amazonaws.com" in target_registry:
            # Parse region from ECR URL: account.dkr.ecr.region.amazonaws.com
            region_part = target_registry.split(".ecr.")[1].split(".amazonaws.com")[0]
            settings_region = region_part
        else:
            settings_region = resolve_aws_region(self.default_region)

        # Collect unique non-ECR images
        unique_images = {}
        for workload in scan_result.workload_details:
            for image_ref in workload.non_ecr_images:
                unique_images[image_ref.image_url] = image_ref

        # Generate batch configuration dict
        config_dict = {
            "_comment": [
                "ECReshore batch configuration generated from Kubernetes cluster scan",
                f"Cluster: {scan_result.cluster_name or 'Unknown'}",
                f"Scan date: {scan_result.scan_timestamp.isoformat()}",
                f"Target ECR registry: {target_registry}",
                f"Found {len(unique_images)} unique non-ECR images",
            ],
            "settings": {
                "concurrent_transfers": DEFAULT_CONCURRENT_TRANSFERS,
                "retry_attempts": DEFAULT_RETRY_ATTEMPTS,
                "verify_digests": DEFAULT_VERIFY_DIGESTS,
                "region": settings_region,
            },
            "transfers": [],
        }

        for image_url, image_ref in unique_images.items():
            target_repo = self._generate_target_repository_name(image_ref)

            # Build full source repository path including registry
            if image_ref.registry:
                source_repo = f"{image_ref.registry}/{image_ref.repository}"
            else:
                source_repo = image_ref.repository

            # Prefer tag for transfer, fallback to digest if only digest is available
            transfer_tag = image_ref.tag if image_ref.tag else (f"@{image_ref.digest}" if image_ref.digest else "latest")

            config_dict["transfers"].append(
                {
                    "source": source_repo,
                    "source_tag": transfer_tag,
                    "target": target_repo,
                    "target_tag": transfer_tag,
                }
            )

        return dumps(config_dict)

    def generate_scan_results_yaml(self, scan_result: ClusterScanResult) -> str:
        """Generate YAML representation of scan results."""

        # Convert scan results to dict for YAML output
        # Build namespace usage map for each image - use defaultdict to avoid repeated set() creation
        image_namespace_map = defaultdict(set)
        for workload in scan_result.workload_details:
            for image_ref in workload.non_ecr_images:
                image_namespace_map[image_ref.image_url].add(workload.namespace)

        # Convert to sorted list with namespaces
        unique_images_with_namespaces = []
        for image_url in sorted(scan_result.unique_non_ecr_images):
            namespaces = sorted(image_namespace_map[image_url])
            unique_images_with_namespaces.append(
                {"image_url": image_url, "namespaces": namespaces}
            )

        results_dict = {
            "cluster_scan_results": {
                "cluster_name": scan_result.cluster_name,
                "scan_timestamp": scan_result.scan_timestamp.isoformat(),
                "summary": {
                    "total_workloads_scanned": scan_result.total_workloads_scanned,
                    "workloads_with_non_ecr_images": scan_result.workloads_with_non_ecr_images,
                    "total_unique_non_ecr_images": scan_result.total_unique_non_ecr_images,
                },
                "unique_non_ecr_images": unique_images_with_namespaces,
                "workload_details": [],
            }
        }

        # Add workload details
        for workload in scan_result.workload_details:
            workload_dict = {
                "name": workload.name,
                "namespace": workload.namespace,
                "type": workload.workload_type,
                "labels": workload.labels,
                "non_ecr_images": [
                    {
                        "image_url": img.image_url,
                        "registry": img.registry,
                        "repository": img.repository,
                        "tag": img.tag,
                        "digest": img.digest,
                    }
                    for img in workload.non_ecr_images
                ],
            }
            results_dict["cluster_scan_results"]["workload_details"].append(
                workload_dict
            )

        return dumps(results_dict)

    def generate_scan_results_json(
        self, scan_result: ClusterScanResult
    ) -> Dict[str, Any]:
        """Generate JSON-serializable dict of scan results."""

        # Build namespace usage map for each image - use defaultdict to avoid repeated set() creation
        image_namespace_map = defaultdict(set)
        for workload in scan_result.workload_details:
            for image_ref in workload.non_ecr_images:
                image_namespace_map[image_ref.image_url].add(workload.namespace)

        # Convert to sorted list for JSON serialization
        unique_images_with_namespaces = []
        for image_url in sorted(scan_result.unique_non_ecr_images):
            namespaces = sorted(image_namespace_map[image_url])
            unique_images_with_namespaces.append(
                {"image_url": image_url, "namespaces": namespaces}
            )

        return {
            "cluster_name": scan_result.cluster_name,
            "scan_timestamp": scan_result.scan_timestamp.isoformat(),
            "summary": {
                "total_workloads_scanned": scan_result.total_workloads_scanned,
                "workloads_with_non_ecr_images": scan_result.workloads_with_non_ecr_images,
                "total_unique_non_ecr_images": scan_result.total_unique_non_ecr_images,
            },
            "unique_non_ecr_images": unique_images_with_namespaces,
            "workload_details": [
                {
                    "name": workload.name,
                    "namespace": workload.namespace,
                    "type": workload.workload_type,
                    "labels": workload.labels,
                    "annotations": workload.annotations,
                    "images": [
                        {
                            "image_url": img.image_url,
                            "registry": img.registry,
                            "repository": img.repository,
                            "tag": img.tag,
                            "digest": img.digest,
                            "is_ecr": img.is_ecr,
                        }
                        for img in workload.images
                    ],
                    "non_ecr_images": [
                        {
                            "image_url": img.image_url,
                            "registry": img.registry,
                            "repository": img.repository,
                            "tag": img.tag,
                            "digest": img.digest,
                        }
                        for img in workload.non_ecr_images
                    ],
                }
                for workload in scan_result.workload_details
            ],
        }

    def _generate_target_repository_name(self, image_ref: ImageReference) -> str:
        """Generate appropriate ECR repository name from source image."""
        # Trim first directory element for multi-directory repositories
        repo_parts = image_ref.repository.split("/")

        if len(repo_parts) > 1:
            repo_name = "/".join(repo_parts[1:])  # Remove first directory
        else:
            repo_name = image_ref.repository  # Keep as-is for single names

        # Replace slashes and special chars to create valid ECR repo name
        repo_name = repo_name.replace("/", "-").replace("_", "-")

        # Ensure valid ECR repository name
        repo_name = re.sub(r"[^a-z0-9\-_/]", "-", repo_name.lower())
        repo_name = re.sub(r"-+", "-", repo_name)  # Collapse multiple dashes
        repo_name = repo_name.strip("-")  # Remove leading/trailing dashes

        return repo_name
