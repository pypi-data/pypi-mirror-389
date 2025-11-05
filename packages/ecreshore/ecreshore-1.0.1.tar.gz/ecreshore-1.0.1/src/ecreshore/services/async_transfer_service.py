"""Async Transfer service for moving container images to ECR with concurrent support."""

import logging
from typing import Optional, Dict, List
import asyncio

from ..async_docker_client import AsyncDockerImageClient, AsyncDockerClientError
from ..ecr_auth import ECRAuthenticationError
from .base_service import BaseECRService
from .transfer_service import TransferRequest, TransferResult

logger = logging.getLogger(__name__)


class AsyncTransferService(BaseECRService):
    """Async service for transferring container images to ECR with concurrent capabilities."""

    def __init__(
        self,
        region_name: Optional[str] = None,
        registry_id: Optional[str] = None,
        max_retry_attempts: int = 3,
        enable_retry: bool = False,
    ):
        """Initialize async transfer service.

        Args:
            region_name: AWS region for ECR registry
            registry_id: AWS account ID for ECR registry
            max_retry_attempts: Maximum number of retry attempts
            enable_retry: Enable retry logic for failed transfers
        """
        super().__init__(region_name, registry_id)
        self.max_retry_attempts = max_retry_attempts
        self.enable_retry = enable_retry

    async def transfer_image(self, request: TransferRequest) -> TransferResult:
        """Transfer a single image to ECR asynchronously.

        Args:
            request: Transfer request details

        Returns:
            Transfer result with success status and details
        """
        # For now, implement without retry logic - can add later
        return await self._transfer_image_once(request)

    async def _transfer_image_once(self, request: TransferRequest) -> TransferResult:
        """Transfer a single image to ECR without retry logic.

        Args:
            request: Transfer request details

        Returns:
            Transfer result with success status and details
        """
        logger.info(
            f"Starting async transfer: {request.source_image}:{request.source_tag} -> {request.target_repository}:{request.target_tag}"
        )

        async with AsyncDockerImageClient() as docker_client:
            try:
                # Get ECR registry URL and build full target image name
                ecr_registry_url = self.get_ecr_registry_url()
                full_target_image = f"{ecr_registry_url}/{request.target_repository}"

                # Pull source image
                logger.debug(
                    f"Pulling source image: {request.source_image}:{request.source_tag}"
                )
                await docker_client.pull_image(request.source_image, request.source_tag)

                # Get source digest if verification is requested
                source_digest = None
                if request.verify_digest:
                    from .digest_verification import get_enhanced_digest

                    source_digest = await get_enhanced_digest(
                        docker_client, request.source_image, request.source_tag
                    )

                # Tag for ECR
                logger.debug(
                    f"Tagging for ECR: {full_target_image}:{request.target_tag}"
                )
                await docker_client.tag_image(
                    f"{request.source_image}:{request.source_tag}",
                    full_target_image,
                    request.target_tag,
                )

                # Get ECR credentials and push
                username, password = self.ecr_auth.get_docker_credentials()
                auth_config = {"username": username, "password": password}

                logger.debug(
                    f"Pushing to ECR: {full_target_image}:{request.target_tag}"
                )

                # Push with streaming - O(1) memory usage (CRITICAL FIX)
                await self._push_with_streaming(
                    docker_client, full_target_image, request.target_tag, auth_config
                )

                # Get target digest for verification
                target_digest = None
                if request.verify_digest:
                    from .digest_verification import get_enhanced_digest

                    target_digest = await get_enhanced_digest(
                        docker_client, full_target_image, request.target_tag
                    )

                    # Verify digests match if both available
                    if source_digest and target_digest:
                        if source_digest != target_digest:
                            logger.error(
                                f"Image integrity verification failed - digest mismatch: source={source_digest}, target={target_digest}"
                            )
                            return TransferResult(
                                request=request,
                                success=False,
                                error_message="Image integrity verification failed - digest mismatch",
                                source_digest=source_digest,
                                target_digest=target_digest,
                            )
                        else:
                            logger.info(
                                f"Image integrity verified - digests match: {source_digest}"
                            )
                    elif not source_digest and not target_digest:
                        logger.debug(
                            "Digest verification skipped - no digests available"
                        )
                    else:
                        logger.warning(
                            f"Partial digest verification - source: {source_digest}, target: {target_digest}"
                        )

                logger.info(
                    f"Async transfer completed successfully: {request.source_image}:{request.source_tag}"
                )

                return TransferResult(
                    request=request,
                    success=True,
                    source_digest=source_digest,
                    target_digest=target_digest,
                )

            except (AsyncDockerClientError, ECRAuthenticationError) as e:
                logger.error(f"Async transfer failed: {e}")
                return TransferResult(
                    request=request, success=False, error_message=str(e)
                )
            except Exception as e:
                logger.error(f"Unexpected async transfer error: {e}")
                return TransferResult(
                    request=request,
                    success=False,
                    error_message=f"Unexpected error: {e}",
                )

    async def _push_with_streaming(
        self,
        docker_client: AsyncDockerImageClient,
        repository: str,
        tag: str,
        auth_config: Dict[str, str],
    ) -> None:
        """Push image with streaming progress - O(1) memory usage.

        This replaces the problematic list(push_logs) pattern that consumed
        all push logs in memory proportional to image size.
        """
        log_count = 0
        async for log_entry in docker_client.push_image_stream(
            repository, tag, auth_config
        ):
            log_count += 1
            # Process logs incrementally without storing them
            if "status" in log_entry:
                if log_count % 10 == 0:  # Log progress every 10th entry to avoid spam
                    logger.debug(f"Push progress: {log_entry.get('status', '')}")

            # Handle errors immediately
            if "error" in log_entry:
                raise AsyncDockerClientError(f"Push failed: {log_entry['error']}")

        logger.info(f"Push completed with {log_count} status updates")

    async def transfer_images_concurrent(
        self, requests: List[TransferRequest], max_concurrent: int = 5
    ) -> List[TransferResult]:
        """Transfer multiple images concurrently.

        Args:
            requests: List of transfer requests
            max_concurrent: Maximum number of concurrent transfers

        Returns:
            List of transfer results
        """
        logger.info(
            f"Starting concurrent transfer of {len(requests)} images with max_concurrent={max_concurrent}"
        )

        # Create semaphore to limit concurrency
        semaphore = asyncio.Semaphore(max_concurrent)

        async def transfer_with_semaphore(request: TransferRequest) -> TransferResult:
            async with semaphore:
                return await self.transfer_image(request)

        # Execute all transfers concurrently
        tasks = [transfer_with_semaphore(request) for request in requests]
        results = await asyncio.gather(*tasks)

        # Log summary
        success_count = sum(1 for r in results if r.success)
        failure_count = len(results) - success_count
        logger.info(
            f"Concurrent transfer completed: {success_count} succeeded, {failure_count} failed"
        )

        return results
