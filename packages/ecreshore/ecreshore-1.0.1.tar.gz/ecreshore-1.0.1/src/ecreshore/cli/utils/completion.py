"""Shell completion utilities for CLI commands."""

import logging
import time
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# Cache for ECR repository completion (5 minute TTL)
_repo_completion_cache: Dict[str, Tuple[float, List[str]]] = {}
_cache_ttl: int = 300  # 5 minutes


def _get_region_from_context(ctx) -> Optional[str]:
    """Extract region from Click context or environment."""
    if hasattr(ctx, "params") and ctx.params.get("region"):
        return ctx.params["region"]

    # Fall back to environment or default
    import os

    return os.environ.get("AWS_REGION") or os.environ.get("AWS_DEFAULT_REGION")


def _fetch_repositories_with_timeout(
    region: Optional[str], name_filter: str, max_results: int = 50
) -> List:
    """Fetch ECR repositories with timeout protection."""
    try:
        # Import here to avoid circular imports
        from ...services.ecr_repository import ECRRepositoryService

        # Create service with minimal configuration
        service = ECRRepositoryService(region_name=region)

        # Quick fetch with limited results for completion performance
        repos = service.list_repositories(
            name_filter=name_filter, max_results=max_results
        )

        # Debug: log what we got for troubleshooting
        repo_names = [repo.name for repo in repos]
        logger.debug(f"Completion fetched repositories: {repo_names}")

        return repos

    except Exception as e:
        # Log at debug level to avoid cluttering completion
        logger.debug(f"Repository completion failed: {e}")
        return []


def complete_ecr_repositories(ctx, _param, incomplete):
    """Complete ECR repository names with caching and performance optimization.

    Args:
        ctx: Click context
        param: Click parameter
        incomplete: Partial input from user

    Returns:
        List of CompletionItem objects for completion
    """
    try:
        from click.shell_completion import CompletionItem

        # Extract region for cache key
        region = _get_region_from_context(ctx)
        cache_key = f"{region}:{incomplete}"

        # Check cache first
        current_time = time.time()
        if cache_key in _repo_completion_cache:
            cached_time, cached_repos = _repo_completion_cache[cache_key]
            if current_time - cached_time < _cache_ttl:
                return cached_repos

        # Clean old cache entries while we're here
        _cleanup_completion_cache(current_time)

        # Fetch repositories with timeout protection
        repos = _fetch_repositories_with_timeout(region, incomplete or "")

        # Create CompletionItem objects with helpful information
        completions = []
        for repo in repos:
            if repo.name.startswith(incomplete or ""):
                # Format size nicely
                if repo.size_gb >= 1:
                    size_str = f"{repo.size_gb:.1f}GB"
                else:
                    size_str = f"{repo.size_mb:.0f}MB"

                description = f"{repo.image_count} images, {size_str}"
                completions.append(CompletionItem(value=repo.name, help=description))

        # Cache the results
        _repo_completion_cache[cache_key] = (current_time, completions)

        return completions

    except Exception as e:
        # Graceful fallback - never break shell completion
        logger.debug(f"ECR completion error: {e}")
        return []


def _cleanup_completion_cache(current_time: float) -> None:
    """Remove expired entries from completion cache."""
    expired_keys = [
        key
        for key, (cached_time, _) in _repo_completion_cache.items()
        if current_time - cached_time > _cache_ttl
    ]
    for key in expired_keys:
        del _repo_completion_cache[key]


def complete_aws_regions(_ctx, _param, incomplete):
    """Complete AWS region names."""
    from click.shell_completion import CompletionItem

    regions = [
        ("us-east-1", "US East (N. Virginia)"),
        ("us-east-2", "US East (Ohio)"),
        ("us-west-1", "US West (N. California)"),
        ("us-west-2", "US West (Oregon)"),
        ("eu-west-1", "Europe (Ireland)"),
        ("eu-west-2", "Europe (London)"),
        ("eu-central-1", "Europe (Frankfurt)"),
        ("eu-north-1", "Europe (Stockholm)"),
        ("ap-southeast-1", "Asia Pacific (Singapore)"),
        ("ap-southeast-2", "Asia Pacific (Sydney)"),
        ("ap-northeast-1", "Asia Pacific (Tokyo)"),
        ("ca-central-1", "Canada (Central)"),
        ("sa-east-1", "South America (São Paulo)"),
    ]

    return [
        CompletionItem(value=region, help=description)
        for region, description in regions
        if region.startswith(incomplete or "")
    ]
