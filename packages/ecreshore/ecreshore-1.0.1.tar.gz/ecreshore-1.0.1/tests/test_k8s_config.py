"""Tests for Kubernetes configuration generation."""

import pytest
from datetime import datetime
from unittest.mock import patch

from src.ecreshore.services.k8s_config import K8sConfigGenerator
from src.ecreshore.services.k8s_models import (
    ImageReference,
    WorkloadImageInfo, 
    ClusterScanResult
)


@pytest.fixture
def sample_scan_result():
    """Create a sample scan result for testing."""
    workload1 = WorkloadImageInfo(
        name="web-app",
        namespace="production",
        workload_type="Deployment",
        labels={"app": "web", "version": "v1"},
        annotations={"description": "Main web application"},
        images=[
            ImageReference.parse("nginx:1.21"),
            ImageReference.parse("redis:6.2")
        ]
    )
    
    workload2 = WorkloadImageInfo(
        name="background-job", 
        namespace="production",
        workload_type="CronJob",
        labels={"app": "worker"},
        annotations={},
        images=[
            ImageReference.parse("python:3.9"),
            ImageReference.parse("postgres:13")
        ]
    )
    
    return ClusterScanResult(
        cluster_name="production-cluster",
        scan_timestamp=datetime(2023, 10, 15, 14, 30, 0),
        total_workloads_scanned=5,
        workloads_with_non_ecr_images=2, 
        total_unique_non_ecr_images=0,  # Calculated automatically
        workload_details=[workload1, workload2]
    )


def test_generate_target_repository_name_simple():
    """Test target repository name generation for simple images."""
    config_gen = K8sConfigGenerator("123456789012.dkr.ecr.us-east-1.amazonaws.com")
    
    # Simple Docker Hub image
    img_ref = ImageReference.parse("nginx:1.21")
    target_repo = config_gen._generate_target_repository_name(img_ref)
    assert target_repo == "nginx"
    
    # Image with namespace (first directory trimmed)
    img_ref = ImageReference.parse("library/redis:6.2")
    target_repo = config_gen._generate_target_repository_name(img_ref)
    assert target_repo == "redis"


def test_generate_target_repository_name_with_registry():
    """Test target repository name generation without registry prefix."""
    config_gen = K8sConfigGenerator("123456789012.dkr.ecr.us-east-1.amazonaws.com")
    
    # GCR image (first directory trimmed, no registry prefix)
    img_ref = ImageReference.parse("gcr.io/project/app:v1.0")
    target_repo = config_gen._generate_target_repository_name(img_ref)
    assert target_repo == "app"
    
    # Quay image (first directory trimmed, no registry prefix)
    img_ref = ImageReference.parse("quay.io/prometheus/prometheus:v2.30.0")
    target_repo = config_gen._generate_target_repository_name(img_ref)
    assert target_repo == "prometheus"


def test_generate_target_repository_name_special_chars():
    """Test target repository name handles special characters."""
    config_gen = K8sConfigGenerator("123456789012.dkr.ecr.us-east-1.amazonaws.com")
    
    # Image with underscores and special chars (first directory trimmed)
    img_ref = ImageReference.parse("my_custom/app-name_v2:latest")
    target_repo = config_gen._generate_target_repository_name(img_ref)
    assert target_repo == "app-name-v2"


def test_generate_target_repository_name_multi_directory():
    """Test target repository name trims first directory element."""
    config_gen = K8sConfigGenerator("123456789012.dkr.ecr.us-east-1.amazonaws.com")
    
    # Multi-directory images should have first directory trimmed
    test_cases = [
        ("images/misc:latest", "misc"),
        ("bitnami/redis:6.0", "redis"),
        ("library/alpine:3.14", "alpine"),
        ("docker.io/bitnami/postgresql:13", "postgresql-13"),
        ("gcr.io/project/images/app:v1", "images-app"),
    ]
    
    for image_url, expected in test_cases:
        img_ref = ImageReference.parse(image_url)
        target_repo = config_gen._generate_target_repository_name(img_ref)
        assert target_repo == expected, f"Failed for {image_url}: expected {expected}, got {target_repo}"


