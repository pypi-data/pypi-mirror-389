"""Tests for scan_formatters.py pure helper functions.

Following pure-function-extraction-pattern:
- Test pure business logic with zero mocks
- Test edge cases exhaustively
- Fast execution (no I/O, no async)
"""

from dataclasses import dataclass

import pytest

from ecreshore.cli.cluster.scan_formatters import (
    _build_image_namespace_map,
    _build_image_row_data,
    _format_namespace_list,
    _format_truncated_image_list,
)


# ============================================================================
# Test Fixtures - Minimal dataclass stubs for testing
# ============================================================================


@dataclass
class MockImageRef:
    """Mock ImageReference for testing."""

    image_url: str


@dataclass
class MockWorkload:
    """Mock Workload for testing."""

    namespace: str
    non_ecr_images: list
    name: str = "test-workload"
    workload_type: str = "Deployment"


# ============================================================================
# Tests for _build_image_namespace_map()
# ============================================================================


class TestBuildImageNamespaceMap:
    """Test image-to-namespace mapping builder."""

    def test_single_workload_single_image(self):
        """Test simplest case: one workload, one image."""
        workloads = [
            MockWorkload(
                namespace="prod", non_ecr_images=[MockImageRef("nginx:latest")]
            )
        ]

        result = _build_image_namespace_map(workloads)

        assert result == {"nginx:latest": {"prod"}}

    def test_multiple_workloads_same_image(self):
        """Test same image used across multiple namespaces."""
        workloads = [
            MockWorkload(
                namespace="prod", non_ecr_images=[MockImageRef("nginx:latest")]
            ),
            MockWorkload(
                namespace="staging", non_ecr_images=[MockImageRef("nginx:latest")]
            ),
            MockWorkload(namespace="dev", non_ecr_images=[MockImageRef("nginx:latest")]),
        ]

        result = _build_image_namespace_map(workloads)

        assert result == {"nginx:latest": {"prod", "staging", "dev"}}
        assert len(result["nginx:latest"]) == 3

    def test_multiple_images_per_workload(self):
        """Test workload with multiple non-ECR images."""
        workloads = [
            MockWorkload(
                namespace="prod",
                non_ecr_images=[
                    MockImageRef("nginx:latest"),
                    MockImageRef("redis:7"),
                    MockImageRef("postgres:15"),
                ],
            )
        ]

        result = _build_image_namespace_map(workloads)

        assert result == {
            "nginx:latest": {"prod"},
            "redis:7": {"prod"},
            "postgres:15": {"prod"},
        }

    def test_complex_multi_workload_scenario(self):
        """Test realistic scenario with multiple workloads and images."""
        workloads = [
            MockWorkload(
                namespace="prod",
                non_ecr_images=[
                    MockImageRef("nginx:latest"),
                    MockImageRef("redis:7"),
                ],
            ),
            MockWorkload(
                namespace="staging",
                non_ecr_images=[
                    MockImageRef("nginx:latest"),
                    MockImageRef("postgres:15"),
                ],
            ),
            MockWorkload(
                namespace="dev",
                non_ecr_images=[
                    MockImageRef("nginx:latest"),
                    MockImageRef("redis:7"),
                    MockImageRef("postgres:15"),
                ],
            ),
        ]

        result = _build_image_namespace_map(workloads)

        assert result["nginx:latest"] == {"prod", "staging", "dev"}
        assert result["redis:7"] == {"prod", "dev"}
        assert result["postgres:15"] == {"staging", "dev"}

    def test_empty_workloads_list(self):
        """Test empty input returns empty map."""
        result = _build_image_namespace_map([])
        assert result == {}

    def test_workload_with_no_images(self):
        """Test workload with empty non_ecr_images list."""
        workloads = [MockWorkload(namespace="prod", non_ecr_images=[])]

        result = _build_image_namespace_map(workloads)

        assert result == {}


# ============================================================================
# Tests for _format_namespace_list()
# ============================================================================


