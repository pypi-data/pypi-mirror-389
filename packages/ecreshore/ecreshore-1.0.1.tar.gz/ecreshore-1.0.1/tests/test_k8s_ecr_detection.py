"""Tests for ECR registry auto-detection in K8s configuration generation."""

import pytest
from unittest.mock import patch, Mock
from datetime import datetime

from src.ecreshore.services.k8s_config import K8sConfigGenerator
from src.ecreshore.services.k8s_models import ClusterScanResult


def test_explicit_registry_used():
    """Test that explicit registry is used when provided."""
    explicit_registry = "123456789012.dkr.ecr.us-west-2.amazonaws.com"
    config_gen = K8sConfigGenerator(target_registry=explicit_registry)
    
    assert config_gen.get_target_registry() == explicit_registry


@patch('boto3.client')
@patch('boto3.Session')
def test_registry_auto_detection(mock_session, mock_boto_client):
    """Test ECR registry auto-detection from AWS credentials."""
    # Mock STS client response
    mock_sts = Mock()
    mock_sts.get_caller_identity.return_value = {'Account': '999888777666'}
    mock_boto_client.return_value = mock_sts
    
    # Mock session for region
    mock_session_instance = Mock()
    mock_session_instance.region_name = 'eu-west-1'
    mock_session.return_value = mock_session_instance
    
    config_gen = K8sConfigGenerator()
    registry = config_gen.get_target_registry()
    
    expected = "999888777666.dkr.ecr.eu-west-1.amazonaws.com"
    assert registry == expected
    
    # Verify boto3 calls
    mock_boto_client.assert_called_once_with('sts')
    mock_sts.get_caller_identity.assert_called_once()


@patch('boto3.client')
@patch('boto3.Session')
def test_registry_auto_detection_default_region(mock_session, mock_boto_client):
    """Test ECR registry auto-detection with default region fallback."""
    # Mock STS client response
    mock_sts = Mock()
    mock_sts.get_caller_identity.return_value = {'Account': '111222333444'}
    mock_boto_client.return_value = mock_sts
    
    # Mock session with no region (None)
    mock_session_instance = Mock()
    mock_session_instance.region_name = None
    mock_session.return_value = mock_session_instance
    
    config_gen = K8sConfigGenerator(default_region='us-east-1')
    registry = config_gen.get_target_registry()
    
    expected = "111222333444.dkr.ecr.us-east-1.amazonaws.com"
    assert registry == expected


@patch('boto3.client')
def test_registry_auto_detection_failure(mock_boto_client):
    """Test error handling when AWS credentials are not available."""
    # Mock STS client to raise exception
    mock_boto_client.side_effect = Exception("No credentials")
    
    config_gen = K8sConfigGenerator()
    
    with pytest.raises(RuntimeError, match="Failed to derive ECR registry from AWS credentials"):
        config_gen.get_target_registry()


@patch('boto3.client')
@patch('boto3.Session')
def test_batch_config_with_auto_registry(mock_session, mock_boto_client):
    """Test batch config generation with auto-detected registry."""
    # Mock AWS responses
    mock_sts = Mock()
    mock_sts.get_caller_identity.return_value = {'Account': '555666777888'}
    mock_boto_client.return_value = mock_sts
    
    mock_session_instance = Mock()
    mock_session_instance.region_name = 'ap-southeast-2'
    mock_session.return_value = mock_session_instance
    
    # Create empty scan result for testing
    empty_scan = ClusterScanResult(
        cluster_name="test-cluster",
        scan_timestamp=datetime.now(),
        total_workloads_scanned=0,
        workloads_with_non_ecr_images=0,
        total_unique_non_ecr_images=0,
        workload_details=[]
    )
    
    config_gen = K8sConfigGenerator()
    yaml_output = config_gen.generate_batch_config_yaml(empty_scan)
    
    # Check that auto-detected registry appears in output
    assert "555666777888.dkr.ecr.ap-southeast-2.amazonaws.com" in yaml_output
    assert "region: ap-southeast-2" in yaml_output


@patch('boto3.client')
@patch('boto3.Session')
def test_registry_caching(mock_session, mock_boto_client):
    """Test that registry detection is cached after first call."""
    # Mock AWS responses
    mock_sts = Mock()
    mock_sts.get_caller_identity.return_value = {'Account': '111111111111'}
    mock_boto_client.return_value = mock_sts
    
    mock_session_instance = Mock()
    mock_session_instance.region_name = 'us-west-1'
    mock_session.return_value = mock_session_instance
    
    config_gen = K8sConfigGenerator()
    
    # Call twice
    registry1 = config_gen.get_target_registry()
    registry2 = config_gen.get_target_registry()
    
    # Should be same result
    assert registry1 == registry2
    assert registry1 == "111111111111.dkr.ecr.us-west-1.amazonaws.com"
    
    # STS should only be called once due to caching
    assert mock_boto_client.call_count == 1
    assert mock_sts.get_caller_identity.call_count == 1


def test_region_extraction_from_ecr_url():
    """Test region extraction from ECR registry URL."""
    config_gen = K8sConfigGenerator("123456789012.dkr.ecr.eu-central-1.amazonaws.com")
    
    empty_scan = ClusterScanResult(
        cluster_name="test-cluster",
        scan_timestamp=datetime.now(),
        total_workloads_scanned=0,
        workloads_with_non_ecr_images=0,
        total_unique_non_ecr_images=0,
        workload_details=[]
    )
    
    yaml_output = config_gen.generate_batch_config_yaml(empty_scan)
    
    # Should extract region from ECR URL
    assert "region: eu-central-1" in yaml_output
    assert "Target ECR registry: 123456789012.dkr.ecr.eu-central-1.amazonaws.com" in yaml_output


def test_non_ecr_registry_fallback():
    """Test fallback to default region for non-ECR registries."""
    config_gen = K8sConfigGenerator("my-custom-registry.com", default_region="us-west-2")
    
    empty_scan = ClusterScanResult(
        cluster_name="test-cluster",
        scan_timestamp=datetime.now(),
        total_workloads_scanned=0,
        workloads_with_non_ecr_images=0,
        total_unique_non_ecr_images=0,
        workload_details=[]
    )
    
    yaml_output = config_gen.generate_batch_config_yaml(empty_scan)
    
    # Should use default region for non-ECR registry
    assert "region: us-west-2" in yaml_output