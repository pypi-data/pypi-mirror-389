"""Tests for image URL parsing and repository inference business logic."""

import pytest
from src.ecreshore.services.image_parser import (
    parse_image_with_tag,
    infer_target_repository_name,
    validate_image_tag_conflict,
    resolve_final_source_tag
)


def test_parse_image_with_tag_simple_cases():
    """Test parsing simple image URLs with and without tags."""
    # Simple image with tag
    repo, tag = parse_image_with_tag("nginx:latest")
    assert repo == "nginx"
    assert tag == "latest"

    # Simple image with version tag
    repo, tag = parse_image_with_tag("postgres:13.5")
    assert repo == "postgres"
    assert tag == "13.5"

    # Simple image without tag
    repo, tag = parse_image_with_tag("redis")
    assert repo == "redis"
    assert tag is None


def test_parse_image_with_tag_registry_urls():
    """Test parsing registry URLs with various formats."""
    # Full registry URL with tag
    repo, tag = parse_image_with_tag("ghcr.io/fluxcd/helm-controller:v1.3.0")
    assert repo == "ghcr.io/fluxcd/helm-controller"
    assert tag == "v1.3.0"

    # Private registry with organization
    repo, tag = parse_image_with_tag("myregistry.com/org/app:v2.1")
    assert repo == "myregistry.com/org/app"
    assert tag == "v2.1"

    # Docker Hub with organization
    repo, tag = parse_image_with_tag("library/nginx:alpine")
    assert repo == "library/nginx"
    assert tag == "alpine"


def test_parse_image_with_tag_port_numbers():
    """Test that registry port numbers are not confused with tags."""
    # Registry with port number - should not split on port
    repo, tag = parse_image_with_tag("registry.com:5000/repo")
    assert repo == "registry.com:5000/repo"
    assert tag is None

    # Registry with port and actual tag
    repo, tag = parse_image_with_tag("localhost:5000/myapp:v1.0")
    assert repo == "localhost:5000/myapp"
    assert tag == "v1.0"

    # Registry with port and multiple path components
    repo, tag = parse_image_with_tag("registry.company.com:443/team/project:latest")
    assert repo == "registry.company.com:443/team/project"
    assert tag == "latest"


def test_parse_image_with_tag_edge_cases():
    """Test edge cases in image URL parsing."""
    # Tag with special characters
    repo, tag = parse_image_with_tag("app:v1.0-rc.1")
    assert repo == "app"
    assert tag == "v1.0-rc.1"

    # SHA digest instead of tag (should not split on colon)
    repo, tag = parse_image_with_tag("app:sha256:abc123def456")
    assert repo == "app:sha256"
    assert tag == "abc123def456"

    # URL with path that looks like tag
    repo, tag = parse_image_with_tag("registry.com:8080/path:component/repo")
    assert repo == "registry.com:8080/path:component/repo"
    assert tag is None

    # Empty string
    repo, tag = parse_image_with_tag("")
    assert repo == ""
    assert tag is None


def test_infer_target_repository_name_simple():
    """Test repository name inference from simple paths."""
    assert infer_target_repository_name("nginx") == "nginx"
    assert infer_target_repository_name("postgres") == "postgres"
    assert infer_target_repository_name("redis") == "redis"


def test_infer_target_repository_name_with_registry():
    """Test repository name inference with registry URLs."""
    assert infer_target_repository_name("ghcr.io/fluxcd/helm-controller") == "helm-controller"
    assert infer_target_repository_name("docker.io/library/nginx") == "nginx"
    assert infer_target_repository_name("quay.io/prometheus/node-exporter") == "node-exporter"


def test_infer_target_repository_name_with_ports():
    """Test repository name inference with registry ports."""
    assert infer_target_repository_name("localhost:5000/myapp") == "myapp"
    assert infer_target_repository_name("registry.com:443/team/project") == "project"
    assert infer_target_repository_name("private.registry:8080/org/service") == "service"


