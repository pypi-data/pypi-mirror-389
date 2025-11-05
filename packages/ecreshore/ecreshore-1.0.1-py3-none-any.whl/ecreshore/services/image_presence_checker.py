"""Image presence checking service for skip-if-present functionality."""

import logging
import time
from typing import Optional, Dict, Any
from .ecr_repository import ECRRepositoryService, ECRImage
from .digest_verification import get_enhanced_digest
from ..async_docker_client import AsyncDockerImageClient
from .cache_manager import get_cache
from .cache_service import make_cache_key

logger = logging.getLogger(__name__)

# Import structlog for enhanced skip decision logging
try:
    import structlog

    skip_logger = structlog.get_logger("skip_decisions")
    STRUCTURED_LOGGING_AVAILABLE = True
except ImportError:
    skip_logger = logger
    STRUCTURED_LOGGING_AVAILABLE = False


# Pure functions for digest manipulation (easy to test, no I/O)
def normalize_digest(digest: Optional[str]) -> str:
    """Normalize image digest by removing sha256: prefix.

    This pure function extracts the digest normalization logic for easier testing
    and reuse across the codebase.

    Args:
        digest: Image digest (may have sha256: prefix or be None)

    Returns:
        Normalized digest without prefix, or empty string if None

    Examples:
        >>> normalize_digest("sha256:abc123")
        'abc123'
        >>> normalize_digest("abc123")
        'abc123'
        >>> normalize_digest(None)
        ''
    """
    if not digest:
        return ""
    return digest.replace("sha256:", "")


