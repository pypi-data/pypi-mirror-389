"""Hybrid transfer service that chooses between buildx and standard Docker API."""

import logging
from typing import Optional, Dict, Any

from .async_transfer_service import AsyncTransferService
from .buildx_transfer_service import BuildxTransferService
from .ecr_repository import ECRRepositoryService
from .image_presence_checker import ImagePresenceChecker
from .platform_models import BuildxError, ImagePlatformInfo, PlatformResolver
from .transfer_service import TransferRequest, TransferResult

logger = logging.getLogger(__name__)


class HybridTransferService:
    """Transfer service that chooses between buildx and standard Docker API based on request."""

    def __init__(
        self,
        region_name: Optional[str] = None,
        registry_id: Optional[str] = None,
    ):
        """Initialize hybrid transfer service.

        Args:
            region_name: AWS region for ECR registry
            registry_id: AWS account ID for ECR registry
        """
        self.buildx_service = BuildxTransferService(region_name, registry_id)
        self.async_service = AsyncTransferService(region_name, registry_id)
        self.ecr_service = ECRRepositoryService(region_name, registry_id)
        self._buildx_available: Optional[bool] = None

    async def transfer_image(self, request: TransferRequest) -> TransferResult:
        """Transfer image using appropriate service based on request with smart auto-detection."""

        # Pre-transfer check: Skip if present (unless force flag is used)
        if request.skip_if_present:
            logger.info(
                f"Checking if transfer should be skipped: {request.target_repository}:{request.target_tag}"
            )

            try:
                # Initialize image presence checker
                presence_checker = ImagePresenceChecker(self.ecr_service)

                # Use Docker client for more reliable skip-if-present checks
                from ..async_docker_client import AsyncDockerImageClient

                async with AsyncDockerImageClient() as docker_client:
                    # Check if we should skip the transfer
                    skip_decision = await presence_checker.should_skip_transfer(
                        docker_client=docker_client,  # Use Docker API for reliable source digest
                        source_image=request.source_image,
                        source_tag=request.source_tag,
                        target_repository=request.target_repository,
                        target_tag=request.target_tag,
                    )

                if skip_decision["should_skip"]:
                    logger.info(f"‥  Skipping transfer: {skip_decision['reason']}")

                    # Return skipped result
                    return TransferResult(
                        request=request,
                        success=True,  # Skipping is considered success
                        skipped=True,
                        skip_reason=skip_decision["reason"],
                        source_digest=skip_decision.get("source_digest"),
                        target_digest=skip_decision.get("target_digest"),
                        transfer_method="skipped",
                    )
                else:
                    logger.info(
                        f"🔄 Proceeding with transfer: {skip_decision['reason']}"
                    )

            except Exception as e:
                logger.warning(
                    f"Skip-if-present check failed, proceeding with transfer: {e}"
                )
                # Continue with transfer if presence check fails

        # Check if we should auto-detect multi-arch images
        auto_detected_multi_arch = False
        if (
            not request.preserve_architectures
            and request.auto_detect_architectures
            and await self._is_buildx_available()
        ):
            # Auto-detect if source image is multi-architecture
            platform_info = await self.inspect_image_platforms(
                request.source_image, request.source_tag
            )

            if platform_info and platform_info.is_multiarch:
                auto_detected_multi_arch = True
                detected_platforms = [str(p) for p in platform_info.platforms]
                logger.info(
                    f"🔍 Auto-detected multi-architecture image with {len(platform_info.platforms)} platforms: "
                    f"{', '.join(detected_platforms)}"
                )

                # Determine final target platforms based on request configuration
                if request.target_platforms is None:
                    # --all-architectures case: preserve all detected platforms
                    logger.info(
                        "✅ Preserving all detected architectures (--all-architectures)"
                    )
                    final_platforms = None
                elif (
                    request.target_platforms
                    == PlatformResolver.DEFAULT_LIMITED_PLATFORMS
                ):
                    # Default case: limit to supported platforms that are actually detected
                    available_defaults = [
                        p
                        for p in detected_platforms
                        if p in PlatformResolver.DEFAULT_LIMITED_PLATFORMS
                    ]
                    if available_defaults:
                        logger.info(
                            f"✅ Limiting to detected supported architectures: {', '.join(available_defaults)} ({len(available_defaults)}/{len(detected_platforms)} platforms)"
                        )
                        final_platforms = available_defaults
                    else:
                        logger.info(
                            f"⚠️  No supported architectures detected, copying all: {', '.join(detected_platforms)}"
                        )
                        final_platforms = None  # Fallback to all detected if none of our defaults are available
                else:
                    # Explicit --platforms case: use exactly what user specified
                    logger.info(
                        f"✅ Using explicitly specified platforms: {', '.join(request.target_platforms)}"
                    )
                    final_platforms = request.target_platforms

                # Create enhanced request with resolved platform targeting
                enhanced_request = TransferRequest(
                    source_image=request.source_image,
                    source_tag=request.source_tag,
                    target_repository=request.target_repository,
                    target_tag=request.target_tag,
                    verify_digest=request.verify_digest,
                    preserve_architectures=True,  # Auto-enable for detected multi-arch
                    target_platforms=final_platforms,
                    auto_detect_architectures=request.auto_detect_architectures,
                )

                return await self.buildx_service.transfer_image(enhanced_request)
            elif platform_info and not platform_info.is_multiarch:
                logger.debug(
                    f"Single-architecture image detected: {', '.join(str(p) for p in platform_info.platforms)}"
                )
        elif (
            not request.preserve_architectures and not request.auto_detect_architectures
        ):
            # Auto-detection disabled but check if we're potentially losing architectures
            if await self._is_buildx_available():
                platform_info = await self.inspect_image_platforms(
                    request.source_image, request.source_tag
                )
                if platform_info and platform_info.is_multiarch:
                    logger.warning(
                        f"⚠️  Multi-architecture image detected with {len(platform_info.platforms)} platforms "
                        f"({', '.join(str(p) for p in platform_info.platforms)}), but only {platform_info.platforms[0]} "
                        f"will be transferred. Use --preserve-architectures to copy all architectures."
                    )

        if request.preserve_architectures or auto_detected_multi_arch:
            # Multi-arch requested or auto-detected - try buildx first
            if await self._is_buildx_available():
                logger.debug("Using buildx for multi-arch transfer")
                return await self.buildx_service.transfer_image(request)
            else:
                # Buildx not available - log warning and fallback
                logger.warning(
                    "Multi-arch requested but buildx unavailable, falling back to single-arch transfer"
                )
                # Create fallback request without multi-arch flags
                fallback_request = TransferRequest(
                    source_image=request.source_image,
                    source_tag=request.source_tag,
                    target_repository=request.target_repository,
                    target_tag=request.target_tag,
                    verify_digest=request.verify_digest,
                    preserve_architectures=False,
                    target_platforms=None,
                )
                return await self.async_service.transfer_image(fallback_request)
        else:
            # Single-arch transfer - use existing async service
            logger.debug("Using async service for single-arch transfer")
            return await self.async_service.transfer_image(request)

    async def inspect_image_platforms(
        self, repository: str, tag: str
    ) -> Optional[ImagePlatformInfo]:
        """Inspect image platforms if buildx is available."""
        if await self._is_buildx_available():
            try:
                return await self.buildx_service.inspect_image_platforms(
                    repository, tag
                )
            except BuildxError as e:
                logger.warning(f"Failed to inspect image platforms: {e}")
                return None
        else:
            logger.debug("Buildx not available for platform inspection")
            return None

    def validate_prerequisites(self) -> bool:
        """Validate prerequisites for transfer operations."""
        # Always validate async service (required for fallback)
        async_valid = self.async_service.validate_prerequisites()

        # Buildx validation is optional
        try:
            buildx_valid = self.buildx_service.validate_prerequisites()
            logger.debug(
                f"Prerequisites validation - async: {async_valid}, buildx: {buildx_valid}"
            )
        except Exception as e:
            logger.debug(f"Buildx prerequisites check failed: {e}")
            buildx_valid = False

        return async_valid

    def get_ecr_registry_url(self) -> str:
        """Get ECR registry URL."""
        return self.async_service.get_ecr_registry_url()

    async def _is_buildx_available(self) -> bool:
        """Check buildx availability with caching."""
        if self._buildx_available is None:
            try:
                self._buildx_available = await self.buildx_service.has_buildx_support()
                logger.debug(f"Buildx availability cached: {self._buildx_available}")
            except Exception as e:
                logger.debug(f"Buildx availability check failed: {e}")
                self._buildx_available = False

        return self._buildx_available

    async def copy_image_enhanced(self, request: TransferRequest) -> dict:
        """Execute enhanced image copy operation with comprehensive result data.

        This method contains the pure business logic for enhanced image copying,
        separated from UI concerns for testability.

        Args:
            request: Transfer request with all parameters

        Returns:
            Dict containing:
                - prerequisites_valid: bool
                - ecr_registry_url: str (if prerequisites valid)
                - platform_info: ImagePlatformInfo or None (if multi-arch)
                - transfer_result: TransferResult (if transfer attempted)
                - error_message: str (if prerequisites failed)
        """
        result: Dict[str, Any] = {
            "prerequisites_valid": False,
            "ecr_registry_url": None,
            "platform_info": None,
            "transfer_result": None,
            "error_message": None,
        }

        # Validate prerequisites
        if not self.validate_prerequisites():
            result["error_message"] = "Prerequisites validation failed"
            return result

        result["prerequisites_valid"] = True
        result["ecr_registry_url"] = self.get_ecr_registry_url()

        # Inspect platforms if multi-arch is requested
        if request.preserve_architectures:
            try:
                platform_info = await self.inspect_image_platforms(
                    request.source_image, request.source_tag
                )
                result["platform_info"] = platform_info
            except Exception as e:
                logger.debug(f"Platform inspection failed: {e}")
                # Continue with transfer even if platform inspection fails

        # Execute transfer
        transfer_result = await self.transfer_image(request)
        result["transfer_result"] = transfer_result

        return result