class TestFormatNamespaceList:
    """Test namespace list formatter."""

    def test_single_namespace(self):
        """Test formatting single namespace."""
        result = _format_namespace_list({"prod"})
        assert result == "prod"

    def test_multiple_namespaces_sorted(self):
        """Test namespaces are sorted alphabetically."""
        result = _format_namespace_list({"prod", "dev", "staging"})
        assert result == "dev, prod, staging"

    def test_empty_set(self):
        """Test empty set returns empty string."""
        result = _format_namespace_list(set())
        assert result == ""

    def test_many_namespaces(self):
        """Test formatting many namespaces."""
        namespaces = {f"namespace-{i}" for i in range(5)}
        result = _format_namespace_list(namespaces)

        # Should be comma-separated and sorted
        parts = result.split(", ")
        assert len(parts) == 5
        assert parts == sorted(parts)

    def test_special_characters_in_names(self):
        """Test namespaces with special characters."""
        result = _format_namespace_list({"prod-east", "prod-west", "dev-001"})
        assert result == "dev-001, prod-east, prod-west"


# ============================================================================
# Tests for _format_truncated_image_list()
# ============================================================================


class TestFormatTruncatedImageList:
    """Test image list formatter with truncation."""

    def test_empty_list(self):
        """Test empty list returns empty string."""
        result = _format_truncated_image_list([])
        assert result == ""

    def test_single_short_image(self):
        """Test single image under max length."""
        result = _format_truncated_image_list(["nginx:latest"])
        assert result == "nginx:latest"

    def test_multiple_short_images(self):
        """Test multiple images that fit within max length."""
        images = ["nginx:latest", "redis:7"]
        result = _format_truncated_image_list(images)
        assert result == "nginx:latest, redis:7"
        assert len(result) < 50

    def test_truncation_at_exact_boundary(self):
        """Test truncation when string length exceeds max."""
        # Create images that will exceed 50 chars
        images = ["a" * 30, "b" * 30]
        result = _format_truncated_image_list(images, max_length=50)

        assert result.endswith("...")
        assert len(result) == 53  # 50 chars + "..."

    def test_truncation_with_long_single_image(self):
        """Test truncation with single very long image."""
        long_image = "registry.example.com/very/long/path/to/image:v1.2.3"
        result = _format_truncated_image_list([long_image], max_length=20)

        assert result.endswith("...")
        assert len(result) == 23  # 20 + "..."
        assert result.startswith("registry.example.com")

    def test_no_truncation_needed(self):
        """Test that short lists are not truncated."""
        images = ["a", "b", "c"]
        result = _format_truncated_image_list(images, max_length=50)

        assert result == "a, b, c"
        assert "..." not in result

    def test_custom_max_length(self):
        """Test custom max_length parameter."""
        images = ["nginx:latest", "redis:7"]
        result = _format_truncated_image_list(images, max_length=10)

        assert result.endswith("...")
        assert len(result) == 13  # 10 + "..."

    def test_realistic_image_urls(self):
        """Test with realistic Docker image URLs."""
        images = [
            "docker.io/library/nginx:1.21.6",
            "gcr.io/project/app:v1.2.3",
            "registry.hub.docker.com/redis:7-alpine",
        ]
        result = _format_truncated_image_list(images, max_length=50)

        # These should fit (total ~92 chars, but we truncate)
        assert result.endswith("...")
        assert "docker.io" in result

    def test_performance_optimization_short_circuit(self):
        """Test that short estimates avoid building full string."""
        # This should take the fast path (no truncation needed)
        images = ["a", "b", "c"]
        result = _format_truncated_image_list(images, max_length=100)

        assert result == "a, b, c"
        assert "..." not in result


# ============================================================================
# Tests for _build_image_row_data()
# ============================================================================


