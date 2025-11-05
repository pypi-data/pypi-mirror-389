"""Integration tests for buildx platform limiting with DEFAULT_LIMITED_PLATFORMS.

These tests verify the actual data flow through platform filtering to ensure
DEFAULT_LIMITED_PLATFORMS works correctly.
"""

import pytest

from src.ecreshore.services.platform_models import (
    Platform,
    ImagePlatformInfo,
    PlatformResolver,
)


def test_image_platform_info_stores_platform_digests():
    """Verify ImagePlatformInfo properly stores platform-to-digest mappings."""
    # Create platform info like buildx would return for cert-manager-webhook
    platform_info = ImagePlatformInfo(
        repository="quay.io/jetstack/cert-manager-webhook",
        tag="v1.18.2",
        platforms=[
            Platform(os="linux", architecture="amd64"),
            Platform(os="linux", architecture="arm", variant="v7"),
            Platform(os="linux", architecture="arm64", variant="v8"),
            Platform(os="linux", architecture="ppc64le"),
            Platform(os="linux", architecture="s390x"),
        ],
        manifest_digest="sha256:9431f0d8b510",
        platform_digests={
            "linux/amd64": "sha256:amd64digest",
            "linux/arm/v7": "sha256:armv7digest",
            "linux/arm64/v8": "sha256:arm64digest",
            "linux/ppc64le": "sha256:ppc64digest",
            "linux/s390x": "sha256:s390xdigest",
        },
    )

    # Verify all 5 platforms present
    assert len(platform_info.platforms) == 5
    assert platform_info.is_multiarch is True

    # Verify digest lookup works
    amd64 = Platform(os="linux", architecture="amd64")
    assert platform_info.get_platform_digest(amd64) == "sha256:amd64digest"

    arm64 = Platform(os="linux", architecture="arm64", variant="v8")
    assert platform_info.get_platform_digest(arm64) == "sha256:arm64digest"


def test_filter_platforms_with_default_limited_platforms():
    """Verify filter_platforms limits 5 platforms to DEFAULT_LIMITED_PLATFORMS (2 platforms)."""
    platform_info = ImagePlatformInfo(
        repository="test-repo",
        tag="test-tag",
        platforms=[
            Platform(os="linux", architecture="amd64"),
            Platform(os="linux", architecture="arm", variant="v7"),
            Platform(os="linux", architecture="arm64", variant="v8"),
            Platform(os="linux", architecture="ppc64le"),
            Platform(os="linux", architecture="s390x"),
        ],
        manifest_digest="sha256:manifest",
        platform_digests={
            "linux/amd64": "sha256:digest1",
            "linux/arm/v7": "sha256:digest2",
            "linux/arm64/v8": "sha256:digest3",
            "linux/ppc64le": "sha256:digest4",
            "linux/s390x": "sha256:digest5",
        },
    )

    # Filter using DEFAULT_LIMITED_PLATFORMS
    filtered = platform_info.filter_platforms(PlatformResolver.DEFAULT_LIMITED_PLATFORMS)

    # Should get exactly 2 platforms
    assert len(filtered) == 2, f"Expected 2 platforms, got {len(filtered)}"

    platform_strs = {str(p) for p in filtered}

    # Must include linux/amd64 and linux/arm64
    # Note: DEFAULT_LIMITED_PLATFORMS has "linux/arm64" but source has "linux/arm64/v8"
    # The filter should match on "linux/arm64" prefix
    assert "linux/amd64" in platform_strs
    # Check if arm64 variant made it through
    arm64_found = any("arm64" in p for p in platform_strs)
    assert arm64_found, f"No arm64 platform in filtered results: {platform_strs}"

    # Must NOT include arm/v7, ppc64le, s390x
    assert "linux/arm/v7" not in platform_strs
    assert "linux/ppc64le" not in platform_strs
    assert "linux/s390x" not in platform_strs


def test_default_limited_platforms_constant_value():
    """Verify DEFAULT_LIMITED_PLATFORMS contains exactly linux/amd64 and linux/arm64."""
    assert PlatformResolver.DEFAULT_LIMITED_PLATFORMS == ["linux/amd64", "linux/arm64"]


