"""Platform models for multi-architecture image support."""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Tuple


@dataclass
class Platform:
    """Container image platform specification."""

    os: str
    architecture: str
    variant: Optional[str] = None
    os_version: Optional[str] = None

    def __str__(self) -> str:
        """String representation in standard format."""
        base = f"{self.os}/{self.architecture}"
        if self.variant:
            base += f"/{self.variant}"
        return base

    @classmethod
    def parse(cls, platform_dict: Dict[str, Any]) -> "Platform":
        """Parse platform from buildx manifest entry."""
        return cls(
            os=platform_dict.get("os", "unknown"),
            architecture=platform_dict.get("architecture", "unknown"),
            variant=platform_dict.get("variant"),
            os_version=platform_dict.get("os.version"),
        )


@dataclass
class PlatformDigest:
    """Pairs a platform with its specific manifest digest."""

    platform: Platform
    digest: str

    def __str__(self) -> str:
        """String representation showing platform and digest."""
        return f"{self.platform} -> {self.digest[:12]}"


@dataclass
class ImagePlatformInfo:
    """Complete platform information for a container image."""

    repository: str
    tag: str
    platforms: List[Platform]
    manifest_digest: str
    platform_digests: Dict[str, str] = field(
        default_factory=dict
    )  # platform_str -> digest
    is_multiarch: bool = field(init=False)

    def __post_init__(self):
        """Calculate derived fields."""
        # Filter out unknown platforms and check if multi-arch
        valid_platforms = [p for p in self.platforms if p.architecture != "unknown"]
        self.platforms = valid_platforms
        self.is_multiarch = len(valid_platforms) > 1

    def get_platform_count(self) -> int:
        """Get number of valid platforms."""
        return len(self.platforms)

    def has_platform(self, target_platform: str) -> bool:
        """Check if specific platform is available."""
        return any(str(p) == target_platform for p in self.platforms)

    def filter_platforms(self, target_platforms: Optional[List[str]]) -> List[Platform]:
        """Filter platforms by target list.

        Handles platform variants intelligently: if target has "linux/arm64",
        it matches both "linux/arm64" and "linux/arm64/v8".
        """
        if not target_platforms:
            return self.platforms

        filtered = []
        for platform in self.platforms:
            platform_str = str(platform)
            # Check exact match first
            if platform_str in target_platforms:
                filtered.append(platform)
                continue

            # Check if any target platform is a prefix (for variant matching)
            # e.g., "linux/arm64" matches "linux/arm64/v8"
            for target in target_platforms:
                if platform_str.startswith(target + "/"):
                    filtered.append(platform)
                    break

        return filtered

    def get_platform_digest(self, platform: Platform) -> Optional[str]:
        """Get digest for specific platform."""
        return self.platform_digests.get(str(platform))


class BuildxError(Exception):
    """Raised when buildx operations fail."""

    def __init__(
        self,
        message: str,
        command: Optional[List[str]] = None,
        stderr: Optional[str] = None,
    ):
        super().__init__(message)
        self.command = command or []
        self.stderr = stderr or ""


class PlatformResolver:
    """Centralized platform resolution logic for consistent architecture handling."""

    DEFAULT_LIMITED_PLATFORMS = ["linux/amd64", "linux/arm64"]

    @staticmethod
    def resolve_target_platforms(
        detected_platforms: Optional[List[str]] = None,
        all_architectures: bool = False,
        explicit_platforms: Optional[List[str]] = None,
        use_defaults_when_none: bool = True,
    ) -> Optional[List[str]]:
        """Resolve which platforms to target based on user preferences and detection.

        This function consolidates all platform decision logic to ensure consistent
        behavior across copy and batch commands.

        Args:
            detected_platforms: Platforms detected from source image
            all_architectures: True if --all-architectures flag was used
            explicit_platforms: User-specified platforms via --platforms
            use_defaults_when_none: Use default limited platforms when no specific choice made

        Returns:
            List of platform strings to target, or None to preserve all detected platforms

        Logic:
            1. Explicit platforms (--platforms): Return as-is, no filtering
            2. All architectures (--all-architectures): Return None (preserve all detected)
            3. Auto-detection with defaults: Limit detected platforms to DEFAULT_LIMITED_PLATFORMS
            4. No detection, use defaults: Return DEFAULT_LIMITED_PLATFORMS if use_defaults_when_none=True
        """
        # Priority 1: Explicit user-specified platforms (highest precedence)
        if explicit_platforms is not None:
            return explicit_platforms

        # Priority 2: All architectures flag (preserve all detected, no limits)
        if all_architectures:
            return None  # None means "use all detected platforms"

        # Priority 3: Auto-detection with default limiting
        if detected_platforms is not None:
            # Filter detected platforms to only include our default supported ones
            limited_platforms = [
                p
                for p in detected_platforms
                if p in PlatformResolver.DEFAULT_LIMITED_PLATFORMS
            ]
            return (
                limited_platforms
                if limited_platforms
                else PlatformResolver.DEFAULT_LIMITED_PLATFORMS
            )

        # Priority 4: Fallback to defaults when no detection available
        if use_defaults_when_none:
            return PlatformResolver.DEFAULT_LIMITED_PLATFORMS

        return None