class TestBuildImageRowData:
    """Test image table row data builder."""

    def test_simple_image_with_tag(self):
        """Test simple image URL with tag."""
        namespace_map = {"nginx:latest": {"prod", "dev"}}

        row_data = _build_image_row_data("nginx:latest", namespace_map)

        assert row_data[0] == "nginx:latest"  # image_url
        assert row_data[1] == "docker.io"  # default registry
        assert row_data[2] == "nginx"  # repository
        assert row_data[3] == "latest"  # tag
        assert "dev" in row_data[4] and "prod" in row_data[4]  # namespaces sorted

    def test_image_with_explicit_registry(self):
        """Test image with explicit registry."""
        namespace_map = {"gcr.io/project/app:v1.0": {"prod"}}

        row_data = _build_image_row_data("gcr.io/project/app:v1.0", namespace_map)

        assert row_data[0] == "gcr.io/project/app:v1.0"
        assert row_data[1] == "gcr.io"  # explicit registry
        assert row_data[2] == "project/app"  # repository with path
        assert row_data[3] == "v1.0"  # tag

    def test_image_not_in_namespace_map(self):
        """Test image URL not present in namespace map."""
        namespace_map = {"nginx:latest": {"prod"}}

        row_data = _build_image_row_data("redis:7", namespace_map)

        assert row_data[0] == "redis:7"
        assert row_data[4] == ""  # no namespaces

    def test_image_with_digest(self):
        """Test image with digest instead of tag."""
        digest = "nginx@sha256:abc123def456"
        namespace_map = {digest: {"prod"}}

        row_data = _build_image_row_data(digest, namespace_map)

        assert row_data[0] == digest
        assert row_data[3] == "@sha256:abc123def456"  # digest includes @ separator

    def test_namespaces_are_sorted(self):
        """Test that namespaces in output are sorted."""
        namespace_map = {"nginx:latest": {"zebra", "alpha", "beta"}}

        row_data = _build_image_row_data("nginx:latest", namespace_map)

        # Namespaces should be sorted: "alpha, beta, zebra"
        assert row_data[4] == "alpha, beta, zebra"

    def test_multiple_namespaces(self):
        """Test formatting multiple namespaces."""
        namespace_map = {
            "nginx:latest": {"prod", "staging", "dev", "qa", "test"}
        }

        row_data = _build_image_row_data("nginx:latest", namespace_map)

        namespaces = row_data[4]
        parts = namespaces.split(", ")
        assert len(parts) == 5
        assert parts == sorted(parts)


# ============================================================================
# Integration Tests - Testing Function Composition
# ============================================================================


class TestHelperFunctionIntegration:
    """Test how helper functions work together."""

    def test_full_workflow_single_namespace(self):
        """Test complete workflow: map → format → row."""
        workloads = [
            MockWorkload(
                namespace="prod",
                non_ecr_images=[
                    MockImageRef("nginx:latest"),
                    MockImageRef("redis:7"),
                ],
            )
        ]

        # Step 1: Build namespace map
        namespace_map = _build_image_namespace_map(workloads)
        assert namespace_map == {"nginx:latest": {"prod"}, "redis:7": {"prod"}}

        # Step 2: Build row data for each image
        nginx_row = _build_image_row_data("nginx:latest", namespace_map)
        redis_row = _build_image_row_data("redis:7", namespace_map)

        assert nginx_row[4] == "prod"
        assert redis_row[4] == "prod"

    def test_full_workflow_multiple_namespaces(self):
        """Test complete workflow with multiple namespaces."""
        workloads = [
            MockWorkload(
                namespace="prod", non_ecr_images=[MockImageRef("nginx:latest")]
            ),
            MockWorkload(
                namespace="staging", non_ecr_images=[MockImageRef("nginx:latest")]
            ),
        ]

        # Build map and verify
        namespace_map = _build_image_namespace_map(workloads)
        row_data = _build_image_row_data("nginx:latest", namespace_map)

        assert row_data[4] == "prod, staging"

    def test_workload_table_truncation_workflow(self):
        """Test image list truncation for workload table."""
        # Simulate workload with many images
        images = [f"image-{i}:latest" for i in range(10)]
        image_refs = [MockImageRef(img) for img in images]

        workload = MockWorkload(namespace="prod", non_ecr_images=image_refs)

        # Extract image URLs and format
        image_urls = [img.image_url for img in workload.non_ecr_images]
        display_text = _format_truncated_image_list(image_urls, max_length=50)

        # Should be truncated
        assert display_text.endswith("...")
        assert len(display_text) == 53