def test_platform_digest_retrieval_for_filtered_platforms():
    """Verify we can get digests for platforms after filtering.

    This simulates the flow in buildx_transfer_service.py where we:
    1. Filter platforms
    2. Get digests for each filtered platform
    3. Build source@digest references
    """
    platform_info = ImagePlatformInfo(
        repository="nginx",
        tag="alpine",
        platforms=[
            Platform(os="linux", architecture="amd64"),
            Platform(os="linux", architecture="arm", variant="v7"),
            Platform(os="linux", architecture="arm64"),
            Platform(os="linux", architecture="ppc64le"),
        ],
        manifest_digest="sha256:manifest",
        platform_digests={
            "linux/amd64": "sha256:amd64abc123",
            "linux/arm/v7": "sha256:armv7def456",
            "linux/arm64": "sha256:arm64ghi789",
            "linux/ppc64le": "sha256:ppc64jkl012",
        },
    )

    # Filter to DEFAULT_LIMITED_PLATFORMS
    filtered_platforms = platform_info.filter_platforms(["linux/amd64", "linux/arm64"])

    # Should have 2 platforms
    assert len(filtered_platforms) == 2

    # Build digest references (simulating buildx command building)
    source_refs = []
    for platform in filtered_platforms:
        digest = platform_info.get_platform_digest(platform)
        assert digest is not None, f"No digest for platform {platform}"
        source_ref = f"nginx@{digest}"
        source_refs.append(source_ref)

    # Verify we got 2 source refs with digest format
    assert len(source_refs) == 2
    for ref in source_refs:
        assert "@sha256:" in ref, f"Source ref should use @digest format: {ref}"
        assert ":alpine" not in ref, f"Source ref should not use :tag format: {ref}"


def test_platform_string_representation_matches_digest_keys():
    """Verify Platform.__str__() produces keys that match platform_digests dict."""
    # This is critical: the digest dict keys must match Platform string representation
    platform1 = Platform(os="linux", architecture="amd64")
    assert str(platform1) == "linux/amd64"

    platform2 = Platform(os="linux", architecture="arm64", variant="v8")
    assert str(platform2) == "linux/arm64/v8"

    platform3 = Platform(os="linux", architecture="arm", variant="v7")
    assert str(platform3) == "linux/arm/v7"

    # Create platform info and verify lookups work
    platform_info = ImagePlatformInfo(
        repository="test",
        tag="test",
        platforms=[platform1, platform2, platform3],
        manifest_digest="sha256:test",
        platform_digests={
            "linux/amd64": "sha256:digest1",
            "linux/arm64/v8": "sha256:digest2",
            "linux/arm/v7": "sha256:digest3",
        },
    )

    # Verify all lookups work
    assert platform_info.get_platform_digest(platform1) == "sha256:digest1"
    assert platform_info.get_platform_digest(platform2) == "sha256:digest2"
    assert platform_info.get_platform_digest(platform3) == "sha256:digest3"


def test_filter_platforms_returns_platform_objects_not_strings():
    """Verify filter_platforms returns actual Platform objects, not strings.

    This matters because we need to call get_platform_digest(platform) which
    requires Platform objects.
    """
    platform_info = ImagePlatformInfo(
        repository="test",
        tag="test",
        platforms=[
            Platform(os="linux", architecture="amd64"),
            Platform(os="linux", architecture="arm64"),
        ],
        manifest_digest="sha256:test",
        platform_digests={
            "linux/amd64": "sha256:digest1",
            "linux/arm64": "sha256:digest2",
        },
    )

    filtered = platform_info.filter_platforms(["linux/amd64"])

    assert len(filtered) == 1
    assert isinstance(filtered[0], Platform), "filter_platforms must return Platform objects"
    assert filtered[0].architecture == "amd64"

    # Should be able to get digest for filtered platform
    digest = platform_info.get_platform_digest(filtered[0])
    assert digest == "sha256:digest1"


def test_empty_platform_digests_returns_none():
    """Verify get_platform_digest returns None when no digest available."""
    platform_info = ImagePlatformInfo(
        repository="test",
        tag="test",
        platforms=[Platform(os="linux", architecture="amd64")],
        manifest_digest="sha256:test",
        platform_digests={},  # No platform digests
    )

    platform = Platform(os="linux", architecture="amd64")
    assert platform_info.get_platform_digest(platform) is None