def test_generate_batch_config_yaml(sample_scan_result):
    """Test batch configuration YAML generation."""
    config_gen = K8sConfigGenerator("123456789012.dkr.ecr.us-east-1.amazonaws.com", "us-west-2")
    
    yaml_output = config_gen.generate_batch_config_yaml(sample_scan_result)
    
    # Check that it contains expected elements
    assert "settings:" in yaml_output
    assert "transfers:" in yaml_output
    assert "concurrent_transfers: 3" in yaml_output
    # Region should be extracted from ECR registry URL, not default
    assert "region: us-east-1" in yaml_output
    assert "source: nginx" in yaml_output
    assert "source_tag: '1.21'" in yaml_output
    assert "target: nginx" in yaml_output


def test_generate_batch_config_yaml_with_registry():
    """Test batch configuration YAML generation with explicit registry."""
    config_gen = K8sConfigGenerator("123456789012.dkr.ecr.us-east-1.amazonaws.com", "us-west-2")
    
    # Create scan result with images from external registry
    workload = WorkloadImageInfo(
        name="test-app",
        namespace="default",
        workload_type="Deployment",
        labels={},
        annotations={},
        images=[
            ImageReference.parse("registry.revsys.com/images/misc:util-pg16"),
            ImageReference.parse("gcr.io/project/app:v1.0")
        ]
    )
    
    scan_result = ClusterScanResult(
        cluster_name="test-cluster",
        scan_timestamp=datetime(2023, 10, 15, 14, 30, 0),
        total_workloads_scanned=1,
        workloads_with_non_ecr_images=1,
        total_unique_non_ecr_images=0,
        workload_details=[workload]
    )
    
    yaml_output = config_gen.generate_batch_config_yaml(scan_result)
    
    # Check that registry is included in source
    assert "source: registry.revsys.com/images/misc" in yaml_output
    assert "source_tag: util-pg16" in yaml_output
    assert "target: misc" in yaml_output  # First directory trimmed, no registry prefix
    assert "source: gcr.io/project/app" in yaml_output
    assert "source_tag: v1.0" in yaml_output
    assert "target: app" in yaml_output  # First directory trimmed, no registry prefix
    
    # Check comment header
    assert "Kubernetes cluster scan" in yaml_output
    assert "test-cluster" in yaml_output
    assert "2023-10-15" in yaml_output


def test_generate_scan_results_yaml(sample_scan_result):
    """Test scan results YAML generation."""
    config_gen = K8sConfigGenerator("123456789012.dkr.ecr.us-east-1.amazonaws.com")
    
    yaml_output = config_gen.generate_scan_results_yaml(sample_scan_result)
    
    # Check structure
    assert "cluster_scan_results:" in yaml_output
    assert "cluster_name: production-cluster" in yaml_output
    assert "total_workloads_scanned: 5" in yaml_output
    assert "workloads_with_non_ecr_images: 2" in yaml_output
    assert "workload_details:" in yaml_output
    
    # Check workload details
    assert "name: web-app" in yaml_output
    assert "namespace: production" in yaml_output
    assert "type: Deployment" in yaml_output
    assert "nginx:1.21" in yaml_output
    assert "redis:6.2" in yaml_output


