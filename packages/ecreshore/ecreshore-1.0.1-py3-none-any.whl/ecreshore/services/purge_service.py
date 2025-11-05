"""ECR purge service for removing images from ECR repositories."""

import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple

from botocore.exceptions import ClientError

from ..ecr_auth import ECRAuthenticationError
from .ecr_repository import ECRRepositoryService, ECRImage

logger = logging.getLogger(__name__)

DANGER_WARNING_ALL = "DANGER: This operation will permanently delete ALL images from ALL ECR repositories."
DANGER_WARNING_REPO = "DANGER: This operation will permanently delete images from the specified repository."


@dataclass
class PurgeResult:
    """Result of purge operation."""

    repository_name: str
    images_deleted: int
    images_kept: int
    images_failed: int
    success: bool
    kept_latest: bool = False
    error_message: Optional[str] = None
    # Detailed image information
    deleted_images: List["ECRImage"] = field(default_factory=list)
    kept_images: List["ECRImage"] = field(default_factory=list)
    failed_images: List["ECRImage"] = field(default_factory=list)


@dataclass
class PurgeSummary:
    """Summary of complete purge operation."""

    repositories_processed: int
    total_images_deleted: int
    total_images_kept: int
    total_images_failed: int
    repositories_failed: int
    success_results: List[PurgeResult]
    failed_results: List[PurgeResult]

    @property
    def overall_success(self) -> bool:
        """Check if overall operation was successful."""
        return self.repositories_failed == 0 and self.total_images_failed == 0


