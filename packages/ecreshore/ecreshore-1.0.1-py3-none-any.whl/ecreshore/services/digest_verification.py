"""Enhanced digest verification service with improved reliability."""

import asyncio
import json
import logging
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from ..async_docker_client import AsyncDockerImageClient
from .cache_manager import get_cache
from .cache_service import make_cache_key

logger = logging.getLogger(__name__)


@dataclass
class DigestResult:
    """Result of digest retrieval operation."""

    digest: Optional[str]
    method: str
    registry: Optional[str] = None
    error: Optional[str] = None
    success: bool = False


@dataclass
class PlatformDigestResult:
    """Result of platform-aware digest retrieval operation."""

    platform_digests: Dict[str, str]  # platform -> digest mapping
    method: str
    registry: Optional[str] = None
    error: Optional[str] = None
    success: bool = False

    def get_digest_for_platform(self, platform: str) -> Optional[str]:
        """Get digest for specific platform."""
        return self.platform_digests.get(platform)

    def get_any_digest(self) -> Optional[str]:
        """Get any available digest (for fallback)."""
        if self.platform_digests:
            return next(iter(self.platform_digests.values()))
        return None


class EnhancedDigestVerification:
    """Enhanced digest verification with multiple fallback strategies."""

    def __init__(self, max_retries: int = 3, retry_delay: float = 1.0):
        """Initialize enhanced digest verification.

        Args:
            max_retries: Maximum retry attempts for digest retrieval
            retry_delay: Delay between retry attempts in seconds
        """
        self.max_retries = max_retries
        self.retry_delay = retry_delay

    async def get_content_digest_with_fallback(
        self,
        docker_client: AsyncDockerImageClient,
        repository: str,
        tag: str = "latest",
    ) -> DigestResult:
        """Get content digest using multiple fallback methods.

        Args:
            docker_client: Docker client instance
            repository: Image repository
            tag: Image tag

        Returns:
            DigestResult with digest and metadata
        """
        image_name = f"{repository}:{tag}"

        # Strategy 1: RepoDigests (most reliable for content verification)
        result = await self._get_digest_from_repo_digests(
            docker_client, image_name, repository
        )
        if result.success:
            return result

        # Strategy 2: Image ID (less reliable but available)
        result = await self._get_digest_from_image_id(docker_client, image_name)
        if result.success:
            return result

        # Strategy 3: Buildx registry inspection (for registry-to-registry transfers)
        result = await self._get_digest_from_buildx_inspect(repository, tag)
        if result.success:
            return result

        return DigestResult(
            digest=None,
            method="all_methods_failed",
            error="All digest retrieval methods failed",
        )

    async def _get_digest_from_repo_digests(
        self, docker_client: AsyncDockerImageClient, image_name: str, repository: str
    ) -> DigestResult:
        """Get digest from RepoDigests field (preferred method)."""
        for attempt in range(self.max_retries):
            try:
                logger.debug(
                    f"Attempting RepoDigests retrieval for {image_name} (attempt {attempt + 1})"
                )

                image_data = await docker_client.docker.images.get(image_name)
                repo_digests = image_data.get("RepoDigests", [])

                if not repo_digests:
                    logger.debug(f"No RepoDigests found for {image_name}")
                    if attempt < self.max_retries - 1:
                        await asyncio.sleep(self.retry_delay)
                        continue
                    return DigestResult(
                        digest=None,
                        method="repo_digests",
                        error="No RepoDigests available",
                    )

                # Strategy: Find the most relevant digest
                best_digest = self._select_best_repo_digest(repo_digests, repository)

                if best_digest:
                    # Extract content digest (format: "registry/repo@sha256:digest")
                    if "@sha256:" in best_digest:
                        content_digest = best_digest.split("@")[1]
                        registry = self._extract_registry_from_digest(best_digest)

                        logger.debug(
                            f"Found content digest for {image_name}: {content_digest}"
                        )
                        return DigestResult(
                            digest=content_digest,
                            method="repo_digests",
                            registry=registry,
                            success=True,
                        )

                logger.debug(
                    f"No valid SHA256 digest found in RepoDigests for {image_name}"
                )
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay)

            except Exception as e:
                logger.debug(f"RepoDigests retrieval failed for {image_name}: {e}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay)

        return DigestResult(
            digest=None,
            method="repo_digests",
            error="RepoDigests retrieval failed after retries",
        )

    async def _get_digest_from_image_id(
        self, docker_client: AsyncDockerImageClient, image_name: str
    ) -> DigestResult:
        """Get digest from Image ID field (fallback method)."""
        try:
            logger.debug(f"Attempting Image ID retrieval for {image_name}")

            image_data = await docker_client.docker.images.get(image_name)
            image_id = image_data.get("Id", "")

            if image_id.startswith("sha256:"):
                # Note: This is the image ID, not the content digest
                # Less reliable for cross-registry verification
                logger.debug(f"Using Image ID as digest for {image_name}: {image_id}")
                return DigestResult(digest=image_id, method="image_id", success=True)

            return DigestResult(
                digest=None, method="image_id", error="Image ID not in expected format"
            )

        except Exception as e:
            logger.debug(f"Image ID retrieval failed for {image_name}: {e}")
            return DigestResult(
                digest=None, method="image_id", error=f"Image ID retrieval failed: {e}"
            )

    async def _get_digest_from_buildx_inspect(
        self, repository: str, tag: str
    ) -> DigestResult:
        """Get digest using buildx imagetools inspect (for registry queries)."""
        image_ref = f"{repository}:{tag}"

        for attempt in range(self.max_retries):
            try:
                logger.debug(
                    f"Attempting buildx inspect for {image_ref} (attempt {attempt + 1})"
                )

                # Execute buildx imagetools inspect
                cmd = ["docker", "buildx", "imagetools", "inspect", "--raw", image_ref]

                result = await asyncio.create_subprocess_exec(
                    *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
                )
                stdout, stderr = await result.communicate()

                if result.returncode != 0:
                    error_msg = stderr.decode().strip()
                    logger.debug(f"Buildx inspect failed for {image_ref}: {error_msg}")
                    if attempt < self.max_retries - 1:
                        await asyncio.sleep(self.retry_delay)
                        continue
                    return DigestResult(
                        digest=None,
                        method="buildx_inspect",
                        error=f"Buildx inspect failed: {error_msg}",
                    )

                # Parse JSON manifest
                try:
                    manifest_data = json.loads(stdout.decode())

                    # Handle both single manifest and manifest list formats
                    digest = None

                    if "digest" in manifest_data:
                        # Single manifest
                        digest = manifest_data["digest"]
                    elif "manifests" in manifest_data and manifest_data["manifests"]:
                        # Manifest list - get digest of the first manifest for consistency
                        # In practice, for verification we care about content addressability
                        first_manifest = manifest_data["manifests"][0]
                        if "digest" in first_manifest:
                            digest = first_manifest["digest"]

                    if digest and digest.startswith("sha256:"):
                        logger.debug(
                            f"Found digest via buildx inspect for {image_ref}: {digest}"
                        )
                        return DigestResult(
                            digest=digest,
                            method="buildx_inspect",
                            registry=self._extract_registry_from_repository(repository),
                            success=True,
                        )
                    else:
                        logger.debug(
                            f"No valid digest found in buildx manifest for {image_ref}"
                        )
                        if attempt < self.max_retries - 1:
                            await asyncio.sleep(self.retry_delay)
                            continue

                except json.JSONDecodeError as e:
                    logger.debug(
                        f"Failed to parse buildx manifest for {image_ref}: {e}"
                    )
                    if attempt < self.max_retries - 1:
                        await asyncio.sleep(self.retry_delay)
                        continue

            except FileNotFoundError:
                logger.debug("Docker buildx not found")
                return DigestResult(
                    digest=None,
                    method="buildx_inspect",
                    error="Docker buildx not available",
                )
            except Exception as e:
                logger.debug(f"Buildx inspect error for {image_ref}: {e}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay)
                    continue

        return DigestResult(
            digest=None,
            method="buildx_inspect",
            error="Buildx inspect failed after retries",
        )

    def _extract_registry_from_repository(self, repository: str) -> Optional[str]:
        """Extract registry from repository string."""
        if "/" in repository:
            parts = repository.split("/")
            if len(parts) >= 2 and ("." in parts[0] or ":" in parts[0]):
                return parts[0]
        return "docker.io"

    def _select_best_repo_digest(
        self, repo_digests: List[str], repository: str
    ) -> Optional[str]:
        """Select the most relevant digest from available RepoDigests.

        Priority:
        1. Digest matching the target repository
        2. ECR digest (amazonaws.com)
        3. Any other digest

        Args:
            repo_digests: List of repository digests
            repository: Target repository to match

        Returns:
            Best matching digest or None
        """
        if not repo_digests:
            return None

        # Extract repository name from full path (e.g., "ecr.../my-app" -> "my-app")
        repo_name = repository.split("/")[-1] if "/" in repository else repository

        # Priority 1: Exact repository match
        for digest in repo_digests:
            if digest.startswith(f"{repository}@") or digest.startswith(
                f"{repo_name}@"
            ):
                return digest

        # Priority 2: ECR digest (if pushing to ECR)
        if "amazonaws.com" in repository:
            for digest in repo_digests:
                if "amazonaws.com" in digest:
                    return digest

        # Priority 3: Any digest (fallback)
        return repo_digests[0]

    def _extract_registry_from_digest(self, digest: str) -> Optional[str]:
        """Extract registry from repo digest string."""
        if "@" not in digest:
            return None

        repo_part = digest.split("@")[0]

        if "/" in repo_part:
            # Format: "registry.com/org/repo@digest" -> "registry.com"
            parts = repo_part.split("/")
            if len(parts) >= 2 and ("." in parts[0] or ":" in parts[0]):
                return parts[0]

        # Default to Docker Hub
        return "docker.io"

    async def get_platform_digests_from_buildx(
        self, repository: str, tag: str
    ) -> PlatformDigestResult:
        """Get platform→digest mappings using buildx inspect --raw."""
        image_ref = f"{repository}:{tag}"

        for attempt in range(self.max_retries):
            try:
                logger.debug(
                    f"Attempting platform digest extraction for {image_ref} (attempt {attempt + 1})"
                )

                # Execute buildx imagetools inspect --raw
                cmd = ["docker", "buildx", "imagetools", "inspect", "--raw", image_ref]

                result = await asyncio.create_subprocess_exec(
                    *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
                )
                stdout, stderr = await result.communicate()

                if result.returncode != 0:
                    error_msg = stderr.decode().strip()
                    logger.debug(
                        f"Buildx platform digest extraction failed for {image_ref}: {error_msg}"
                    )
                    if attempt < self.max_retries - 1:
                        await asyncio.sleep(self.retry_delay)
                        continue
                    return PlatformDigestResult(
                        platform_digests={},
                        method="buildx_platform_inspect",
                        error=f"Buildx inspect failed: {error_msg}",
                    )

                # Parse JSON manifest
                try:
                    manifest_data = json.loads(stdout.decode())
                    platform_digests = {}

                    # Handle both single manifest and manifest list formats
                    if "manifests" in manifest_data and manifest_data["manifests"]:
                        # Manifest list - extract platform→digest mappings
                        for manifest in manifest_data["manifests"]:
                            digest = manifest.get("digest")
                            platform_info = manifest.get("platform", {})

                            if digest and platform_info:
                                # Build platform string (e.g., "linux/amd64")
                                os_name = platform_info.get("os", "unknown")
                                arch = platform_info.get("architecture", "unknown")
                                variant = platform_info.get("variant")

                                platform_str = f"{os_name}/{arch}"
                                if variant:
                                    platform_str += f"/{variant}"

                                platform_digests[platform_str] = digest
                                logger.debug(
                                    f"Found platform digest: {platform_str} -> {digest}"
                                )

                    elif "digest" in manifest_data:
                        # Single manifest - use default platform
                        digest = manifest_data["digest"]
                        platform_digests["linux/amd64"] = digest  # Default assumption
                        logger.debug(
                            f"Found single manifest digest: linux/amd64 -> {digest}"
                        )

                    if platform_digests:
                        logger.debug(
                            f"Extracted {len(platform_digests)} platform digests for {image_ref}"
                        )
                        return PlatformDigestResult(
                            platform_digests=platform_digests,
                            method="buildx_platform_inspect",
                            registry=self._extract_registry_from_repository(repository),
                            success=True,
                        )
                    else:
                        logger.debug(
                            f"No platform digests found in manifest for {image_ref}"
                        )
                        if attempt < self.max_retries - 1:
                            await asyncio.sleep(self.retry_delay)
                            continue

                except json.JSONDecodeError as e:
                    logger.debug(
                        f"Failed to parse buildx manifest for {image_ref}: {e}"
                    )
                    if attempt < self.max_retries - 1:
                        await asyncio.sleep(self.retry_delay)
                        continue

            except FileNotFoundError:
                logger.debug("Docker buildx not found")
                return PlatformDigestResult(
                    platform_digests={},
                    method="buildx_platform_inspect",
                    error="Docker buildx not available",
                )
            except Exception as e:
                logger.debug(f"Buildx platform inspect error for {image_ref}: {e}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay)
                    continue

        return PlatformDigestResult(
            platform_digests={},
            method="buildx_platform_inspect",
            error="Platform digest extraction failed after retries",
        )

    async def verify_digests_enhanced(
        self,
        docker_client: AsyncDockerImageClient,
        source_repository: str,
        source_tag: str,
        target_repository: str,
        target_tag: str,
    ) -> Dict[str, Any]:
        """Enhanced digest verification with detailed reporting.

        Returns:
            Dict with verification results and detailed information
        """
        logger.info(
            f"Enhanced digest verification: {source_repository}:{source_tag} vs {target_repository}:{target_tag}"
        )

        # Get source digest
        source_result = await self.get_content_digest_with_fallback(
            docker_client, source_repository, source_tag
        )

        # Get target digest
        target_result = await self.get_content_digest_with_fallback(
            docker_client, target_repository, target_tag
        )

        # Analyze results
        verification_result: Dict[str, Any] = {
            "source_digest": source_result.digest,
            "target_digest": target_result.digest,
            "source_method": source_result.method,
            "target_method": target_result.method,
            "source_registry": source_result.registry,
            "target_registry": target_result.registry,
            "verification_possible": bool(
                source_result.digest and target_result.digest
            ),
            "digests_match": None,
            "verification_quality": None,
            "warnings": [],
        }

        if verification_result["verification_possible"]:
            # Clean digests for comparison (remove sha256: prefix if present)
            source_clean = (
                source_result.digest.replace("sha256:", "")
                if source_result.digest
                else None
            )
            target_clean = (
                target_result.digest.replace("sha256:", "")
                if target_result.digest
                else None
            )

            verification_result["digests_match"] = source_clean == target_clean

            # Assess verification quality
            high_quality_methods = ["repo_digests", "buildx_inspect"]
            medium_quality_methods = ["image_id"]

            if (
                source_result.method in high_quality_methods
                and target_result.method in high_quality_methods
            ):
                verification_result["verification_quality"] = "high"
            elif (
                source_result.method in high_quality_methods + medium_quality_methods
                and target_result.method
                in high_quality_methods + medium_quality_methods
            ):
                verification_result["verification_quality"] = "medium"
                if source_result.method != target_result.method:
                    warnings_list = verification_result["warnings"]
                    if isinstance(warnings_list, list):
                        warnings_list.append(
                            "Using different digest methods for source and target"
                        )
            else:
                verification_result["verification_quality"] = "low"
                warnings_list = verification_result["warnings"]
                if isinstance(warnings_list, list):
                    warnings_list.append("Using fallback digest methods")
        else:
            # Add specific error details
            if not source_result.digest:
                warnings_list = verification_result["warnings"]
                if isinstance(warnings_list, list):
                    warnings_list.append(
                        f"Source digest unavailable: {source_result.error}"
                    )
            if not target_result.digest:
                warnings_list = verification_result["warnings"]
                if isinstance(warnings_list, list):
                    warnings_list.append(
                        f"Target digest unavailable: {target_result.error}"
                    )

        return verification_result


# Convenience function for backward compatibility
async def get_enhanced_digest(
    docker_client: Optional[AsyncDockerImageClient],
    repository: str,
    tag: str = "latest",
) -> Optional[str]:
    """Get image digest using enhanced retrieval methods (with caching).

    This is a drop-in replacement for the existing get_image_digest method.
    Works with or without a docker_client for buildx compatibility.
    """
    # Step 1: Try cache first
    cache = get_cache("image_digests")
    if cache:
        try:
            cache_key = make_cache_key("digest", repository, tag, "enhanced")
            cached_digest = await cache.get(cache_key)
            if cached_digest is not None:
                logger.debug(f"Cache hit for digest: {repository}:{tag}")
                return cached_digest
        except Exception as e:
            # Cache errors should not break functionality
            logger.debug(f"Cache lookup error for digest {repository}:{tag}: {e}")

    # Step 2: Cache miss - compute digest
    verifier = EnhancedDigestVerification()

    if docker_client is None:
        # Buildx-only mode: skip Docker API methods and use buildx inspect directly
        result = await verifier._get_digest_from_buildx_inspect(repository, tag)
        digest = result.digest
    else:
        # Normal mode: use all available methods
        result = await verifier.get_content_digest_with_fallback(
            docker_client, repository, tag
        )
        digest = result.digest

    # Step 3: Cache on success (1hr TTL - digests are immutable)
    if cache and digest:
        try:
            await cache.set(cache_key, digest, ttl=3600)
            logger.debug(f"Cached digest: {repository}:{tag} (TTL=3600s)")
        except Exception as e:
            # Cache errors should not break functionality
            logger.debug(f"Cache store error for digest {repository}:{tag}: {e}")

    return digest


# Platform-aware digest extraction
async def get_platform_digests(
    docker_client: Optional[AsyncDockerImageClient],
    repository: str,
    tag: str = "latest",
) -> PlatformDigestResult:
    """Get platform→digest mappings using enhanced retrieval methods (with caching).

    Args:
        docker_client: Docker client (can be None for buildx-only mode)
        repository: Image repository
        tag: Image tag

    Returns:
        PlatformDigestResult with platform→digest mappings
    """
    # Step 1: Try cache first
    cache = get_cache("image_digests")
    if cache:
        try:
            cache_key = make_cache_key("digest", repository, tag, "platforms")
            cached_mappings = await cache.get(cache_key)
            if cached_mappings is not None:
                logger.debug(f"Cache hit for platform digests: {repository}:{tag}")
                return PlatformDigestResult(
                    platform_digests=cached_mappings,
                    method="cache",
                    success=True
                )
        except Exception as e:
            # Cache errors should not break functionality
            logger.debug(f"Cache lookup error for platform digests {repository}:{tag}: {e}")

    # Step 2: Cache miss - compute platform digests
    verifier = EnhancedDigestVerification()

    if docker_client is None:
        # Buildx-only mode: use buildx platform extraction
        result = await verifier.get_platform_digests_from_buildx(repository, tag)
    else:
        # Try Docker API first, fallback to buildx if needed
        # For now, use buildx platform extraction as it's more reliable for platform info
        result = await verifier.get_platform_digests_from_buildx(repository, tag)

    # Step 3: Cache on success (1hr TTL)
    if cache and result.success:
        try:
            await cache.set(cache_key, result.platform_digests, ttl=3600)
            logger.debug(f"Cached platform digests: {repository}:{tag} (TTL=3600s)")
        except Exception as e:
            # Cache errors should not break functionality
            logger.debug(f"Cache store error for platform digests {repository}:{tag}: {e}")

    return result