def test_generate_scan_results_json(sample_scan_result):
    """Test scan results JSON generation."""
    config_gen = K8sConfigGenerator("123456789012.dkr.ecr.us-east-1.amazonaws.com")
    
    json_data = config_gen.generate_scan_results_json(sample_scan_result)
    
    # Check structure
    assert json_data['cluster_name'] == "production-cluster"
    assert json_data['summary']['total_workloads_scanned'] == 5
    assert json_data['summary']['workloads_with_non_ecr_images'] == 2
    assert json_data['summary']['total_unique_non_ecr_images'] == 4
    
    # Check unique images list structure
    assert len(json_data['unique_non_ecr_images']) == 4
    
    # Find specific images and check they have namespace info
    nginx_image = next(img for img in json_data['unique_non_ecr_images'] if img['image_url'] == 'nginx:1.21')
    assert nginx_image['namespaces'] == ['production']
    
    redis_image = next(img for img in json_data['unique_non_ecr_images'] if img['image_url'] == 'redis:6.2') 
    assert redis_image['namespaces'] == ['production']
    
    # Check workload details
    assert len(json_data['workload_details']) == 2
    workload1 = json_data['workload_details'][0]
    assert workload1['name'] == "web-app"
    assert workload1['namespace'] == "production"
    assert workload1['type'] == "Deployment"
    assert len(workload1['images']) == 2
    assert len(workload1['non_ecr_images']) == 2
    
    # Check image details
    image1 = workload1['images'][0]
    assert image1['image_url'] == "nginx:1.21"
    assert image1['registry'] is None
    assert image1['repository'] == "nginx"
    assert image1['tag'] == "1.21"
    assert image1['digest'] is None
    assert image1['is_ecr'] is False


def test_empty_scan_result():
    """Test configuration generation with empty scan results."""
    empty_scan = ClusterScanResult(
        cluster_name="empty-cluster",
        scan_timestamp=datetime.now(),
        total_workloads_scanned=0,
        workloads_with_non_ecr_images=0,
        total_unique_non_ecr_images=0,
        workload_details=[]
    )
    
    config_gen = K8sConfigGenerator("123456789012.dkr.ecr.us-east-1.amazonaws.com")
    
    # Should generate valid but empty configuration
    yaml_output = config_gen.generate_batch_config_yaml(empty_scan)
    assert "settings:" in yaml_output
    assert "transfers: []" in yaml_output
    
    json_data = config_gen.generate_scan_results_json(empty_scan)
    assert json_data['summary']['total_workloads_scanned'] == 0
    assert json_data['workload_details'] == []
    assert json_data['unique_non_ecr_images'] == []


def test_mixed_ecr_and_non_ecr_images():
    """Test configuration generation with mixed ECR and non-ECR images."""
    workload = WorkloadImageInfo(
        name="mixed-app",
        namespace="default",
        workload_type="Deployment",
        labels={},
        annotations={},
        images=[
            ImageReference.parse("nginx:1.21"),  # Non-ECR
            ImageReference.parse("123456789012.dkr.ecr.us-east-1.amazonaws.com/existing:v1.0"),  # ECR
            ImageReference.parse("redis:6.2")  # Non-ECR
        ]
    )
    
    scan_result = ClusterScanResult(
        cluster_name="mixed-cluster",
        scan_timestamp=datetime.now(),
        total_workloads_scanned=1,
        workloads_with_non_ecr_images=1,
        total_unique_non_ecr_images=0,
        workload_details=[workload]
    )
    
    config_gen = K8sConfigGenerator("123456789012.dkr.ecr.us-east-1.amazonaws.com")
    
    # Batch config should only include non-ECR images
    yaml_output = config_gen.generate_batch_config_yaml(scan_result)
    assert "source: nginx" in yaml_output
    assert "source: redis" in yaml_output
    assert "existing" not in yaml_output  # ECR image should not appear
    
    # JSON should include all images in workload details but only non-ECR in unique list
    json_data = config_gen.generate_scan_results_json(scan_result)
    assert len(json_data['workload_details'][0]['images']) == 3
    assert len(json_data['workload_details'][0]['non_ecr_images']) == 2
    assert len(json_data['unique_non_ecr_images']) == 2
    
    # Check that unique images have namespace information
    nginx_image = next(img for img in json_data['unique_non_ecr_images'] if img['image_url'] == 'nginx:1.21')
    assert nginx_image['namespaces'] == ['default']