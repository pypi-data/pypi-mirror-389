"""ECR repository listing and management service."""

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional, Any

import boto3
from botocore.exceptions import ClientError, NoCredentialsError

from ..ecr_auth import ECRAuthenticationError
from ..aws_utils import resolve_aws_region
from .base_service import BaseECRService
from .cache_manager import get_cache
from .cache_service import make_cache_key, hash_params

logger = logging.getLogger(__name__)


@dataclass
class ECRRepository:
    """ECR repository information."""

    name: str
    uri: str
    created_at: datetime
    image_count: int
    size_bytes: int
    registry_id: str
    region: str
    latest_tag: Optional[str] = None
    tags: Dict[str, str] = None

    def __post_init__(self):
        if self.tags is None:
            self.tags = {}

    @property
    def size_mb(self) -> float:
        """Get repository size in MB."""
        return self.size_bytes / (1024 * 1024)

    @property
    def size_gb(self) -> float:
        """Get repository size in GB."""
        return self.size_bytes / (1024 * 1024 * 1024)


def _matches_tag_filter(
    image_tags: List[str], image_digest: str, tag_filter: str
) -> tuple[bool, List[str], bool]:
    """Check if image matches tag filter criteria.

    PURE FUNCTION: No I/O, easily testable.

    Args:
        image_tags: List of image tags
        image_digest: Image digest string
        tag_filter: Filter pattern to match against

    Returns:
        Tuple of (matches, matching_tags, has_matching_digest)
        - matches: True if image matches filter
        - matching_tags: List of tags that matched the filter
        - has_matching_digest: True if digest matched the filter
    """
    matching_tags = [tag for tag in image_tags if tag_filter.lower() in tag.lower()]
    has_matching_tag = bool(matching_tags)
    has_matching_digest = tag_filter.lower() in image_digest.lower()

    matches = has_matching_tag or has_matching_digest
    return matches, matching_tags, has_matching_digest


def _build_ecr_image(
    image_detail: dict,
    repository_name: str,
    registry_id: str,
    region_name: str,
) -> "ECRImage":
    """Build ECRImage object from AWS API response.

    PURE FUNCTION: Deterministic construction from dict.

    Args:
        image_detail: Image detail dict from describe_images API
        repository_name: Repository name
        registry_id: Registry ID (account ID)
        region_name: AWS region name

    Returns:
        ECRImage object
    """
    from ..aws_utils import resolve_aws_region

    return ECRImage(
        repository_name=repository_name,
        image_tags=image_detail.get("imageTags", []),
        image_digest=image_detail["imageDigest"],
        size_bytes=image_detail["imageSizeInBytes"],
        pushed_at=image_detail["imagePushedAt"],
        registry_id=registry_id or image_detail.get("registryId", ""),
        region=resolve_aws_region(region_name),
    )


def _handle_list_images_error(error: Exception, repository_name: str) -> None:
    """Handle errors from list_images operation.

    ERROR HANDLER: Testable with exception mocking.

    Args:
        error: The exception that was raised
        repository_name: Repository name for error messages

    Raises:
        ECRAuthenticationError: Always raises with appropriate message
    """
    from botocore.exceptions import ClientError

    from ..ecr_auth import ECRAuthenticationError

    if isinstance(error, ClientError):
        error_code = error.response["Error"]["Code"]
        if error_code == "RepositoryNotFoundException":
            raise ECRAuthenticationError(f"Repository '{repository_name}' not found")
        elif error_code == "UnauthorizedOperation":
            raise ECRAuthenticationError("Insufficient permissions to list ECR images")
        else:
            raise ECRAuthenticationError(f"ECR API error: {error}")
    else:
        logger.error(f"Failed to list images in repository {repository_name}: {error}")
        raise ECRAuthenticationError(f"Failed to list images: {error}")