def test_infer_target_repository_name_deep_paths():
    """Test repository name inference with deep path hierarchies."""
    assert infer_target_repository_name("registry.com/org/team/project") == "project"
    assert infer_target_repository_name("gcr.io/company/division/team/app") == "app"
    assert infer_target_repository_name("quay.io/very/deep/path/to/repo") == "repo"


def test_validate_image_tag_conflict_no_conflict():
    """Test validation when there's no conflict between tag methods."""
    # No tag in URL, explicit source-tag - OK
    assert validate_image_tag_conflict("nginx", "v1.20") is None

    # No tag in URL, default source-tag - OK
    assert validate_image_tag_conflict("nginx", "latest") is None

    # Tag in URL, no explicit source-tag (None) - OK
    assert validate_image_tag_conflict("nginx:v1.21", None) is None

    # Tag in URL, default explicit source-tag - OK (default doesn't conflict)
    assert validate_image_tag_conflict("nginx:v1.21", "latest") is None


def test_validate_image_tag_conflict_with_conflict():
    """Test validation when there is a conflict between tag methods."""
    # Both tag in URL and explicit non-default source-tag - CONFLICT
    error = validate_image_tag_conflict("nginx:v1.21", "v1.20")
    assert error is not None
    assert "Cannot use both image:tag syntax" in error
    assert "nginx:v1.21" in error
    assert "v1.20" in error
    assert "simultaneously" in error

    # Complex registry URL with conflict
    error = validate_image_tag_conflict("ghcr.io/org/app:v2.0", "v1.5")
    assert error is not None
    assert "ghcr.io/org/app:v2.0" in error
    assert "v1.5" in error


def test_resolve_final_source_tag_priority():
    """Test source tag resolution priority."""
    # Tag from URL takes priority
    assert resolve_final_source_tag("nginx:v1.21", "latest") == "v1.21"
    assert resolve_final_source_tag("nginx:v1.21", "v1.20") == "v1.21"

    # Explicit tag when no URL tag
    assert resolve_final_source_tag("nginx", "v1.20") == "v1.20"
    assert resolve_final_source_tag("redis", "6.2") == "6.2"

    # Default tag when neither specified
    assert resolve_final_source_tag("nginx", "latest") == "latest"


def test_resolve_final_source_tag_complex_cases():
    """Test source tag resolution with complex image URLs."""
    # Registry URLs with tags
    assert resolve_final_source_tag("ghcr.io/org/app:v2.1", "latest") == "v2.1"
    assert resolve_final_source_tag("registry.com:5000/app:prod", "dev") == "prod"

    # Registry URLs without tags
    assert resolve_final_source_tag("ghcr.io/org/app", "v1.0") == "v1.0"
    assert resolve_final_source_tag("localhost:5000/myapp", "staging") == "staging"


def test_integration_workflow():
    """Test the complete workflow for enhanced copy command parsing."""
    # Scenario 1: URL with tag, no explicit source-tag
    image_url = "ghcr.io/fluxcd/helm-controller:v1.3.0"

    # Parse the URL
    repo_without_tag, url_tag = parse_image_with_tag(image_url)
    assert repo_without_tag == "ghcr.io/fluxcd/helm-controller"
    assert url_tag == "v1.3.0"

    # Validate no conflict
    conflict = validate_image_tag_conflict(image_url, "latest")
    assert conflict is None

    # Resolve final tag
    final_tag = resolve_final_source_tag(image_url, "latest")
    assert final_tag == "v1.3.0"

    # Infer target repository
    target_repo = infer_target_repository_name(repo_without_tag)
    assert target_repo == "helm-controller"

    # Scenario 2: URL without tag, explicit source-tag
    image_url = "ghcr.io/fluxcd/helm-controller"

    repo_without_tag, url_tag = parse_image_with_tag(image_url)
    assert repo_without_tag == "ghcr.io/fluxcd/helm-controller"
    assert url_tag is None

    conflict = validate_image_tag_conflict(image_url, "v1.2.0")
    assert conflict is None

    final_tag = resolve_final_source_tag(image_url, "v1.2.0")
    assert final_tag == "v1.2.0"

    target_repo = infer_target_repository_name(repo_without_tag)
    assert target_repo == "helm-controller"