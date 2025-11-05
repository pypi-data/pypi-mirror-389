"""Tests for Kubernetes models and image parsing."""

import pytest
from datetime import datetime

from src.ecreshore.services.k8s_models import (
    ImageReference, 
    WorkloadImageInfo, 
    ClusterScanResult,
    parse_image_reference,
    is_ecr_registry
)


def test_parse_image_reference_simple_name():
    """Test parsing simple image name."""
    registry, repository, tag, digest = parse_image_reference("nginx")
    assert registry is None
    assert repository == "nginx"
    assert tag == "latest"
    assert digest is None


def test_parse_image_reference_with_tag():
    """Test parsing image with tag."""
    registry, repository, tag, digest = parse_image_reference("nginx:1.21")
    assert registry is None
    assert repository == "nginx"
    assert tag == "1.21"
    assert digest is None


def test_parse_image_reference_docker_hub():
    """Test parsing Docker Hub image."""
    registry, repository, tag, digest = parse_image_reference("docker.io/library/nginx:1.21")
    assert registry == "docker.io"
    assert repository == "library/nginx"
    assert tag == "1.21"
    assert digest is None


def test_parse_image_reference_private_registry():
    """Test parsing private registry image."""
    registry, repository, tag, digest = parse_image_reference("gcr.io/project/app:v1.0")
    assert registry == "gcr.io"
    assert repository == "project/app"
    assert tag == "v1.0"
    assert digest is None


def test_parse_image_reference_with_digest():
    """Test parsing image with digest."""
    image_url = "nginx@sha256:abc123def456"
    registry, repository, tag, digest = parse_image_reference(image_url)
    assert registry is None
    assert repository == "nginx"
    assert tag is None  # No explicit tag when only digest is present
    assert digest == "sha256:abc123def456"


def test_parse_image_reference_with_tag_and_digest():
    """Test parsing image with both tag and digest."""
    image_url = "registry.k8s.io/ingress-nginx/controller:v1.13.2@sha256:abc123def456"
    registry, repository, tag, digest = parse_image_reference(image_url)
    assert registry == "registry.k8s.io"
    assert repository == "ingress-nginx/controller"
    assert tag == "v1.13.2"
    assert digest == "sha256:abc123def456"


def test_parse_image_reference_ecr():
    """Test parsing private ECR image."""
    image_url = "123456789012.dkr.ecr.us-east-1.amazonaws.com/my-app:v1.0"
    registry, repository, tag, digest = parse_image_reference(image_url)
    assert registry == "123456789012.dkr.ecr.us-east-1.amazonaws.com"
    assert repository == "my-app"
    assert tag == "v1.0"
    assert digest is None


def test_parse_image_reference_public_ecr():
    """Test parsing public ECR image."""
    image_url = "public.ecr.aws/nginx/nginx:latest"
    registry, repository, tag, digest = parse_image_reference(image_url)
    assert registry == "public.ecr.aws"
    assert repository == "nginx/nginx"
    assert tag == "latest"
    assert digest is None


def test_is_ecr_registry():
    """Test ECR registry detection."""
    # Valid private ECR registries
    assert is_ecr_registry("123456789012.dkr.ecr.us-east-1.amazonaws.com") is True
    assert is_ecr_registry("999999999999.dkr.ecr.eu-west-1.amazonaws.com") is True
    assert is_ecr_registry("111111111111.dkr.ecr.ap-southeast-2.amazonaws.com") is True
    
    # Valid public ECR registry
    assert is_ecr_registry("public.ecr.aws") is True
    
    # Invalid ECR registries
    assert is_ecr_registry("docker.io") is False
    assert is_ecr_registry("gcr.io") is False
    assert is_ecr_registry("123456789012.ecr.us-east-1.amazonaws.com") is False  # Missing dkr
    assert is_ecr_registry("12345678901.dkr.ecr.us-east-1.amazonaws.com") is False  # Wrong account ID length
    assert is_ecr_registry("public-ecr.aws") is False  # Wrong public format
    assert is_ecr_registry("public.ecr.com") is False  # Wrong public domain
    assert is_ecr_registry(None) is False
    assert is_ecr_registry("") is False