@dataclass
class ECRImage:
    """ECR image information."""

    repository_name: str
    image_tags: List[str]
    image_digest: str
    size_bytes: int
    pushed_at: datetime
    registry_id: str
    region: str
    architectures: Optional[List[str]] = None

    @property
    def size_mb(self) -> float:
        """Get image size in MB."""
        return self.size_bytes / (1024 * 1024)

    @property
    def primary_tag(self) -> str:
        """Get primary tag (first tag or digest if no tags)."""
        if self.image_tags:
            return self.image_tags[0]
        return self.image_digest[:12]

    @property
    def architectures_display(self) -> str:
        """Get compact formatted architecture display string."""
        if not self.architectures:
            return "unknown"
        if len(self.architectures) == 1:
            # Show single arch without linux/ prefix for cleaner display
            arch = self.architectures[0]
            return arch[6:] if arch.startswith("linux/") else arch

        # For multi-arch, show first 2-3 architectures + count
        # Use list comprehension for better performance
        cleaned_archs = [
            arch[6:] if arch.startswith("linux/") else arch
            for arch in self.architectures[:3]  # Show first 3
        ]

        if len(self.architectures) <= 3:
            return ", ".join(cleaned_archs)
        else:
            remaining = len(self.architectures) - 3
            return f"{', '.join(cleaned_archs)} +{remaining}"

    @property
    def architectures_detailed(self) -> str:
        """Get detailed architecture display string."""
        if not self.architectures:
            return "unknown"

        # Clean up platform names for better display
        cleaned_platforms = []
        for arch in self.architectures:
            # Remove 'linux/' prefix for cleaner display
            if arch.startswith("linux/"):
                cleaned_platforms.append(arch[6:])
            else:
                cleaned_platforms.append(arch)

        # Join with commas, wrapping at reasonable length
        platforms_str = ", ".join(cleaned_platforms)
        if len(platforms_str) > 40:
            # Split into multiple lines for readability - optimized to avoid O(n²) string building
            lines = []
            current_parts: List[str] = []
            current_length = 0

            for platform in cleaned_platforms:
                # Calculate length without creating temporary strings
                comma_space_len = 2 if current_parts else 0
                new_total_length = current_length + len(platform) + comma_space_len

                if current_parts and new_total_length > 40:
                    # Finalize current line
                    lines.append(", ".join(current_parts))
                    current_parts = [platform]
                    current_length = len(platform)
                else:
                    current_parts.append(platform)
                    current_length = new_total_length

            if current_parts:
                lines.append(", ".join(current_parts))
            return "\n".join(lines)

        return platforms_str

    @property
    def is_digest_tag(self) -> bool:
        """Check if this image is tagged with a SHA256 digest."""
        # Check if primary tag (first tag or digest-based fallback) is a SHA256 digest
        primary = self.primary_tag
        return primary.startswith("sha256:") or (
            not self.image_tags and primary.startswith(self.image_digest[:12])
        )


