"""Builder for TransferRequest objects to eliminate duplicate construction patterns."""

from typing import List, Optional
from .transfer_service import TransferRequest
from .batch_config import BatchTransferRequest, BatchSettings
from .platform_models import PlatformResolver


class TransferRequestBuilder:
    """Builder pattern for constructing TransferRequest objects.

    Consolidates the duplicate request building logic found in:
    - batch_processor.py (_execute_single_transfer methods)
    - cli.py (copy command request construction)
    """

    def __init__(self):
        """Initialize empty builder."""
        self._source_image: Optional[str] = None
        self._source_tag: str = "latest"
        self._target_repository: Optional[str] = None
        self._target_tag: Optional[str] = None
        self._verify_digest: bool = True
        self._preserve_architectures: bool = False
        self._target_platforms: Optional[List[str]] = None
        self._auto_detect_architectures: bool = True
        self._skip_if_present: bool = True

    def source(self, image: str, tag: str = "latest") -> "TransferRequestBuilder":
        """Set source image and tag.

        Args:
            image: Source image repository
            tag: Source image tag

        Returns:
            Self for method chaining
        """
        self._source_image = image
        self._source_tag = tag
        return self

    def target(
        self, repository: str, tag: Optional[str] = None
    ) -> "TransferRequestBuilder":
        """Set target repository and optional tag.

        Args:
            repository: Target repository name
            tag: Target tag (defaults to source tag if None)

        Returns:
            Self for method chaining
        """
        self._target_repository = repository
        self._target_tag = tag
        return self

    def verify_digest(self, verify: bool = True) -> "TransferRequestBuilder":
        """Set digest verification.

        Args:
            verify: Whether to verify image digest

        Returns:
            Self for method chaining
        """
        self._verify_digest = verify
        return self

    def preserve_architectures(self, preserve: bool = True) -> "TransferRequestBuilder":
        """Set architecture preservation.

        Args:
            preserve: Whether to preserve all architectures

        Returns:
            Self for method chaining
        """
        self._preserve_architectures = preserve
        return self

    def platforms(
        self, platforms: Optional[List[str]] = None
    ) -> "TransferRequestBuilder":
        """Set target platforms.

        Args:
            platforms: List of target platforms (e.g., ["linux/amd64", "linux/arm64"])

        Returns:
            Self for method chaining
        """
        self._target_platforms = platforms
        return self

    def auto_detect(self, auto_detect: bool = True) -> "TransferRequestBuilder":
        """Set auto-detection of multi-architecture images.

        Args:
            auto_detect: Whether to auto-detect multi-arch images

        Returns:
            Self for method chaining
        """
        self._auto_detect_architectures = auto_detect
        return self

    def skip_if_present(self, skip: bool = True) -> "TransferRequestBuilder":
        """Set skip-if-present behavior.

        Args:
            skip: Whether to skip transfer if image already exists with matching content

        Returns:
            Self for method chaining
        """
        self._skip_if_present = skip
        return self

    def _apply_default_platform_strategy(
        self,
        configured_platforms: Optional[List[str]],
        preserve_arch_flag: Optional[bool],
    ) -> None:
        """Apply unified platform resolution strategy for both CLI and batch.

        This centralizes the logic for determining target_platforms and preserve_architectures
        to ensure DEFAULT_LIMITED_PLATFORMS is consistently applied.

        Strategy:
            1. Explicit platforms specified → use them, enable multi-arch
            2. preserve_arch_flag is False → single platform mode (both None)
            3. preserve_arch_flag is True → use DEFAULT_LIMITED_PLATFORMS
            4. No flags (None) → default to DEFAULT_LIMITED_PLATFORMS with multi-arch

        Args:
            configured_platforms: Explicit platform list (from --platforms or YAML)
            preserve_arch_flag: True (enable multi-arch), False (disable), None (use default)
        """
        if configured_platforms is not None:
            # Priority 1: Explicit platforms specified - use as-is
            self._target_platforms = configured_platforms
            self._preserve_architectures = True
        elif preserve_arch_flag is False:
            # Priority 2: Explicitly disabled multi-arch
            self._target_platforms = None
            self._preserve_architectures = False
        elif preserve_arch_flag is True:
            # Priority 3: Multi-arch enabled, no explicit platforms - use defaults
            self._target_platforms = PlatformResolver.DEFAULT_LIMITED_PLATFORMS
            self._preserve_architectures = True
        else:
            # Priority 4: No flags specified - default to limited multi-arch
            self._target_platforms = PlatformResolver.DEFAULT_LIMITED_PLATFORMS
            self._preserve_architectures = True

    def from_batch_transfer(
        self, batch_transfer: BatchTransferRequest, batch_settings: BatchSettings
    ) -> "TransferRequestBuilder":
        """Populate builder from batch transfer request and settings.

        This consolidates the duplicate logic found in batch_processor.py
        where BatchTransferRequest + BatchSettings are merged into TransferRequest.

        Args:
            batch_transfer: Individual batch transfer request
            batch_settings: Batch-wide settings

        Returns:
            Self for method chaining
        """
        self._source_image = batch_transfer.source
        self._source_tag = batch_transfer.source_tag
        self._target_repository = batch_transfer.target
        self._target_tag = batch_transfer.target_tag

        # Apply defaults from batch settings with override hierarchy
        self._verify_digest = (
            batch_transfer.verify_digest
            if batch_transfer.verify_digest is not None
            else batch_settings.verify_digests
        )

        preserve_arch_setting = (
            batch_transfer.preserve_architectures
            if batch_transfer.preserve_architectures is not None
            else batch_settings.preserve_architectures
        )

        # Handle platform configuration with DEFAULT_LIMITED_PLATFORMS fallback
        configured_platforms = (
            batch_transfer.platforms or batch_settings.target_platforms
        )

        # Apply unified platform strategy (fixes batch bug where DEFAULT_LIMITED_PLATFORMS wasn't applied)
        self._apply_default_platform_strategy(
            configured_platforms, preserve_arch_setting
        )

        return self

    def from_cli_args(
        self,
        source_image: str,
        target_repository: str,
        source_tag: str = "latest",
        target_tag: Optional[str] = None,
        verify_digest: bool = True,
        platforms: Optional[str] = None,
        all_architectures: bool = False,
        no_auto_detect: bool = False,
        force: bool = False,
    ) -> "TransferRequestBuilder":
        """Populate builder from CLI command arguments.

        This consolidates the duplicate logic found in cli.py copy command.

        Args:
            source_image: Source image repository
            target_repository: Target repository name
            source_tag: Source image tag
            target_tag: Target tag (defaults to source_tag if None)
            verify_digest: Whether to verify image digest
            platforms: Comma-separated platform list
            all_architectures: Copy all detected architectures (no platform limits)
            no_auto_detect: Disable auto-detection of multi-arch
            force: Force transfer even if target image exists with matching content

        Returns:
            Self for method chaining
        """
        self._source_image = source_image
        self._source_tag = source_tag
        self._target_repository = target_repository
        self._target_tag = target_tag or source_tag
        self._verify_digest = verify_digest
        self._auto_detect_architectures = not no_auto_detect
        self._skip_if_present = not force  # Force flag disables skip-if-present

        # Handle CLI-specific platform logic using unified strategy
        explicit_platforms = platforms.split(",") if platforms else None

        # Map CLI flags to preserve_arch_flag:
        # - all_architectures=True → None (use all detected, set preserve=True)
        # - explicit platforms → use those platforms
        # - no flags → None (default to DEFAULT_LIMITED_PLATFORMS)
        if all_architectures:
            # Special case: --all-architectures means preserve ALL detected platforms
            self._target_platforms = None
            self._preserve_architectures = True
        else:
            # Apply unified platform strategy for explicit platforms or defaults
            self._apply_default_platform_strategy(
                explicit_platforms, preserve_arch_flag=None
            )

        return self

    def build(self) -> TransferRequest:
        """Build the final TransferRequest object.

        Returns:
            Configured TransferRequest

        Raises:
            ValueError: If required fields are missing
        """
        if not self._source_image:
            raise ValueError("Source image is required")
        if not self._target_repository:
            raise ValueError("Target repository is required")

        # Default target_tag to source_tag if not specified
        target_tag = self._target_tag or self._source_tag

        return TransferRequest(
            source_image=self._source_image,
            source_tag=self._source_tag,
            target_repository=self._target_repository,
            target_tag=target_tag,
            verify_digest=self._verify_digest,
            preserve_architectures=self._preserve_architectures,
            target_platforms=self._target_platforms,
            auto_detect_architectures=self._auto_detect_architectures,
            skip_if_present=self._skip_if_present,
        )

    @classmethod
    def for_batch_transfer(
        cls,
        batch_transfer: BatchTransferRequest,
        batch_settings: BatchSettings,
        force: bool = False,
    ) -> TransferRequest:
        """Convenience method to create TransferRequest from batch components.

        Args:
            batch_transfer: Individual batch transfer request
            batch_settings: Batch-wide settings
            force: If True, disable skip-if-present for this transfer

        Returns:
            Configured TransferRequest
        """
        builder = cls().from_batch_transfer(batch_transfer, batch_settings)
        if force:
            builder.skip_if_present(False)
        return builder.build()

    @classmethod
    def for_cli_copy(
        cls, source_image: str, target_repository: str, **kwargs
    ) -> TransferRequest:
        """Convenience method to create TransferRequest from CLI arguments.

        Args:
            source_image: Source image repository
            target_repository: Target repository name
            **kwargs: Additional CLI arguments

        Returns:
            Configured TransferRequest
        """
        return cls().from_cli_args(source_image, target_repository, **kwargs).build()