class ImagePresenceChecker:
    """Service for checking if images already exist in ECR with matching content."""

    def __init__(self, ecr_service: ECRRepositoryService):
        """Initialize image presence checker.

        Args:
            ecr_service: ECR repository service for registry queries
        """
        self.ecr_service = ecr_service

    def _log_skip_decision(
        self,
        source_image: str,
        source_tag: str,
        target_repository: str,
        target_tag: str,
        decision: str,
        reason: str,
        decision_path: list,
        metadata: Dict[str, Any],
        duration_ms: float = None,
    ) -> None:
        """Log structured skip decision event.

        Args:
            source_image: Source image repository
            source_tag: Source image tag
            target_repository: Target ECR repository name
            target_tag: Target image tag
            decision: 'skip' or 'proceed'
            reason: Decision reason code
            decision_path: List of decision steps taken
            metadata: Additional decision metadata
            duration_ms: Decision duration in milliseconds
        """
        import os

        log_data = {
            "event": "skip_decision",
            "source_image": f"{source_image}:{source_tag}",
            "target_image": f"{target_repository}:{target_tag}",
            "decision": decision,
            "reason": reason,
            "decision_path": decision_path,
            "metadata": metadata,
        }

        if duration_ms is not None:
            log_data["duration_ms"] = duration_ms

        # Human-readable output for --explain-skips flag
        if os.getenv("ECRESHORE_EXPLAIN_SKIPS"):
            self._print_human_readable_skip_decision(
                source_image,
                source_tag,
                target_repository,
                target_tag,
                decision,
                reason,
                metadata,
            )

        # Audit trail output for --skip-audit-trail flag
        if os.getenv("ECRESHORE_SKIP_AUDIT_TRAIL"):
            logger.info(
                f"Skip Audit Trail: {' → '.join(decision_path)} → {decision.upper()} ({reason})"
            )

        if STRUCTURED_LOGGING_AVAILABLE and os.getenv("ECRESHORE_DEBUG_SKIP_DECISIONS"):
            skip_logger.info("skip_decision_complete", **log_data)
        else:
            # Standard logging for normal operation or fallback
            logger.info(
                f"Skip Decision: {decision.upper()} - {source_image}:{source_tag} → {target_repository}:{target_tag} "
                f"(reason: {reason}, path: {' → '.join(decision_path)})"
            )

    def _print_human_readable_skip_decision(
        self,
        source_image: str,
        source_tag: str,
        target_repository: str,
        target_tag: str,
        decision: str,
        reason: str,
        metadata: Dict[str, Any],
    ) -> None:
        """Print human-readable skip decision for --explain-skips."""
        from rich.console import Console

        console = Console()

        if decision == "skip":
            icon = "✅"
            color = "green"
            action = "SKIPPED"
        else:
            icon = "🔄"
            color = "yellow"
            action = "TRANSFER"

        # Create human-readable reason
        reason_explanations = {
            "no_target_image": "Target image does not exist in ECR",
            "source_digest_failed": "Cannot retrieve source image digest",
            "digest_match": "Images have identical content",
            "digest_mismatch": "Images have different content",
            "platform_match": "Multi-architecture images match",
            "platform_content_mismatch": "Multi-architecture content differs",
            "skip_determination_failed": "Cannot determine if images match",
        }

        human_reason = reason_explanations.get(reason, reason)

        console.print(
            f"{icon} [{color}]{source_image}:{source_tag} → {target_repository}:{target_tag}[/{color}] - "
            f"[bold {color}]{action}[/bold {color}] ({human_reason})"
        )

    async def check_image_exists_in_ecr(
        self, repository: str, tag: str
    ) -> Optional[ECRImage]:
        """Check if image exists in ECR repository (with caching).

        Args:
            repository: Target ECR repository name
            tag: Target image tag

        Returns:
            ECRImage if exists, None if not found
        """
        # Step 1: Try cache first
        cache = get_cache("image_presence")
        if cache:
            try:
                cache_key = make_cache_key(
                    "presence",
                    self.ecr_service.region_name,
                    self.ecr_service.registry_id or "default",
                    repository,
                    tag
                )

                cached_result = await cache.get(cache_key)
                if cached_result is not None:
                    if cached_result == "NOT_FOUND":
                        logger.debug(f"Cache hit (negative): {repository}:{tag}")
                        return None  # Negative cache hit
                    logger.debug(f"Cache hit (positive): {repository}:{tag}")
                    return cached_result  # Positive cache hit
            except Exception as e:
                # Cache errors should not break functionality
                logger.debug(f"Cache lookup error for {repository}:{tag}: {e}")

        # Step 2: Cache miss - call existing logic
        try:
            logger.debug(
                f"check_image_exists_in_ecr: Checking ECR for {repository}:{tag}"
            )

            # List images in repository with tag filter
            # Use tagged_only=True to skip digest-only platform manifests which don't have tags
            # This prevents pagination issues where the first 10 results are all untagged manifests
            images = self.ecr_service.list_images(
                repository, tag_filter=tag, max_results=100, tagged_only=True
            )

            logger.debug(
                f"check_image_exists_in_ecr: list_images returned {len(images)} images for repository={repository}, tag_filter={tag}"
            )

            # Find exact tag match
            existing_image = None
            for idx, image in enumerate(images):
                logger.debug(
                    f"check_image_exists_in_ecr: Checking image {idx + 1}/{len(images)}: "
                    f"tags={image.image_tags}, digest={image.image_digest[:20]}..., "
                    f"looking_for='{tag}'"
                )

                if tag in image.image_tags:
                    logger.debug(
                        f"check_image_exists_in_ecr: FOUND exact match! {repository}:{tag} "
                        f"with digest {image.image_digest}"
                    )
                    existing_image = image
                    break

            # Step 3: Cache the result
            if cache:
                try:
                    if existing_image:
                        # Positive cache: image exists (5min TTL)
                        await cache.set(cache_key, existing_image, ttl=300)
                        logger.debug(f"Cached (positive): {repository}:{tag} (TTL=300s)")
                    else:
                        # Negative cache: image not found (1min TTL)
                        await cache.set(cache_key, "NOT_FOUND", ttl=60)
                        logger.debug(f"Cached (negative): {repository}:{tag} (TTL=60s)")
                except Exception as e:
                    # Cache errors should not break functionality
                    logger.debug(f"Cache store error for {repository}:{tag}: {e}")

            if not existing_image:
                logger.debug(
                    f"check_image_exists_in_ecr: No exact tag match found. "
                    f"repository={repository}, tag={tag}, images_checked={len(images)}"
                )

            return existing_image

        except Exception as e:
            # Log at debug level to avoid polluting batch operation output
            # The BatchErrorAggregator provides user-facing error summaries
            logger.debug(
                f"check_image_exists_in_ecr: Error checking ECR for {repository}:{tag}: {e}",
                exc_info=True,
            )
            return None

    async def get_target_image_digest(self, repository: str, tag: str) -> Optional[str]:
        """Get digest of existing ECR image.

        Args:
            repository: Target ECR repository name
            tag: Target image tag

        Returns:
            Image digest if found, None otherwise
        """
        # First check if image exists in ECR
        existing_image = await self.check_image_exists_in_ecr(repository, tag)
        if not existing_image:
            return None

        # Return the digest directly from ECR
        logger.debug(f"Found target image digest: {existing_image.image_digest}")
        return existing_image.image_digest

    async def get_target_platform_specific_digest(
        self,
        docker_client: Optional[AsyncDockerImageClient],
        repository: str,
        tag: str,
        existing_image: Optional[ECRImage] = None,
    ) -> Optional[str]:
        """Get digest for ECR target image.

        Simply returns the digest from ECR API. The digest from ECR is authoritative
        and can be directly compared with source digests.

        Args:
            docker_client: Docker client (unused, kept for API compatibility)
            repository: Target ECR repository name
            tag: Target image tag
            existing_image: Optional pre-fetched ECRImage to avoid redundant API calls

        Returns:
            ECR image digest if available, None otherwise
        """
        if not existing_image:
            existing_image = await self.check_image_exists_in_ecr(repository, tag)
            if not existing_image:
                return None

        # Return the digest from ECR - this is authoritative
        logger.debug(f"Using ECR digest for target: {existing_image.image_digest}")
        return existing_image.image_digest

    async def get_target_platform_digests(
        self,
        docker_client: Optional[AsyncDockerImageClient],
        repository: str,
        tag: str,
        existing_image: Optional[ECRImage] = None,
    ) -> Dict[str, str]:
        """Get platform→digest mappings for ECR target image.

        Args:
            docker_client: Docker client (can be None for buildx-only mode)
            repository: Target ECR repository name
            tag: Target image tag
            existing_image: Optional pre-fetched ECRImage to avoid redundant API calls

        Returns:
            Dictionary mapping platform strings to digests
        """
        try:
            # Use provided existing_image if available, otherwise check ECR
            if existing_image is None:
                existing_image = await self.check_image_exists_in_ecr(repository, tag)

            if not existing_image:
                logger.debug(f"Target image {repository}:{tag} does not exist in ECR")
                return {}

            # Build ECR registry URL for buildx inspection
            from ..aws_utils import resolve_aws_region

            region = resolve_aws_region(self.ecr_service.region_name)
            registry_id = (
                self.ecr_service.registry_id or self.ecr_service.ecr_auth.registry_id
            )
            ecr_registry_url = f"{registry_id}.dkr.ecr.{region}.amazonaws.com"
            full_ecr_image = f"{ecr_registry_url}/{repository}"

            logger.debug(
                f"Getting platform digests for ECR target: {full_ecr_image}:{tag}"
            )

            # Use the new platform digest extraction
            from .digest_verification import get_platform_digests

            result = await get_platform_digests(docker_client, full_ecr_image, tag)

            if result.success:
                logger.debug(
                    f"Found {len(result.platform_digests)} platform digests for target image"
                )
                return result.platform_digests
            else:
                logger.debug(
                    f"Failed to get platform digests for target: {result.error}"
                )
                return {}

        except Exception as e:
            logger.debug(
                f"Error getting target platform digests for {repository}:{tag}: {e}"
            )
            return {}

    async def get_source_platform_specific_digest(
        self,
        docker_client: Optional[AsyncDockerImageClient],
        source_image: str,
        source_tag: str,
    ) -> Optional[str]:
        """Get platform-specific digest for source image to enable proper comparison.

        This method mirrors get_target_platform_specific_digest() to ensure
        consistent platform-specific digest retrieval for accurate comparison.

        Args:
            docker_client: Docker client (can be None for buildx-only mode)
            source_image: Source image repository
            source_tag: Source image tag

        Returns:
            Platform-specific digest if available, None otherwise
        """
        try:
            logger.debug(
                f"Attempting to get platform-specific digest for source: {source_image}:{source_tag}"
            )

            # Use platform digest extraction with buildx inspection (same as target method)
            from .digest_verification import get_platform_digests

            result = await get_platform_digests(docker_client, source_image, source_tag)

            if result.success and result.platform_digests:
                # Get the first available platform digest (usually linux/amd64)
                platform_digest = result.get_any_digest()
                if platform_digest:
                    logger.debug(
                        f"Successfully retrieved platform-specific digest for source: {platform_digest}"
                    )
                    return platform_digest
                else:
                    logger.debug(
                        f"Platform digests available but could not extract any digest"
                    )
                    return None
            else:
                logger.debug(f"Platform digest extraction failed: {result.error}")
                # Fallback to enhanced digest verification
                fallback_digest = await get_enhanced_digest(
                    docker_client, source_image, source_tag
                )
                if fallback_digest:
                    logger.debug(f"Using fallback digest for source: {fallback_digest}")
                    return fallback_digest
                return None

        except Exception as e:
            logger.debug(
                f"Error getting platform-specific digest for source {source_image}:{source_tag}: {e}"
            )
            # Final fallback
            return await get_enhanced_digest(docker_client, source_image, source_tag)

    async def get_source_image_digest(
        self,
        docker_client: Optional[AsyncDockerImageClient],
        source_image: str,
        source_tag: str,
    ) -> Optional[str]:
        """Get platform-specific digest of source image using same method as target.

        Args:
            docker_client: Docker client (can be None for buildx-only mode)
            source_image: Source image repository
            source_tag: Source image tag

        Returns:
            Platform-specific source image digest if available, None otherwise
        """
        # Always use platform-specific digest method for consistency with target
        return await self.get_source_platform_specific_digest(
            docker_client, source_image, source_tag
        )

    async def get_source_platform_digests(
        self,
        docker_client: Optional[AsyncDockerImageClient],
        source_image: str,
        source_tag: str,
    ) -> Dict[str, str]:
        """Get platform→digest mappings for source image.

        Args:
            docker_client: Docker client (can be None for buildx-only mode)
            source_image: Source image repository
            source_tag: Source image tag

        Returns:
            Dictionary mapping platform strings to digests
        """
        try:
            logger.debug(
                f"Getting source platform digests: {source_image}:{source_tag}"
            )

            # Use platform digest extraction
            from .digest_verification import get_platform_digests

            result = await get_platform_digests(docker_client, source_image, source_tag)

            if result.success:
                logger.debug(
                    f"Found {len(result.platform_digests)} platform digests for source image"
                )
                return result.platform_digests
            else:
                logger.debug(
                    f"Failed to get platform digests for source: {result.error}"
                )
                return {}

        except Exception as e:
            logger.debug(
                f"Error getting source platform digests for {source_image}:{source_tag}: {e}"
            )
            return {}

    def compare_source_target_digests(
        self, source_digest: str, target_digest: str
    ) -> bool:
        """Compare source and target image digests.

        Args:
            source_digest: Source image digest
            target_digest: Target image digest

        Returns:
            True if digests match (indicating same content)
        """
        if not source_digest or not target_digest:
            return False

        # Use pure function for digest normalization
        source_clean = normalize_digest(source_digest)
        target_clean = normalize_digest(target_digest)

        logger.debug(
            f"Comparing digests - source: {source_clean[:12]}... target: {target_clean[:12]}..."
        )

        return source_clean == target_clean

    def compare_platform_digests(
        self,
        source_platform_digests: Dict[str, str],
        target_platform_digests: Dict[str, str],
    ) -> Dict[str, Any]:
        """Compare platform→digest mappings between source and target.

        Args:
            source_platform_digests: Source platform→digest mapping
            target_platform_digests: Target platform→digest mapping

        Returns:
            Dictionary with comparison results:
                - platforms_match: bool - True if all common platforms have matching digests
                - common_platforms: List[str] - Platforms available in both source and target
                - matching_platforms: List[str] - Platforms with matching digests
                - mismatched_platforms: List[str] - Platforms with different digests
                - source_only_platforms: List[str] - Platforms only in source
                - target_only_platforms: List[str] - Platforms only in target
        """
        result = {
            "platforms_match": False,
            "common_platforms": [],
            "matching_platforms": [],
            "mismatched_platforms": [],
            "source_only_platforms": [],
            "target_only_platforms": [],
        }

        if not source_platform_digests or not target_platform_digests:
            logger.debug(
                "Cannot compare platform digests - one or both mappings are empty"
            )
            return result

        source_platforms = set(source_platform_digests.keys())
        target_platforms = set(target_platform_digests.keys())

        # Find platform relationships
        common_platforms = source_platforms & target_platforms
        source_only = source_platforms - target_platforms
        target_only = target_platforms - source_platforms

        result["common_platforms"] = list(common_platforms)
        result["source_only_platforms"] = list(source_only)
        result["target_only_platforms"] = list(target_only)

        # Compare digests for common platforms
        matching_platforms = []
        mismatched_platforms = []

        for platform in common_platforms:
            source_digest = source_platform_digests[platform]
            target_digest = target_platform_digests[platform]

            if self.compare_source_target_digests(source_digest, target_digest):
                matching_platforms.append(platform)
                logger.debug(f"Platform {platform}: digests match")
            else:
                mismatched_platforms.append(platform)
                logger.debug(
                    f"Platform {platform}: digest mismatch - source: {source_digest[:20]}... target: {target_digest[:20]}..."
                )

        result["matching_platforms"] = matching_platforms
        result["mismatched_platforms"] = mismatched_platforms

        # Determine overall match status
        # All common platforms must have matching digests for platforms_match to be True
        result["platforms_match"] = (
            len(common_platforms) > 0 and len(mismatched_platforms) == 0
        )

        logger.debug(
            f"Platform digest comparison: {len(matching_platforms)} matching, {len(mismatched_platforms)} mismatched, {len(common_platforms)} common platforms"
        )

        return result

    async def _cache_skip_decision(
        self,
        source_image: str,
        source_tag: str,
        target_repository: str,
        target_tag: str,
        result: Dict[str, Any],
    ) -> None:
        """Cache skip decision result (Phase 3B).

        Only caches positive skip decisions (should_skip=True). Never caches
        digest mismatches or platform mismatches to ensure they always trigger
        fresh checks.

        Args:
            source_image: Source image repository
            source_tag: Source image tag
            target_repository: Target ECR repository name
            target_tag: Target image tag
            result: Skip decision result dictionary
        """
        # Only cache positive skip decisions
        if not result.get("should_skip"):
            logger.debug(
                f"Not caching decision (should_skip=False): {source_image}:{source_tag} → {target_repository}:{target_tag}"
            )
            return

        cache = get_cache("skip_decisions")
        if not cache:
            return

        try:
            from .cache_service import hash_params
            source_hash = hash_params(image=source_image, tag=source_tag)
            target_hash = hash_params(
                repository=target_repository,
                tag=target_tag,
                region=self.ecr_service.region_name,
                registry_id=self.ecr_service.registry_id or "default"
            )
            cache_key = make_cache_key("skip_decision", source_hash, target_hash)

            # Cache for 2 minutes (120s) - conservative TTL
            await cache.set(cache_key, result, ttl=120)
            logger.debug(
                f"Cached skip decision: {source_image}:{source_tag} → {target_repository}:{target_tag} (TTL=120s)"
            )
        except Exception as e:
            # Cache errors should not break functionality
            logger.debug(f"Decision cache store error: {e}")

    async def should_skip_transfer(
        self,
        docker_client: Optional[AsyncDockerImageClient],
        source_image: str,
        source_tag: str,
        target_repository: str,
        target_tag: str,
        force_refresh: bool = False,
    ) -> Dict[str, Any]:
        """Determine if transfer should be skipped based on platform-aware image presence and content match.

        Args:
            docker_client: Docker client (can be None for buildx-only mode)
            source_image: Source image repository
            source_tag: Source image tag
            target_repository: Target ECR repository name
            target_tag: Target image tag
            force_refresh: If True, bypass decision cache and force fresh check

        Returns:
            Dict with skip decision and metadata:
                - should_skip: bool
                - reason: str
                - existing_image: ECRImage or None
                - source_digest: str or None (fallback digest)
                - target_digest: str or None (fallback digest)
                - digests_match: bool or None (fallback comparison)
                - source_platform_digests: Dict[str, str] - Source platform→digest mapping
                - target_platform_digests: Dict[str, str] - Target platform→digest mapping
                - platform_comparison: Dict - Platform-aware comparison results
                - cache_hit: bool (optional) - True if result came from cache
        """
        start_time = time.time()
        decision_path = []
        api_calls = []

        # Phase 3B: Try decision cache first (unless force_refresh is set)
        if not force_refresh:
            cache = get_cache("skip_decisions")
            if cache:
                try:
                    # Build cache key from source and target
                    from .cache_service import hash_params
                    source_hash = hash_params(image=source_image, tag=source_tag)
                    target_hash = hash_params(
                        repository=target_repository,
                        tag=target_tag,
                        region=self.ecr_service.region_name,
                        registry_id=self.ecr_service.registry_id or "default"
                    )
                    cache_key = make_cache_key("skip_decision", source_hash, target_hash)

                    cached_result = await cache.get(cache_key)
                    if cached_result is not None:
                        logger.debug(
                            f"Decision cache hit: {source_image}:{source_tag} → {target_repository}:{target_tag}"
                        )
                        # Add cache_hit flag and return cached result
                        cached_result["cache_hit"] = True
                        return cached_result
                except Exception as e:
                    # Cache errors should not break functionality
                    logger.debug(f"Decision cache lookup error: {e}")

        result = {
            "should_skip": False,
            "reason": "",
            "existing_image": None,
            "source_digest": None,
            "target_digest": None,
            "digests_match": None,
            "source_platform_digests": {},
            "target_platform_digests": {},
            "platform_comparison": {},
        }

        logger.info(
            f"Platform-aware skip check: {source_image}:{source_tag} → {target_repository}:{target_tag}"
        )

        # Check if target image exists in ECR
        decision_path.append("ecr_existence_check")
        api_calls.append("ecr:ListImages")
        existing_image = await self.check_image_exists_in_ecr(
            target_repository, target_tag
        )
        result["existing_image"] = existing_image

        if not existing_image:
            decision_path.append("no_target_image")
            result["reason"] = (
                f"Target image {target_repository}:{target_tag} does not exist in ECR"
            )
            logger.debug(result["reason"])

            # Log structured skip decision
            duration_ms = (time.time() - start_time) * 1000
            self._log_skip_decision(
                source_image,
                source_tag,
                target_repository,
                target_tag,
                "proceed",
                "no_target_image",
                decision_path,
                {"api_calls": api_calls, "ecr_check_result": "not_found"},
                duration_ms,
            )
            return result

        # First try ECR API digest comparison (faster, more reliable)
        decision_path.append("digest_comparison")
        logger.debug(
            "Attempting ECR API digest comparison with platform-specific normalization"
        )

        # Get platform-specific digest from ECR target for proper comparison
        api_calls.append(
            "ecr:buildx:inspect" if docker_client else "ecr:buildx:inspect"
        )

        # Log both ECR manifest digest and platform-specific digest for debugging
        ecr_manifest_digest = existing_image.image_digest
        target_digest = await self.get_target_platform_specific_digest(
            docker_client, target_repository, target_tag, existing_image
        )

        logger.debug(f"ECR manifest digest: {ecr_manifest_digest}")
        logger.debug(f"Target platform-specific digest: {target_digest}")

        # Check if we successfully normalized the digest
        if target_digest != ecr_manifest_digest:
            logger.debug(
                "✅ Successfully normalized ECR manifest digest to platform-specific digest"
            )
        else:
            logger.debug(
                "ℹ️ Using ECR manifest digest (normalization not needed or unavailable)"
            )

        api_calls.append("docker:inspect" if docker_client else "buildx:inspect")
        source_digest = await self.get_source_image_digest(
            docker_client, source_image, source_tag
        )

        result["source_digest"] = source_digest
        result["target_digest"] = target_digest

        # If source digest failed, return early with specific error
        if not source_digest:
            decision_path.append("source_digest_failed")
            result["reason"] = (
                f"Could not retrieve source image digest for {source_image}:{source_tag}"
            )
            logger.debug(result["reason"])

            # Log structured skip decision
            duration_ms = (time.time() - start_time) * 1000
            self._log_skip_decision(
                source_image,
                source_tag,
                target_repository,
                target_tag,
                "proceed",
                "source_digest_failed",
                decision_path,
                {
                    "api_calls": api_calls,
                    "target_digest": target_digest,
                    "source_digest": None,
                    "error": "digest_retrieval_failed",
                },
                duration_ms,
            )
            return result

        # If both digests available via ECR API, use direct comparison
        if source_digest and target_digest:
            decision_path.append("ecr_api_comparison")
            digests_match = self.compare_source_target_digests(
                source_digest, target_digest
            )
            result["digests_match"] = digests_match

            duration_ms = (time.time() - start_time) * 1000

            if digests_match:
                decision_path.append("digest_match")
                result["should_skip"] = True
                result["reason"] = (
                    f"Target image {target_repository}:{target_tag} already exists with matching digest (ECR API comparison)"
                )
                logger.info(f"✅ ECR API skip decision: {result['reason']}")

                # Log structured skip decision
                self._log_skip_decision(
                    source_image,
                    source_tag,
                    target_repository,
                    target_tag,
                    "skip",
                    "digest_match",
                    decision_path,
                    {
                        "api_calls": api_calls,
                        "target_digest": target_digest[:20] + "...",
                        "target_ecr_manifest_digest": ecr_manifest_digest[:20] + "...",
                        "source_digest": source_digest[:20] + "...",
                        "comparison_method": "ecr_api_normalized",
                        "digest_normalized": target_digest != ecr_manifest_digest,
                    },
                    duration_ms,
                )

                # Phase 3B: Cache this positive skip decision
                await self._cache_skip_decision(
                    source_image, source_tag, target_repository, target_tag, result
                )
                return result
            else:
                decision_path.append("digest_mismatch")
                result["reason"] = (
                    f"Target image {target_repository}:{target_tag} exists but has different content (ECR API digest mismatch)"
                )
                logger.info(f"🔄 ECR API transfer needed: {result['reason']}")

                # Log structured skip decision
                self._log_skip_decision(
                    source_image,
                    source_tag,
                    target_repository,
                    target_tag,
                    "proceed",
                    "digest_mismatch",
                    decision_path,
                    {
                        "api_calls": api_calls,
                        "target_digest": target_digest[:20] + "...",
                        "target_ecr_manifest_digest": ecr_manifest_digest[:20] + "...",
                        "source_digest": source_digest[:20] + "...",
                        "comparison_method": "ecr_api_normalized",
                        "digest_normalized": target_digest != ecr_manifest_digest,
                    },
                    duration_ms,
                )
                return result

        # Fallback: Try platform-aware comparison for complex cases
        decision_path.append("platform_aware_fallback")
        logger.debug(
            "ECR API comparison insufficient, trying platform digests for multi-arch detection"
        )

        api_calls.extend(["buildx:imagetools_inspect", "buildx:imagetools_inspect"])
        source_platform_digests = await self.get_source_platform_digests(
            docker_client, source_image, source_tag
        )
        target_platform_digests = await self.get_target_platform_digests(
            docker_client, target_repository, target_tag, existing_image
        )

        result["source_platform_digests"] = source_platform_digests
        result["target_platform_digests"] = target_platform_digests

        duration_ms = (time.time() - start_time) * 1000

        # Perform platform-aware comparison
        if source_platform_digests and target_platform_digests:
            decision_path.append("platform_comparison")
            platform_comparison = self.compare_platform_digests(
                source_platform_digests, target_platform_digests
            )
            result["platform_comparison"] = platform_comparison

            if platform_comparison["platforms_match"]:
                decision_path.append("platform_match")
                result["should_skip"] = True
                matching_platforms = platform_comparison["matching_platforms"]
                result["reason"] = (
                    f"Target image {target_repository}:{target_tag} already exists with matching platform digests ({len(matching_platforms)} platforms: {', '.join(matching_platforms)})"
                )
                logger.info(f"✅ Platform-aware skip: {result['reason']}")

                # Log structured skip decision
                self._log_skip_decision(
                    source_image,
                    source_tag,
                    target_repository,
                    target_tag,
                    "skip",
                    "platform_match",
                    decision_path,
                    {
                        "api_calls": api_calls,
                        "comparison_method": "platform_aware",
                        "matching_platforms": matching_platforms,
                        "platform_count": len(matching_platforms),
                    },
                    duration_ms,
                )

                # Phase 3B: Cache this positive skip decision
                await self._cache_skip_decision(
                    source_image, source_tag, target_repository, target_tag, result
                )
                return result
            else:
                decision_path.append("platform_mismatch")
                mismatched_platforms = platform_comparison["mismatched_platforms"]
                common_platforms = platform_comparison["common_platforms"]
                if mismatched_platforms:
                    reason_code = "platform_content_mismatch"
                    result["reason"] = (
                        f"Target image {target_repository}:{target_tag} exists but has different content on platforms: {', '.join(mismatched_platforms)}"
                    )
                elif not common_platforms:
                    reason_code = "no_common_platforms"
                    result["reason"] = (
                        f"Target image {target_repository}:{target_tag} exists but has no common platforms with source"
                    )
                else:
                    reason_code = "platform_comparison_failed"
                    result["reason"] = (
                        f"Target image {target_repository}:{target_tag} exists but platform comparison failed"
                    )
                logger.info(f"🔄 Platform-aware transfer needed: {result['reason']}")

                # Log structured skip decision
                self._log_skip_decision(
                    source_image,
                    source_tag,
                    target_repository,
                    target_tag,
                    "proceed",
                    reason_code,
                    decision_path,
                    {
                        "api_calls": api_calls,
                        "comparison_method": "platform_aware",
                        "mismatched_platforms": mismatched_platforms,
                        "common_platforms": list(common_platforms),
                    },
                    duration_ms,
                )
                return result

        # If platform-aware comparison also fails, we've already tried ECR API comparison above
        # No further fallback needed - the ECR API comparison is the most reliable approach
        decision_path.append("fallback_exhausted")
        logger.debug(
            "Platform digests unavailable, ECR API comparison was already attempted"
        )

        result["reason"] = (
            f"Could not determine if transfer should be skipped for {target_repository}:{target_tag} - proceeding with transfer"
        )
        logger.info(f"🔄 Proceeding with transfer: {result['reason']}")

        # Log final structured skip decision
        self._log_skip_decision(
            source_image,
            source_tag,
            target_repository,
            target_tag,
            "proceed",
            "skip_determination_failed",
            decision_path,
            {
                "api_calls": api_calls,
                "error": "could_not_determine_skip_condition",
                "source_platform_count": len(source_platform_digests),
                "target_platform_count": len(target_platform_digests),
            },
            duration_ms,
        )
        return result