class ECRRepositoryService(BaseECRService):
    """Service for managing ECR repository operations."""

    def __init__(
        self, region_name: Optional[str] = None, registry_id: Optional[str] = None
    ):
        """Initialize ECR repository service.

        Args:
            region_name: AWS region for ECR registry
            registry_id: AWS account ID for ECR registry
        """
        super().__init__(region_name, registry_id)
        self._ecr_client = None

    @property
    def ecr_client(self):
        """Get or create ECR client."""
        if self._ecr_client is None:
            try:
                self._ecr_client = boto3.client("ecr", region_name=self.region_name)
            except Exception as e:
                raise ECRAuthenticationError(f"Failed to create ECR client: {e}")
        return self._ecr_client

    def list_repositories(
        self, name_filter: Optional[str] = None, max_results: int = 100
    ) -> List[ECRRepository]:
        """List ECR repositories.

        This method uses caching to avoid repeated expensive API calls.
        Cache TTL is 600 seconds (10 minutes) to balance freshness with performance.

        Args:
            name_filter: Filter repositories by name pattern
            max_results: Maximum number of repositories to return

        Returns:
            List of ECR repositories

        Raises:
            ECRAuthenticationError: If authentication fails
        """
        # Try to get from cache first
        cache = get_cache("ecr_repositories")
        if cache:
            try:
                # Generate cache key including all parameters that affect results
                region = resolve_aws_region(self.region_name)
                params_hash = hash_params(
                    name_filter=name_filter or "",
                    max_results=max_results
                )
                cache_key = make_cache_key(
                    "ecr", region, self.registry_id or "default", "repos", params_hash
                )

                # Check cache
                import asyncio
                try:
                    loop = asyncio.get_event_loop()
                    if not loop.is_running():
                        cached_repos = loop.run_until_complete(cache.get(cache_key))
                        if cached_repos is not None:
                            logger.debug(
                                f"Cache hit for list_repositories: "
                                f"filter={name_filter}, max_results={max_results}"
                            )
                            return cached_repos
                except RuntimeError:
                    cached_repos = asyncio.run(cache.get(cache_key))
                    if cached_repos is not None:
                        logger.debug(
                            f"Cache hit for list_repositories: "
                            f"filter={name_filter}, max_results={max_results}"
                        )
                        return cached_repos
            except Exception as e:
                logger.debug(f"Cache lookup error for list_repositories: {e}")

        logger.debug(f"Cache miss for list_repositories: filter={name_filter}")

        try:
            repositories = []
            paginator = self.ecr_client.get_paginator("describe_repositories")

            pagination_config = {"MaxItems": max_results}
            paginate_kwargs = {"PaginationConfig": pagination_config}
            if self.registry_id:
                paginate_kwargs["registryId"] = self.registry_id

            page_iterator = paginator.paginate(**paginate_kwargs)

            # Generator expression for memory efficiency - process repos as they're found
            repositories = [
                ECRRepository(
                    name=repo_name,
                    uri=repo_data["repositoryUri"],
                    created_at=repo_data["createdAt"],
                    image_count=image_count,
                    size_bytes=total_size,
                    registry_id=repo_data["registryId"],
                    region=resolve_aws_region(self.region_name),
                    latest_tag=latest_tag,
                    tags=self._get_repository_tags(repo_name),
                )
                for page in page_iterator
                for repo_data in page["repositories"]
                for repo_name in [repo_data["repositoryName"]]
                if not name_filter or name_filter.lower() in repo_name.lower()
                for image_count, total_size, latest_tag in [
                    self._get_repository_statistics(repo_name)
                ]
            ]

            # Sort by name
            repositories.sort(key=lambda r: r.name)

            # Store in cache for future use
            if cache:
                try:
                    import asyncio
                    try:
                        loop = asyncio.get_event_loop()
                        if not loop.is_running():
                            loop.run_until_complete(cache.set(cache_key, repositories, ttl=600))
                    except RuntimeError:
                        asyncio.run(cache.set(cache_key, repositories, ttl=600))
                    logger.debug(
                        f"Cached list_repositories for filter={name_filter} (TTL=600s)"
                    )
                except Exception as e:
                    logger.debug(f"Cache store error for list_repositories: {e}")

            return repositories

        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            if error_code == "UnauthorizedOperation":
                raise ECRAuthenticationError(
                    "Insufficient permissions to list ECR repositories"
                )
            elif error_code == "RepositoryNotFoundException":
                return []
            else:
                raise ECRAuthenticationError(f"ECR API error: {e}")
        except NoCredentialsError:
            raise ECRAuthenticationError("AWS credentials not found")
        except Exception as e:
            logger.error(f"Failed to list ECR repositories: {e}")
            raise ECRAuthenticationError(f"Failed to list repositories: {e}")

    def list_images(
        self,
        repository_name: str,
        tag_filter: Optional[str] = None,
        max_results: int = 100,
        tagged_only: bool = False,
    ) -> List[ECRImage]:
        """List images in an ECR repository.

        This method uses caching to avoid repeated expensive API calls.
        Cache TTL is 300 seconds (5 minutes) to balance freshness with performance.

        Args:
            repository_name: Repository name
            tag_filter: Filter images by tag pattern
            max_results: Maximum number of images to return
            tagged_only: If True, only return images with tags (excludes digest-only manifests)

        Returns:
            List of ECR images

        Raises:
            ECRAuthenticationError: If authentication fails
        """
        logger.debug(
            f"list_images called: repository={repository_name}, tag_filter={tag_filter}, "
            f"max_results={max_results}, tagged_only={tagged_only}, "
            f"registry_id={self.registry_id}, region={self.region_name}"
        )

        # Try to get from cache first
        cache = get_cache("ecr_images")
        if cache:
            try:
                # Generate cache key including all parameters that affect results
                region = resolve_aws_region(self.region_name)
                params_hash = hash_params(
                    tag_filter=tag_filter or "",
                    max_results=max_results,
                    tagged_only=tagged_only
                )
                cache_key = make_cache_key(
                    "ecr", region, self.registry_id or "default", "images",
                    repository_name, params_hash
                )

                # Check cache
                import asyncio
                try:
                    loop = asyncio.get_event_loop()
                    if not loop.is_running():
                        cached_images = loop.run_until_complete(cache.get(cache_key))
                        if cached_images is not None:
                            logger.debug(
                                f"Cache hit for list_images: {repository_name} "
                                f"(filter={tag_filter}, tagged_only={tagged_only})"
                            )
                            return cached_images
                except RuntimeError:
                    cached_images = asyncio.run(cache.get(cache_key))
                    if cached_images is not None:
                        logger.debug(
                            f"Cache hit for list_images: {repository_name} "
                            f"(filter={tag_filter}, tagged_only={tagged_only})"
                        )
                        return cached_images
            except Exception as e:
                logger.debug(f"Cache lookup error for list_images({repository_name}): {e}")

        logger.debug(f"Cache miss for list_images: {repository_name}")

        try:
            images = []
            paginator = self.ecr_client.get_paginator("list_images")

            paginate_kwargs = {
                "repositoryName": repository_name,
                "PaginationConfig": {"MaxItems": max_results},
            }
            if self.registry_id:
                paginate_kwargs["registryId"] = self.registry_id

            # Use ECR's native filter to only fetch tagged images
            # This prevents fetching all the digest-only platform manifests first
            if tagged_only:
                paginate_kwargs["filter"] = {"tagStatus": "TAGGED"}
                logger.debug(
                    "list_images: Using ECR filter tagStatus=TAGGED to skip digest-only manifests"
                )

            page_iterator = paginator.paginate(**paginate_kwargs)

            page_count = 0
            total_image_ids = 0
            for page in page_iterator:
                page_count += 1
                # Get detailed image information
                if page["imageIds"]:
                    image_ids_in_page = len(page["imageIds"])
                    total_image_ids += image_ids_in_page
                    logger.debug(
                        f"list_images page {page_count}: {image_ids_in_page} imageIds found in repository {repository_name}"
                    )

                    image_details = self._describe_images(
                        repository_name, page["imageIds"]
                    )

                    logger.debug(
                        f"list_images page {page_count}: describe_images returned {len(image_details)} image details"
                    )

                    for image_detail in image_details:
                        image_tags = image_detail.get("imageTags", [])
                        image_digest = image_detail["imageDigest"]

                        # Apply tag filter using extracted helper
                        if tag_filter:
                            matches, matching_tags, has_matching_digest = (
                                _matches_tag_filter(
                                    image_tags, image_digest, tag_filter
                                )
                            )

                            if not matches:
                                logger.debug(
                                    f"list_images filter SKIP: digest={image_digest[:20]}..., tags={image_tags}, "
                                    f"tag_filter='{tag_filter}' - no match"
                                )
                                continue
                            else:
                                logger.debug(
                                    f"list_images filter MATCH: digest={image_digest[:20]}..., tags={image_tags}, "
                                    f"tag_filter='{tag_filter}' - matched_tags={matching_tags}, matched_digest={has_matching_digest}"
                                )

                        # Build image object using extracted helper
                        image = _build_ecr_image(
                            image_detail,
                            repository_name,
                            self.registry_id,
                            self.region_name,
                        )

                        images.append(image)

            # Sort by push date (newest first)
            images.sort(key=lambda i: i.pushed_at, reverse=True)

            logger.debug(
                f"list_images result: repository={repository_name}, tag_filter={tag_filter}, "
                f"pages={page_count}, total_imageIds={total_image_ids}, returned_images={len(images)}"
            )

            # Store in cache for future use
            if cache:
                try:
                    import asyncio
                    try:
                        loop = asyncio.get_event_loop()
                        if not loop.is_running():
                            loop.run_until_complete(cache.set(cache_key, images, ttl=300))
                    except RuntimeError:
                        asyncio.run(cache.set(cache_key, images, ttl=300))
                    logger.debug(f"Cached list_images for {repository_name} (TTL=300s)")
                except Exception as e:
                    logger.debug(f"Cache store error for list_images({repository_name}): {e}")

            return images

        except Exception as e:
            # Use extracted error handler
            _handle_list_images_error(e, repository_name)

    def repository_exists(self, repository_name: str) -> bool:
        """Check if ECR repository exists.

        Args:
            repository_name: Repository name to check

        Returns:
            True if repository exists
        """
        try:
            describe_kwargs = {"repositoryNames": [repository_name]}
            if self.registry_id:
                describe_kwargs["registryId"] = self.registry_id

            self.ecr_client.describe_repositories(**describe_kwargs)
            return True
        except ClientError as e:
            if e.response["Error"]["Code"] == "RepositoryNotFoundException":
                return False
            raise
        except Exception:
            return False

    def create_repository(
        self, repository_name: str, tags: Optional[Dict[str, str]] = None
    ) -> ECRRepository:
        """Create ECR repository.

        Args:
            repository_name: Name for new repository
            tags: Optional tags for repository

        Returns:
            Created repository information

        Raises:
            ECRAuthenticationError: If creation fails
        """
        try:
            create_params = {"repositoryName": repository_name}

            if self.registry_id:
                create_params["registryId"] = self.registry_id

            if tags:
                create_params["tags"] = [
                    {"Key": k, "Value": v} for k, v in tags.items()
                ]

            response = self.ecr_client.create_repository(**create_params)
            repo_data = response["repository"]

            return ECRRepository(
                name=repo_data["repositoryName"],
                uri=repo_data["repositoryUri"],
                created_at=repo_data["createdAt"],
                image_count=0,
                size_bytes=0,
                registry_id=repo_data["registryId"],
                region=resolve_aws_region(self.region_name),
                tags=tags or {},
            )

        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            if error_code == "RepositoryAlreadyExistsException":
                raise ECRAuthenticationError(
                    f"Repository '{repository_name}' already exists"
                )
            elif error_code == "LimitExceededException":
                raise ECRAuthenticationError("Repository limit exceeded")
            else:
                raise ECRAuthenticationError(f"Failed to create repository: {e}")
        except Exception as e:
            logger.error(f"Failed to create repository {repository_name}: {e}")
            raise ECRAuthenticationError(f"Failed to create repository: {e}")

    def get_repository_statistics(self) -> Dict[str, Any]:
        """Get overall ECR registry statistics.

        Returns:
            Dictionary with registry statistics
        """
        try:
            repositories = self.list_repositories()

            total_repositories = len(repositories)
            total_images = sum(repo.image_count for repo in repositories)
            total_size_gb = sum(repo.size_gb for repo in repositories)

            # Find largest repositories
            largest_repos = sorted(
                repositories, key=lambda r: r.size_bytes, reverse=True
            )[:5]
            most_images = sorted(
                repositories, key=lambda r: r.image_count, reverse=True
            )[:5]

            return {
                "total_repositories": total_repositories,
                "total_images": total_images,
                "total_size_gb": round(total_size_gb, 2),
                "average_images_per_repo": round(total_images / total_repositories, 1)
                if total_repositories > 0
                else 0,
                "average_size_mb_per_repo": round(
                    sum(repo.size_mb for repo in repositories) / total_repositories, 1
                )
                if total_repositories > 0
                else 0,
                "largest_repositories": [
                    {
                        "name": repo.name,
                        "size_gb": round(repo.size_gb, 2),
                        "image_count": repo.image_count,
                    }
                    for repo in largest_repos
                ],
                "repositories_with_most_images": [
                    {
                        "name": repo.name,
                        "image_count": repo.image_count,
                        "size_gb": round(repo.size_gb, 2),
                    }
                    for repo in most_images
                ],
            }

        except Exception as e:
            logger.error(f"Failed to get repository statistics: {e}")
            return {
                "error": str(e),
                "total_repositories": 0,
                "total_images": 0,
                "total_size_gb": 0,
            }

    def validate_repository_access(self, repository_name: str) -> bool:
        """Validate that we have access to push to a repository.

        Args:
            repository_name: Repository name to validate

        Returns:
            True if we have push access
        """
        try:
            # Check if repository exists
            if not self.repository_exists(repository_name):
                logger.info(f"Repository '{repository_name}' does not exist")
                return False

            # Try to get ECR authentication token (validates push permission)
            self.ecr_auth.get_docker_credentials()

            return True

        except Exception as e:
            logger.error(
                f"Repository access validation failed for '{repository_name}': {e}"
            )
            return False

    def _should_count_image(self, image_detail: Dict, repository_name: str) -> bool:
        """Determine if image should be counted in statistics - pure business logic.

        Filters out digest-only images (platform manifests without meaningful tags).
        This mirrors the filtering logic from list_images() for consistency.

        Args:
            image_detail: Image detail dictionary from AWS describe_images
            repository_name: Repository name for ECRImage construction

        Returns:
            True if image should be counted, False if it's digest-only
        """
        # Import locally to avoid circular imports
        from ..aws_utils import resolve_aws_region

        # Create ECRImage to leverage is_digest_tag property
        ecr_image = ECRImage(
            repository_name=repository_name,
            image_tags=image_detail.get("imageTags", []),
            image_digest=image_detail["imageDigest"],
            size_bytes=image_detail["imageSizeInBytes"],
            pushed_at=image_detail["imagePushedAt"],
            registry_id=self.registry_id or image_detail.get("registryId", ""),
            region=resolve_aws_region(self.region_name),
        )

        # Only count non-digest-tagged images (same logic as list_images)
        return not ecr_image.is_digest_tag

    def _update_latest_tag(
        self,
        current_latest: Optional[tuple[datetime, str]],
        image_detail: Dict,
    ) -> Optional[tuple[datetime, str]]:
        """Update latest tag if image is newer - pure comparison logic.

        Args:
            current_latest: Current (pushed_at, tag) tuple or None
            image_detail: Image detail dictionary from AWS

        Returns:
            Updated (pushed_at, tag) tuple if image is newer, or current_latest
        """
        # Check if image has tags
        image_tags = image_detail.get("imageTags")
        if not image_tags:
            return current_latest

        # Get pushed timestamp
        pushed_at = image_detail.get("imagePushedAt")
        if not pushed_at:
            return current_latest

        # Update if this is the first tagged image or if it's newer
        if current_latest is None or pushed_at > current_latest[0]:
            return (pushed_at, image_tags[0])  # Use first tag

        return current_latest

    def _get_repository_statistics(
        self, repository_name: str
    ) -> tuple[int, int, Optional[str]]:
        """Get image count, total size, and latest tag for repository.

        This method uses caching to avoid repeated expensive API calls.
        Cache TTL is 300 seconds (5 minutes) to balance freshness with performance.

        Args:
            repository_name: Repository name

        Returns:
            Tuple of (image_count, total_size_bytes, latest_tag)
        """
        # Try to get from cache first
        cache = get_cache("ecr_repositories")
        if cache:
            try:
                # Generate cache key: v1:ecr:{region}:{registry}:stats:{repo_name}
                region = resolve_aws_region(self.region_name)
                cache_key = make_cache_key(
                    "ecr", region, self.registry_id or "default", "stats", repository_name
                )

                # Check cache (need to run async code synchronously)
                import asyncio
                try:
                    # Try to get existing event loop
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        # We're already in an async context, can't use run()
                        # Fall through to compute stats without cache
                        pass
                    else:
                        cached_stats = loop.run_until_complete(cache.get(cache_key))
                        if cached_stats is not None:
                            logger.debug(f"Cache hit for repository statistics: {repository_name}")
                            return cached_stats
                except RuntimeError:
                    # No event loop, create one
                    cached_stats = asyncio.run(cache.get(cache_key))
                    if cached_stats is not None:
                        logger.debug(f"Cache hit for repository statistics: {repository_name}")
                        return cached_stats
            except Exception as e:
                # Cache errors should not break functionality
                logger.debug(f"Cache lookup error for {repository_name}: {e}")

        try:
            # Cache miss or cache unavailable - compute statistics
            logger.debug(f"Cache miss for repository statistics: {repository_name}")

            # List images to count them
            paginator = self.ecr_client.get_paginator("list_images")
            image_count = 0
            total_size = 0
            latest_info = None  # Track (pushed_at, tag) tuple

            paginate_kwargs = {"repositoryName": repository_name}
            if self.registry_id:
                paginate_kwargs["registryId"] = self.registry_id

            for page in paginator.paginate(**paginate_kwargs):
                image_ids = page["imageIds"]

                # Get detailed image information to count properly (like list_images does)
                if image_ids:
                    try:
                        image_details = self._describe_images(
                            repository_name, image_ids[:100]
                        )  # Limit to avoid API limits

                        # Process each image using extracted helpers
                        for img in image_details:
                            # Count only meaningful images (uses _should_count_image helper)
                            if self._should_count_image(img, repository_name):
                                image_count += 1

                            # Always count size (even for digest-only images)
                            total_size += img.get("imageSizeInBytes", 0)

                            # Track latest tagged image (uses _update_latest_tag helper)
                            latest_info = self._update_latest_tag(latest_info, img)

                    except Exception as e:
                        logger.debug(
                            f"Failed to get image sizes for {repository_name}: {e}"
                        )

            # Extract tag from latest_info tuple
            latest_tag = latest_info[1] if latest_info else None
            result = (image_count, total_size, latest_tag)

            # Store in cache for future use
            if cache:
                try:
                    import asyncio
                    try:
                        loop = asyncio.get_event_loop()
                        if not loop.is_running():
                            loop.run_until_complete(cache.set(cache_key, result, ttl=300))
                    except RuntimeError:
                        asyncio.run(cache.set(cache_key, result, ttl=300))
                    logger.debug(f"Cached repository statistics for {repository_name} (TTL=300s)")
                except Exception as e:
                    logger.debug(f"Cache store error for {repository_name}: {e}")

            return result

        except Exception as e:
            logger.debug(
                f"Failed to get statistics for repository {repository_name}: {e}"
            )
            return 0, 0, None

    def _describe_images(
        self, repository_name: str, image_ids: List[Dict]
    ) -> List[Dict]:
        """Get detailed information about images.

        Args:
            repository_name: Repository name
            image_ids: List of image identifiers

        Returns:
            List of image details

        Raises:
            Exception: If describe_images API call fails
        """
        logger.debug(
            f"_describe_images called: repository={repository_name}, "
            f"image_ids_count={len(image_ids)}, registry_id={self.registry_id}"
        )

        try:
            describe_kwargs = {"repositoryName": repository_name, "imageIds": image_ids}
            if self.registry_id:
                describe_kwargs["registryId"] = self.registry_id

            response = self.ecr_client.describe_images(**describe_kwargs)
            image_details = response["imageDetails"]

            logger.debug(
                f"_describe_images result: repository={repository_name}, "
                f"requested={len(image_ids)}, returned={len(image_details)}"
            )
            return image_details
        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            error_message = e.response["Error"]["Message"]
            logger.error(
                f"ECR API describe_images failed: repository={repository_name}, "
                f"error_code={error_code}, error_message={error_message}, "
                f"registry_id={self.registry_id}"
            )
            # Re-raise to propagate the error instead of silently returning []
            raise
        except Exception as e:
            logger.error(
                f"Unexpected error in describe_images: repository={repository_name}, "
                f"error={e}",
                exc_info=True,
            )
            # Re-raise to propagate the error instead of silently returning []
            raise

    def _get_repository_tags(self, repository_name: str) -> Dict[str, str]:
        """Get tags for repository.

        Args:
            repository_name: Repository name

        Returns:
            Dictionary of repository tags
        """
        try:
            response = self.ecr_client.list_tags_for_resource(
                resourceArn=f"arn:aws:ecr:{resolve_aws_region(self.region_name)}:{self.registry_id or '*'}:repository/{repository_name}"
            )

            return {tag["Key"]: tag["Value"] for tag in response.get("tags", [])}

        except Exception as e:
            logger.debug(f"Failed to get tags for repository {repository_name}: {e}")
            return {}

    async def _detect_image_architectures(
        self, repository_name: str, image_tag: str
    ) -> Optional[List[str]]:
        """Detect image architectures using buildx if available.

        Args:
            repository_name: ECR repository name
            image_tag: Image tag

        Returns:
            List of architecture strings (e.g., ['linux/amd64', 'linux/arm64']) or None if detection fails
        """
        try:
            from .hybrid_transfer_service import HybridTransferService

            # Build ECR registry URL
            ecr_registry_url = f"{self.registry_id or self.ecr_auth.registry_id}.dkr.ecr.{resolve_aws_region(self.region_name)}.amazonaws.com"
            full_image_name = f"{ecr_registry_url}/{repository_name}"

            # Initialize hybrid service (uses buildx if available)
            hybrid_service = HybridTransferService(
                region_name=self.region_name, registry_id=self.registry_id
            )

            # Ensure buildx is available before attempting inspection
            if not await hybrid_service._is_buildx_available():
                logger.debug("Buildx not available for architecture detection")
                return None

            # ECR login is required for buildx to access private registries
            # We need to authenticate Docker with ECR first
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

                process = await asyncio.create_subprocess_exec(
                    *login_cmd,
                    stdin=asyncio.subprocess.PIPE,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )

                stdout, stderr = await process.communicate(password.encode())

                if process.returncode != 0:
                    logger.debug(f"Docker login failed: {stderr.decode()}")
                    return None

            except Exception as e:
                logger.debug(f"ECR authentication failed for buildx: {e}")
                return None

            # Inspect image platforms
            platform_info = await hybrid_service.inspect_image_platforms(
                full_image_name, image_tag
            )

            if platform_info and platform_info.platforms:
                return [str(platform) for platform in platform_info.platforms]

            # If no platforms detected, assume single-arch amd64 (most common for ECR images)
            # This is because many single-arch images don't expose platform info via buildx
            logger.debug(
                f"No platforms detected for {full_image_name}:{image_tag}, assuming linux/amd64"
            )
            return ["linux/amd64"]

        except Exception as e:
            logger.debug(
                f"Failed to detect architectures for {repository_name}:{image_tag}: {e}"
            )
            return None

    async def list_images_with_architectures(
        self,
        repository_name: str,
        tag_filter: Optional[str] = None,
        max_results: int = 100,
    ) -> List[ECRImage]:
        """List images in an ECR repository with architecture detection.

        Args:
            repository_name: Repository name
            tag_filter: Filter images by tag pattern
            max_results: Maximum number of images to return

        Returns:
            List of ECR images with architecture information

        Raises:
            ECRAuthenticationError: If authentication fails
        """
        # Get basic image list first
        images = self.list_images(repository_name, tag_filter, max_results)

        # Detect architectures for each image (limit concurrency to avoid overwhelming the system)
        semaphore = asyncio.Semaphore(
            3
        )  # Limit to 3 concurrent architecture detections

        async def detect_architectures_for_image(image: ECRImage) -> ECRImage:
            async with semaphore:
                if image.image_tags:
                    # Use first tag for architecture detection
                    architectures = await self._detect_image_architectures(
                        repository_name, image.image_tags[0]
                    )
                    image.architectures = architectures
                return image

        # Process images concurrently
        tasks = [detect_architectures_for_image(image) for image in images]
        enhanced_images = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter out any exceptions and return successful results
        result_images = []
        for img in enhanced_images:
            if isinstance(img, ECRImage):
                result_images.append(img)
            else:
                logger.debug(f"Architecture detection failed for image: {img}")

        return result_images