class ECRPurgeService:
    """Service for purging images from ECR repositories."""

    def __init__(
        self, region_name: Optional[str] = None, registry_id: Optional[str] = None
    ):
        """Initialize ECR purge service.

        Args:
            region_name: AWS region for ECR registry
            registry_id: AWS account ID for ECR registry
        """
        self.region_name = region_name
        self.registry_id = registry_id
        self._ecr_service = ECRRepositoryService(region_name, registry_id)

    def purge(
        self,
        repository_name: Optional[str] = None,
        all_repositories: bool = False,
        keep_latest: bool = False,
        dry_run: bool = False,
        name_filter: Optional[str] = None,
        exclude_repositories: Optional[Set[str]] = None,
    ) -> PurgeSummary:
        """Purge images from ECR repositories.

        Args:
            repository_name: Specific repository to purge (mutually exclusive with all_repositories)
            all_repositories: Purge all repositories (mutually exclusive with repository_name)
            keep_latest: Keep the most recently pushed image in each repository
            dry_run: If True, only simulate the operation
            name_filter: Only process repositories matching this pattern (only with all_repositories)
            exclude_repositories: Set of repository names to exclude (only with all_repositories)

        Returns:
            PurgeSummary with operation results
        """
        if not repository_name and not all_repositories:
            raise ValueError(
                "Must specify either repository_name or all_repositories=True"
            )

        if repository_name and all_repositories:
            raise ValueError(
                "Cannot specify both repository_name and all_repositories=True"
            )

        if repository_name:
            return self._purge_single_repository(
                repository_name=repository_name,
                keep_latest=keep_latest,
                dry_run=dry_run,
            )
        else:
            return self.purge_all_repositories(
                dry_run=dry_run,
                keep_latest=keep_latest,
                name_filter=name_filter,
                exclude_repositories=exclude_repositories,
            )

    def _purge_single_repository(
        self, repository_name: str, keep_latest: bool = False, dry_run: bool = False
    ) -> PurgeSummary:
        """Purge images from a single repository.

        Args:
            repository_name: Repository to purge
            keep_latest: Keep the most recently pushed image
            dry_run: If True, only simulate the operation

        Returns:
            PurgeSummary with single repository result
        """
        if not dry_run:
            warning_msg = DANGER_WARNING_REPO
            if keep_latest:
                warning_msg += " The most recent image will be preserved."
            logger.warning(warning_msg)

        result = self.purge_repository(
            repository_name=repository_name, keep_latest=keep_latest, dry_run=dry_run
        )

        if result.success:
            success_results = [result]
            failed_results = []
        else:
            success_results = []
            failed_results = [result]

        return PurgeSummary(
            repositories_processed=1,
            total_images_deleted=result.images_deleted,
            total_images_kept=result.images_kept,
            total_images_failed=result.images_failed,
            repositories_failed=len(failed_results),
            success_results=success_results,
            failed_results=failed_results,
        )

    def purge_all_repositories(
        self,
        dry_run: bool = False,
        keep_latest: bool = False,
        name_filter: Optional[str] = None,
        exclude_repositories: Optional[Set[str]] = None,
    ) -> PurgeSummary:
        """Purge all images from all ECR repositories.

        Args:
            dry_run: If True, only simulate the operation
            keep_latest: Keep the most recently pushed image in each repository
            name_filter: Only process repositories matching this pattern
            exclude_repositories: Set of repository names to exclude

        Returns:
            PurgeSummary with operation results
        """
        if not dry_run:
            warning_msg = DANGER_WARNING_ALL
            if keep_latest:
                warning_msg += (
                    " The most recent image in each repository will be preserved."
                )
            logger.warning(warning_msg)

        exclude_repositories = exclude_repositories or set()

        try:
            # Get all repositories
            logger.info("Fetching ECR repositories...")
            repositories = self._ecr_service.list_repositories(
                name_filter=name_filter, max_results=1000
            )

            if not repositories:
                logger.info("No repositories found")
                return PurgeSummary(
                    repositories_processed=0,
                    total_images_deleted=0,
                    total_images_kept=0,
                    total_images_failed=0,
                    repositories_failed=0,
                    success_results=[],
                    failed_results=[],
                )

            # Filter repositories
            filtered_repos = [
                repo for repo in repositories if repo.name not in exclude_repositories
            ]

            logger.info(f"Processing {len(filtered_repos)} repositories")

            success_results = []
            failed_results = []
            total_images_deleted = 0
            total_images_kept = 0
            total_images_failed = 0

            # Process each repository
            for repo in filtered_repos:
                logger.info(f"Processing repository: {repo.name}")

                result = self.purge_repository(
                    repo.name, keep_latest=keep_latest, dry_run=dry_run
                )

                if result.success:
                    success_results.append(result)
                    total_images_deleted += result.images_deleted
                    total_images_kept += result.images_kept
                else:
                    failed_results.append(result)
                    total_images_failed += result.images_failed
                    total_images_kept += (
                        result.images_kept
                    )  # Keep count even on partial failure

            return PurgeSummary(
                repositories_processed=len(filtered_repos),
                total_images_deleted=total_images_deleted,
                total_images_kept=total_images_kept,
                total_images_failed=total_images_failed,
                repositories_failed=len(failed_results),
                success_results=success_results,
                failed_results=failed_results,
            )

        except Exception as e:
            logger.error(f"Failed to purge repositories: {e}")
            raise ECRAuthenticationError(f"Purge operation failed: {e}")

    def purge_repository(
        self, repository_name: str, keep_latest: bool = False, dry_run: bool = False
    ) -> PurgeResult:
        """Purge images from a single ECR repository.

        Args:
            repository_name: Repository name to purge
            keep_latest: Keep the most recently pushed image
            dry_run: If True, only simulate the operation

        Returns:
            PurgeResult with operation details
        """
        try:
            # Get all images in repository
            images = self._ecr_service.list_images(repository_name, max_results=10000)

            if not images:
                logger.info(f"Repository {repository_name} is already empty")
                return PurgeResult(
                    repository_name=repository_name,
                    images_deleted=0,
                    images_kept=0,
                    images_failed=0,
                    success=True,
                    kept_latest=keep_latest,
                    deleted_images=[],
                    kept_images=[],
                    failed_images=[],
                )

            # Handle keep_latest logic
            images_to_delete = images
            kept_image_list = []

            if keep_latest and images:
                # Sort images by push date (newest first) and keep the first one
                sorted_images = sorted(
                    images, key=lambda img: img.pushed_at, reverse=True
                )
                latest_image = sorted_images[0]
                images_to_delete = sorted_images[1:]  # All except the latest
                kept_image_list = [latest_image]

                logger.info(
                    f"Keeping latest image: {latest_image.primary_tag} "
                    f"(pushed {latest_image.pushed_at.strftime('%Y-%m-%d %H:%M:%S')})"
                )

            if dry_run:
                delete_count = len(images_to_delete)
                keep_msg = f", keeping {len(kept_image_list)}" if keep_latest else ""
                logger.info(
                    f"DRY RUN: Would delete {delete_count} images from {repository_name}{keep_msg}"
                )
                return PurgeResult(
                    repository_name=repository_name,
                    images_deleted=delete_count,
                    images_kept=len(kept_image_list),
                    images_failed=0,
                    success=True,
                    kept_latest=keep_latest,
                    deleted_images=images_to_delete,
                    kept_images=kept_image_list,
                    failed_images=[],
                )

            if not images_to_delete:
                logger.info(
                    f"No images to delete from {repository_name} (keeping latest)"
                )
                return PurgeResult(
                    repository_name=repository_name,
                    images_deleted=0,
                    images_kept=len(kept_image_list),
                    images_failed=0,
                    success=True,
                    kept_latest=keep_latest,
                    deleted_images=[],
                    kept_images=kept_image_list,
                    failed_images=[],
                )

            # Delete images in batches
            all_deleted_images = []
            all_failed_images = []

            # Group images into batches for efficient deletion
            batch_size = 100  # ECR API limit
            image_batches = [
                images_to_delete[i : i + batch_size]
                for i in range(0, len(images_to_delete), batch_size)
            ]

            for batch in image_batches:
                deleted_images, failed_images = self._delete_image_batch(
                    repository_name, batch
                )
                all_deleted_images.extend(deleted_images)
                all_failed_images.extend(failed_images)

            deleted_count = len(all_deleted_images)
            failed_count = len(all_failed_images)
            success = failed_count == 0

            if success:
                keep_msg = (
                    f", kept {len(kept_image_list)}" if len(kept_image_list) > 0 else ""
                )
                logger.info(
                    f"Successfully deleted {deleted_count} images from {repository_name}{keep_msg}"
                )
            else:
                keep_msg = (
                    f", kept {len(kept_image_list)}" if len(kept_image_list) > 0 else ""
                )
                logger.warning(
                    f"Deleted {deleted_count} images from {repository_name}, "
                    f"failed to delete {failed_count} images{keep_msg}"
                )

            return PurgeResult(
                repository_name=repository_name,
                images_deleted=deleted_count,
                images_kept=len(kept_image_list),
                images_failed=failed_count,
                success=success,
                kept_latest=keep_latest,
                deleted_images=all_deleted_images,
                kept_images=kept_image_list,
                failed_images=all_failed_images,
            )

        except ECRAuthenticationError:
            raise
        except Exception as e:
            error_msg = f"Failed to purge repository {repository_name}: {e}"
            logger.error(error_msg)
            return PurgeResult(
                repository_name=repository_name,
                images_deleted=0,
                images_kept=0,
                images_failed=0,
                success=False,
                kept_latest=keep_latest,
                error_message=error_msg,
                deleted_images=[],
                kept_images=[],
                failed_images=[],
            )

    def _extract_deleted_images(
        self, response_ids: List[Dict], digest_to_image: Dict[str, ECRImage]
    ) -> List[ECRImage]:
        """Extract successfully deleted images from AWS response - pure function.

        Args:
            response_ids: List of imageId dicts from batch_delete_image response
            digest_to_image: Mapping from digest to ECRImage object

        Returns:
            List of ECRImage objects that were successfully deleted
        """
        deleted_images = []
        for deleted_id in response_ids:
            digest = deleted_id.get("imageDigest")
            if digest and digest in digest_to_image:
                deleted_images.append(digest_to_image[digest])
        return deleted_images

    def _extract_failed_images(
        self, response_failures: List[Dict], digest_to_image: Dict[str, ECRImage]
    ) -> List[ECRImage]:
        """Extract failed images from AWS response - pure function.

        Args:
            response_failures: List of failure dicts from batch_delete_image response
            digest_to_image: Mapping from digest to ECRImage object

        Returns:
            List of ECRImage objects that failed to delete
        """
        failed_images = []
        for failure in response_failures:
            digest = failure.get("imageId", {}).get("imageDigest")
            if digest and digest in digest_to_image:
                failed_images.append(digest_to_image[digest])
        return failed_images

    def _log_delete_failures(
        self, failures: List[Dict], repository_name: str
    ) -> None:
        """Log deletion failures - side effect function.

        Args:
            failures: List of failure dicts from AWS response
            repository_name: Repository name for logging context
        """
        for failure in failures:
            image_id = failure.get("imageId", {})
            reason = failure.get("failureReason", "Unknown error")
            logger.warning(
                f"Failed to delete image {image_id} from {repository_name}: {reason}"
            )

    def _handle_delete_error(
        self,
        error: Exception,
        repository_name: str,
        images: List[ECRImage]
    ) -> Tuple[List[ECRImage], List[ECRImage]]:
        """Handle deletion errors and return failure result - error handler.

        Args:
            error: Exception that occurred
            repository_name: Repository name for logging context
            images: Original list of images (all will be marked as failed)

        Returns:
            Tuple of (empty list, all images as failed)
        """
        if isinstance(error, ClientError):
            error_code = error.response["Error"]["Code"]
            if error_code == "RepositoryNotFoundException":
                logger.error(f"Repository '{repository_name}' not found")
            elif error_code == "InvalidParameterException":
                logger.error(
                    f"Invalid parameters for repository '{repository_name}': {error}"
                )
            else:
                logger.error(f"ECR API error deleting from {repository_name}: {error}")
        else:
            logger.error(f"Unexpected error deleting batch from {repository_name}: {error}")

        return [], images  # All images failed

    def _delete_image_batch(
        self, repository_name: str, images: List[ECRImage]
    ) -> Tuple[List[ECRImage], List[ECRImage]]:
        """Delete a batch of images from repository.

        Args:
            repository_name: Repository name
            images: List of images to delete

        Returns:
            Tuple of (deleted_images, failed_images)
        """
        try:
            # Create mapping from digest to image object for tracking results
            digest_to_image = {image.image_digest: image for image in images}

            # Prepare image identifiers for batch delete
            image_ids = [{"imageDigest": image.image_digest} for image in images]

            # Execute batch delete
            delete_kwargs = {"repositoryName": repository_name, "imageIds": image_ids}
            if self.registry_id:
                delete_kwargs["registryId"] = self.registry_id

            response = self._ecr_service.ecr_client.batch_delete_image(**delete_kwargs)

            # Extract results using helpers
            deleted_images = self._extract_deleted_images(
                response.get("imageIds", []), digest_to_image
            )

            failed_images = self._extract_failed_images(
                response.get("failures", []), digest_to_image
            )

            # Log failures
            if response.get("failures"):
                self._log_delete_failures(response["failures"], repository_name)

            return deleted_images, failed_images

        except Exception as e:
            return self._handle_delete_error(e, repository_name, images)

    def get_purge_preview(
        self,
        name_filter: Optional[str] = None,
        exclude_repositories: Optional[Set[str]] = None,
    ) -> Dict[str, int]:
        """Get preview of what would be purged without actually purging.

        Args:
            name_filter: Only include repositories matching this pattern
            exclude_repositories: Set of repository names to exclude

        Returns:
            Dictionary mapping repository names to image counts
        """
        exclude_repositories = exclude_repositories or set()

        try:
            repositories = self._ecr_service.list_repositories(
                name_filter=name_filter, max_results=1000
            )

            preview = {}
            for repo in repositories:
                if repo.name not in exclude_repositories:
                    # Use cached image count from repository listing
                    preview[repo.name] = repo.image_count

            return preview

        except Exception as e:
            logger.error(f"Failed to get purge preview: {e}")
            raise ECRAuthenticationError(f"Preview failed: {e}")