def test_image_reference_parse():
    """Test ImageReference.parse() class method."""
    # Non-ECR image
    img_ref = ImageReference.parse("nginx:1.21")
    assert img_ref.image_url == "nginx:1.21"
    assert img_ref.registry is None
    assert img_ref.repository == "nginx"
    assert img_ref.tag == "1.21"
    assert img_ref.digest is None
    assert img_ref.is_ecr is False

    # Private ECR image
    private_ecr_url = "123456789012.dkr.ecr.us-east-1.amazonaws.com/my-app:v1.0"
    img_ref = ImageReference.parse(private_ecr_url)
    assert img_ref.image_url == private_ecr_url
    assert img_ref.registry == "123456789012.dkr.ecr.us-east-1.amazonaws.com"
    assert img_ref.repository == "my-app"
    assert img_ref.tag == "v1.0"
    assert img_ref.digest is None
    assert img_ref.is_ecr is True
    
    # Public ECR image
    public_ecr_url = "public.ecr.aws/nginx/nginx:latest"
    img_ref = ImageReference.parse(public_ecr_url)
    assert img_ref.image_url == public_ecr_url
    assert img_ref.registry == "public.ecr.aws"
    assert img_ref.repository == "nginx/nginx"
    assert img_ref.tag == "latest"
    assert img_ref.digest is None
    assert img_ref.is_ecr is True


def test_workload_image_info_non_ecr_filtering():
    """Test WorkloadImageInfo filters non-ECR images correctly."""
    images = [
        ImageReference.parse("nginx:1.21"),
        ImageReference.parse("123456789012.dkr.ecr.us-east-1.amazonaws.com/my-app:v1.0"),  # Private ECR
        ImageReference.parse("public.ecr.aws/nginx/nginx:latest"),  # Public ECR
        ImageReference.parse("redis:6.2")
    ]
    
    workload = WorkloadImageInfo(
        name="test-deployment",
        namespace="default", 
        workload_type="Deployment",
        labels={},
        annotations={},
        images=images
    )
    
    assert len(workload.images) == 4
    assert len(workload.non_ecr_images) == 2  # Only nginx:1.21 and redis:6.2 are non-ECR
    assert workload.non_ecr_images[0].image_url == "nginx:1.21"
    assert workload.non_ecr_images[1].image_url == "redis:6.2"


def test_cluster_scan_result_calculations():
    """Test ClusterScanResult calculations."""
    # Create workloads with mixed ECR/non-ECR images
    workload1 = WorkloadImageInfo(
        name="app1",
        namespace="default",
        workload_type="Deployment",
        labels={},
        annotations={},
        images=[
            ImageReference.parse("nginx:1.21"),
            ImageReference.parse("redis:6.2")
        ]
    )
    
    workload2 = WorkloadImageInfo(
        name="app2", 
        namespace="production",
        workload_type="StatefulSet",
        labels={},
        annotations={},
        images=[
            ImageReference.parse("nginx:1.21"),  # Duplicate
            ImageReference.parse("postgres:13")
        ]
    )
    
    workload3 = WorkloadImageInfo(
        name="app3",
        namespace="production", 
        workload_type="DaemonSet",
        labels={},
        annotations={},
        images=[
            ImageReference.parse("123456789012.dkr.ecr.us-east-1.amazonaws.com/my-app:v1.0")  # ECR only
        ]
    )
    
    scan_result = ClusterScanResult(
        cluster_name="test-cluster",
        scan_timestamp=datetime.now(),
        total_workloads_scanned=3,
        workloads_with_non_ecr_images=2,
        total_unique_non_ecr_images=0,  # Will be calculated
        workload_details=[workload1, workload2, workload3]
    )
    
    # Check calculations
    assert len(scan_result.workload_details) == 3
    assert len(scan_result.unique_non_ecr_images) == 3  # nginx:1.21, redis:6.2, postgres:13
    assert scan_result.total_unique_non_ecr_images == 3
    assert "nginx:1.21" in scan_result.unique_non_ecr_images
    assert "redis:6.2" in scan_result.unique_non_ecr_images 
    assert "postgres:13" in scan_result.unique_non_ecr_images


def test_cluster_scan_result_no_duplicates():
    """Test that ClusterScanResult properly deduplicates images."""
    # Create multiple workloads using same images
    workloads = []
    for i in range(3):
        workload = WorkloadImageInfo(
            name=f"app{i}",
            namespace="default",
            workload_type="Deployment", 
            labels={},
            annotations={},
            images=[
                ImageReference.parse("nginx:1.21"),
                ImageReference.parse("redis:6.2")
            ]
        )
        workloads.append(workload)
    
    scan_result = ClusterScanResult(
        cluster_name="test-cluster",
        scan_timestamp=datetime.now(),
        total_workloads_scanned=3,
        workloads_with_non_ecr_images=3,
        total_unique_non_ecr_images=0,
        workload_details=workloads
    )
    
    # Should only count unique images
    assert len(scan_result.unique_non_ecr_images) == 2
    assert scan_result.total_unique_non_ecr_images == 2