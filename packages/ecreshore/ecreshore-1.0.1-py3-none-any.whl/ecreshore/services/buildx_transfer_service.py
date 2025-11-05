"""Transfer service using Docker Buildx for multi-architecture support."""

import asyncio
import json
import logging
import re
from typing import List, Optional, Dict

from .base_service import BaseECRService
from .platform_models import BuildxError, ImagePlatformInfo, Platform
from .transfer_service import TransferRequest, TransferResult

logger = logging.getLogger(__name__)


class BuildxTransferService(BaseECRService):
    """Transfer service using Docker Buildx imagetools for multi-architecture support."""

    def __init__(
        self,
        region_name: Optional[str] = None,
        registry_id: Optional[str] = None,
    ):
        """Initialize buildx transfer service.

        Args:
            region_name: AWS region for ECR registry
            registry_id: AWS account ID for ECR registry
        """
        super().__init__(region_name, registry_id)
        self._buildx_available: Optional[bool] = None

    async def has_buildx_support(self) -> bool:
        """Check if docker buildx imagetools is available."""
        if self._buildx_available is not None:
            return self._buildx_available

        try:
            result = await asyncio.create_subprocess_exec(
                "docker",
                "buildx",
                "imagetools",
                "--help",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            returncode = await result.wait()
            self._buildx_available = returncode == 0
            logger.debug(f"Buildx availability check: {self._buildx_available}")
            return self._buildx_available
        except FileNotFoundError:
            logger.debug("Docker buildx not found")
            self._buildx_available = False
            return False

    async def inspect_image_platforms(
        self, repository: str, tag: str
    ) -> ImagePlatformInfo:
        """Get platform information for an image using buildx inspect."""
        cmd = [
            "docker",
            "buildx",
            "imagetools",
            "inspect",
            f"{repository}:{tag}",
            "--format",
            "{{json .Manifest}}",
        ]

        try:
            result = await asyncio.create_subprocess_exec(
                *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await result.communicate()

            if result.returncode != 0:
                error_msg = stderr.decode().strip()
                raise BuildxError(
                    f"Failed to inspect {repository}:{tag}: {error_msg}",
                    command=cmd,
                    stderr=error_msg,
                )

            manifest = json.loads(stdout.decode())
            platforms, platform_digests = self._parse_platforms_from_manifest(manifest)

            return ImagePlatformInfo(
                repository=repository,
                tag=tag,
                platforms=platforms,
                manifest_digest=manifest.get("digest", ""),
                platform_digests=platform_digests,
            )

        except json.JSONDecodeError as e:
            raise BuildxError(
                f"Failed to parse buildx inspect output for {repository}:{tag}: {e}",
                command=cmd,
            ) from e
        except FileNotFoundError as e:
            raise BuildxError(
                "Docker buildx not found - install Docker Buildx", command=cmd
            ) from e

    def _parse_platforms_from_manifest(
        self, manifest: dict
    ) -> tuple[List[Platform], Dict[str, str]]:
        """Parse platform information and digests from buildx manifest.

        Returns:
            Tuple of (platforms list, platform_digests dict mapping platform_str -> digest)
        """
        platforms = []
        platform_digests = {}

        manifests_list = manifest.get("manifests", [])
        for manifest_entry in manifests_list:
            if "platform" in manifest_entry:
                platform = Platform.parse(manifest_entry["platform"])
                platforms.append(platform)

                # Extract digest for this platform
                digest = manifest_entry.get("digest", "")
                if digest:
                    platform_digests[str(platform)] = digest

        logger.debug(f"Parsed {len(platforms)} platforms with digests from manifest")
        return platforms, platform_digests

    def _extract_clean_error_message(self, stderr_output: str) -> str:
        """Extract clean, user-friendly error message from buildx stderr output.

        Args:
            stderr_output: Raw stderr output from buildx command

        Returns:
            Clean error message suitable for user display
        """
        if not stderr_output:
            return "Unknown buildx error"

        # Common buildx error patterns to extract
        error_patterns = [
            # ECR repository not found (most specific first)
            r"The repository with name '([^']+)' does not exist",
            r"unexpected status from POST request.*404 Not Found",
            # Authentication errors
            r"unauthorized: authentication required",
            r"denied:.*?permission",
            # Network/connectivity errors
            r"connection refused",
            r"timeout",
            r"no such host",
            # Generic error patterns
            r"ERROR:\s*(.+)",
            r"error:\s*(.+)",
        ]

        # Try to extract meaningful error from patterns
        for pattern in error_patterns:
            match = re.search(pattern, stderr_output, re.IGNORECASE | re.DOTALL)
            if match:
                if "repository with name" in pattern and match.groups():
                    repo_name = match.group(1)
                    return f"ECR repository '{repo_name}' does not exist in registry"
                elif "404 Not Found" in pattern:
                    return "ECR repository does not exist"
                elif match.groups():
                    return match.group(1).strip()
                else:
                    return match.group(0).strip()

        # If no patterns match, try to extract the last meaningful line
        lines = [line.strip() for line in stderr_output.split("\n") if line.strip()]

        # Filter out buildx progress lines and technical details
        meaningful_lines = [
            line
            for line in lines
            if not any(
                skip in line.lower()
                for skip in ["#", "copying", "sha256:", "------", "pushing", "pulling"]
            )
        ]

        if meaningful_lines:
            # Return the last meaningful line, which is usually the actual error
            error_line = meaningful_lines[-1]
            # Clean up common prefixes
            for prefix in ["error:", "ERROR:", "unknown:"]:
                if error_line.lower().startswith(prefix.lower()):
                    error_line = error_line[len(prefix) :].strip()
            return error_line

        # Fallback: return first few lines without technical details
        clean_lines = [line for line in lines[:3] if not line.startswith("#")]
        return " ".join(clean_lines) if clean_lines else "Buildx transfer failed"

    def validate_prerequisites(self) -> bool:
        """Validate that buildx and ECR access are working."""
        # Use base class ECR validation, but could be extended for buildx-specific checks
        return super().validate_prerequisites()

    async def transfer_image(self, request: TransferRequest) -> TransferResult:
        """Transfer image using buildx imagetools create."""
        if not request.preserve_architectures:
            raise BuildxError(
                "BuildxTransferService requires preserve_architectures=True"
            )

        logger.info(
            f"Starting buildx transfer: {request.source_image}:{request.source_tag} -> {request.target_repository}:{request.target_tag}"
        )

        try:
            # 1. Inspect source platforms
            platform_info = await self.inspect_image_platforms(
                request.source_image, request.source_tag
            )

            logger.info(f"Source image has {len(platform_info.platforms)} platforms")

            # 2. Filter platforms if specified
            target_platforms = platform_info.filter_platforms(request.target_platforms)

            if request.target_platforms and not target_platforms:
                return TransferResult(
                    request=request,
                    success=False,
                    error_message=f"No matching platforms found for {request.target_platforms}",
                    transfer_method="buildx",
                )

            # 3. Build platform-specific source references using digests
            source_refs = []
            if target_platforms:
                # Use digest-based refs to limit to specific platforms
                for platform in target_platforms:
                    digest = platform_info.get_platform_digest(platform)
                    if digest:
                        source_ref = f"{request.source_image}@{digest}"
                        source_refs.append(source_ref)
                        logger.debug(
                            f"Adding platform {platform} with digest {digest[:16]}..."
                        )
                    else:
                        logger.warning(
                            f"No digest found for platform {platform}, skipping"
                        )

            if not source_refs:
                # Fallback: use tag-based reference if no digests available
                logger.warning(
                    "No platform-specific digests available, using tag-based reference"
                )
                source_refs = [f"{request.source_image}:{request.source_tag}"]

            logger.info(
                f"Transferring {len(source_refs)} platform(s): {[str(p) for p in target_platforms]}"
            )

            # 4. Build target registry URL
            ecr_registry_url = self.get_ecr_registry_url()
            target_ref = (
                f"{ecr_registry_url}/{request.target_repository}:{request.target_tag}"
            )

            # 5. Authenticate Docker with ECR registry (required for buildx)
            try:
                username, password = self.ecr_auth.get_docker_credentials()

                # Run docker login for ECR registry
                login_cmd = [
                    "docker",
                    "login",
                    "--username",
                    username,
                    "--password-stdin",
                    ecr_registry_url,
                ]

                logger.debug(
                    f"Authenticating Docker with ECR registry: {ecr_registry_url}"
                )

                process = await asyncio.create_subprocess_exec(
                    *login_cmd,
                    stdin=asyncio.subprocess.PIPE,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )

                stdout_login, stderr_login = await process.communicate(
                    password.encode()
                )

                if process.returncode != 0:
                    error_msg = stderr_login.decode().strip()
                    logger.error(f"Docker login failed: {error_msg}")
                    return TransferResult(
                        request=request,
                        success=False,
                        error_message=f"ECR authentication failed: {error_msg}",
                        transfer_method="buildx",
                    )

                logger.debug("Docker ECR authentication successful")

            except Exception as e:
                logger.error(f"ECR authentication error: {e}")
                return TransferResult(
                    request=request,
                    success=False,
                    error_message=f"ECR authentication error: {e}",
                    transfer_method="buildx",
                )

            # 6. Execute buildx create command with platform-specific sources
            cmd = [
                "docker",
                "buildx",
                "imagetools",
                "create",
                "-t",
                target_ref,
                *source_refs,  # Unpack all platform-specific digest references
            ]

            logger.debug(f"Executing buildx command: {' '.join(cmd)}")

            result = await asyncio.create_subprocess_exec(
                *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await result.communicate()

            success = result.returncode == 0
            stderr_str = stderr.decode().strip()

            if success:
                logger.info(f"Buildx transfer completed successfully: {target_ref}")

                # Perform digest verification if requested
                source_digest = None
                target_digest = None
                if request.verify_digest:
                    from .digest_verification import get_enhanced_digest

                    logger.debug("Starting digest verification for buildx transfer")

                    # Get source digest
                    try:
                        source_digest = await get_enhanced_digest(
                            None, request.source_image, request.source_tag
                        )
                        logger.debug(f"Source digest: {source_digest}")
                    except Exception as e:
                        logger.warning(f"Failed to get source digest: {e}")

                    # Get target digest
                    try:
                        target_digest = await get_enhanced_digest(
                            None,
                            f"{ecr_registry_url}/{request.target_repository}",
                            request.target_tag,
                        )
                        logger.debug(f"Target digest: {target_digest}")
                    except Exception as e:
                        logger.warning(f"Failed to get target digest: {e}")

                return TransferResult(
                    request=request,
                    success=True,
                    source_digest=source_digest,
                    target_digest=target_digest,
                    platforms_copied=target_platforms,
                    transfer_method="buildx",
                )
            else:
                # Extract clean error message for user display
                clean_error = self._extract_clean_error_message(stderr_str)

                # Log the full stderr at debug level to avoid polluting batch output
                # The clean error message is passed to TransferResult for user-facing display
                logger.debug(f"Buildx transfer failed: {stderr_str}")
                logger.debug(f"Clean error message: {clean_error}")

                return TransferResult(
                    request=request,
                    success=False,
                    error_message=clean_error,
                    transfer_method="buildx",
                )

        except BuildxError as e:
            # Log at debug level - error is captured in TransferResult for batch error summary
            logger.debug(f"Buildx transfer error: {e}")
            return TransferResult(
                request=request,
                success=False,
                error_message=str(e),
                transfer_method="buildx",
            )
        except Exception as e:
            # Log unexpected errors at warning level (not error) to reduce noise
            logger.warning(f"Unexpected buildx transfer error: {e}")
            return TransferResult(
                request=request,
                success=False,
                error_message=f"Unexpected error: {e}",
                transfer_method="buildx",
            )
