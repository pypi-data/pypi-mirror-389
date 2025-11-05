"""Tests for public ECR registry filtering."""

import pytest
from datetime import datetime

from src.ecreshore.services.k8s_models import (
    ImageReference,
    WorkloadImageInfo, 
    ClusterScanResult,
    is_ecr_registry
)


def test_public_ecr_recognition():
    """Test that public.ecr.aws is recognized as ECR registry."""
    assert is_ecr_registry("public.ecr.aws") is True
    
    # Variations that should not match
    assert is_ecr_registry("public-ecr.aws") is False
    assert is_ecr_registry("public.ecr.com") is False
    assert is_ecr_registry("public.ecr.amazonaws.com") is False


def test_public_ecr_image_parsing():
    """Test parsing of public ECR image references."""
    # Test specific examples to verify parsing
    img_ref = ImageReference.parse("public.ecr.aws/nginx/nginx:latest")
    assert img_ref.registry == "public.ecr.aws"
    assert img_ref.repository == "nginx/nginx"
    assert img_ref.tag == "latest"
    assert img_ref.digest is None
    assert img_ref.is_ecr is True

    # Test without explicit tag
    img_ref = ImageReference.parse("public.ecr.aws/bitnami/nginx")
    assert img_ref.registry == "public.ecr.aws"
    assert img_ref.repository == "bitnami/nginx"
    assert img_ref.tag == "latest"
    assert img_ref.digest is None
    assert img_ref.is_ecr is True

    # Test with numeric tag
    img_ref = ImageReference.parse("public.ecr.aws/lambda/python:3.9")
    assert img_ref.registry == "public.ecr.aws"
    assert img_ref.repository == "lambda/python"
    assert img_ref.tag == "3.9"
    assert img_ref.digest is None
    assert img_ref.is_ecr is True


def test_mixed_ecr_registry_filtering():
    """Test filtering with mix of private ECR, public ECR, and other registries."""
    images = [
        ImageReference.parse("docker.io/nginx:1.21"),  # Docker Hub
        ImageReference.parse("public.ecr.aws/nginx/nginx:latest"),  # Public ECR
        ImageReference.parse("123456789012.dkr.ecr.us-east-1.amazonaws.com/my-app:v1.0"),  # Private ECR
        ImageReference.parse("gcr.io/project/app:v1.0"),  # Google Container Registry
        ImageReference.parse("quay.io/org/image:tag"),  # Quay
        ImageReference.parse("public.ecr.aws/amazonlinux/amazonlinux:2"),  # Another public ECR
    ]
    
    workload = WorkloadImageInfo(
        name="mixed-workload",
        namespace="default",
        workload_type="Deployment",
        labels={},
        annotations={},
        images=images
    )
    
    # Should filter out both private and public ECR images
    assert len(workload.images) == 6
    assert len(workload.non_ecr_images) == 3  # docker.io, gcr.io, quay.io
    
    non_ecr_urls = [img.image_url for img in workload.non_ecr_images]
    assert "docker.io/nginx:1.21" in non_ecr_urls
    assert "gcr.io/project/app:v1.0" in non_ecr_urls
    assert "quay.io/org/image:tag" in non_ecr_urls
    
    # ECR images should not be in non-ECR list
    assert "public.ecr.aws/nginx/nginx:latest" not in non_ecr_urls
    assert "123456789012.dkr.ecr.us-east-1.amazonaws.com/my-app:v1.0" not in non_ecr_urls
    assert "public.ecr.aws/amazonlinux/amazonlinux:2" not in non_ecr_urls


def test_cluster_scan_result_with_public_ecr():
    """Test cluster scan results properly exclude public ECR images."""
    # Create workloads with mix of registries
    workload1 = WorkloadImageInfo(
        name="web-app",
        namespace="production",
        workload_type="Deployment",
        labels={},
        annotations={},
        images=[
            ImageReference.parse("nginx:1.21"),  # Non-ECR
            ImageReference.parse("public.ecr.aws/nginx/nginx:latest")  # Public ECR
        ]
    )
    
    workload2 = WorkloadImageInfo(
        name="base-images",
        namespace="production",
        workload_type="DaemonSet",
        labels={},
        annotations={},
        images=[
            ImageReference.parse("public.ecr.aws/amazonlinux/amazonlinux:2"),  # Public ECR
            ImageReference.parse("redis:6.2")  # Non-ECR
        ]
    )
    
    scan_result = ClusterScanResult(
        cluster_name="test-cluster",
        scan_timestamp=datetime.now(),
        total_workloads_scanned=2,
        workloads_with_non_ecr_images=2,
        total_unique_non_ecr_images=0,  # Calculated automatically
        workload_details=[workload1, workload2]
    )
    
    # Should only count non-ECR images
    assert len(scan_result.unique_non_ecr_images) == 2  # nginx:1.21, redis:6.2
    assert "nginx:1.21" in scan_result.unique_non_ecr_images
    assert "redis:6.2" in scan_result.unique_non_ecr_images
    
    # Public ECR images should not be in unique non-ECR list
    assert "public.ecr.aws/nginx/nginx:latest" not in scan_result.unique_non_ecr_images
    assert "public.ecr.aws/amazonlinux/amazonlinux:2" not in scan_result.unique_non_ecr_images


def test_public_ecr_only_workload():
    """Test workload with only public ECR images."""
    workload = WorkloadImageInfo(
        name="public-only",
        namespace="default",
        workload_type="Deployment",
        labels={},
        annotations={},
        images=[
            ImageReference.parse("public.ecr.aws/nginx/nginx:latest"),
            ImageReference.parse("public.ecr.aws/amazonlinux/amazonlinux:2")
        ]
    )
    
    # Should have no non-ECR images
    assert len(workload.images) == 2
    assert len(workload.non_ecr_images) == 0


def test_public_ecr_batch_config_exclusion():
    """Test that public ECR images are excluded from batch configuration."""
    from src.ecreshore.services.k8s_config import K8sConfigGenerator
    
    # Create scan result with public ECR images
    workload = WorkloadImageInfo(
        name="mixed-app",
        namespace="default",
        workload_type="Deployment",
        labels={},
        annotations={},
        images=[
            ImageReference.parse("nginx:1.21"),  # Should be included
            ImageReference.parse("public.ecr.aws/nginx/nginx:latest"),  # Should be excluded
            ImageReference.parse("redis:6.2")  # Should be included
        ]
    )
    
    scan_result = ClusterScanResult(
        cluster_name="test-cluster",
        scan_timestamp=datetime.now(),
        total_workloads_scanned=1,
        workloads_with_non_ecr_images=1,
        total_unique_non_ecr_images=0,
        workload_details=[workload]
    )
    
    config_gen = K8sConfigGenerator("123456789012.dkr.ecr.us-east-1.amazonaws.com")
    yaml_output = config_gen.generate_batch_config_yaml(scan_result)
    
    # Should only include non-ECR images in transfers
    assert "source: nginx" in yaml_output
    assert "source: redis" in yaml_output
    
    # Public ECR images should not appear
    assert "public.ecr.aws" not in yaml_output
    assert "Found 2 unique non-ECR images" in yaml_output  # Not 3