# Convenience functions for backward compatibility and simple use cases
async def check_image_exists_in_ecr(
    ecr_service: ECRRepositoryService, repository: str, tag: str
) -> Optional[ECRImage]:
    """Convenience function to check if image exists in ECR.

    Args:
        ecr_service: ECR repository service
        repository: Target ECR repository name
        tag: Target image tag

    Returns:
        ECRImage if exists, None if not found
    """
    checker = ImagePresenceChecker(ecr_service)
    return await checker.check_image_exists_in_ecr(repository, tag)


async def should_skip_transfer(
    ecr_service: ECRRepositoryService,
    docker_client: Optional[AsyncDockerImageClient],
    source_image: str,
    source_tag: str,
    target_repository: str,
    target_tag: str,
) -> Dict[str, Any]:
    """Convenience function to determine if transfer should be skipped.

    Args:
        ecr_service: ECR repository service
        docker_client: Docker client (can be None for buildx-only mode)
        source_image: Source image repository
        source_tag: Source image tag
        target_repository: Target ECR repository name
        target_tag: Target image tag

    Returns:
        Skip decision dictionary (see ImagePresenceChecker.should_skip_transfer)
    """
    checker = ImagePresenceChecker(ecr_service)
    return await checker.should_skip_transfer(
        docker_client, source_image, source_tag, target_repository, target_tag
    )
