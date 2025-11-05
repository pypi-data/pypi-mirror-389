"""AWS utility functions for ecreshore."""

import boto3
from typing import Optional


def resolve_aws_region(explicit_region: Optional[str] = None) -> str:
    """Resolve AWS region using standard boto3 mechanisms.

    Resolution order:
    1. Explicit region parameter
    2. AWS_DEFAULT_REGION environment variable
    3. AWS_REGION environment variable
    4. AWS shared config file (~/.aws/config)
    5. EC2 instance metadata (if running on EC2)

    Args:
        explicit_region: Explicitly provided region (e.g. from --region flag)

    Returns:
        Resolved AWS region name

    Raises:
        ValueError: If no region can be determined through any mechanism
    """
    if explicit_region:
        return explicit_region

    # Let boto3 handle the standard region resolution
    session = boto3.Session()
    region = session.region_name

    if not region:
        raise ValueError(
            "AWS region not specified. Please set the region using one of:\n"
            "  • --region command line flag\n"
            "  • AWS_DEFAULT_REGION environment variable\n"
            "  • AWS_REGION environment variable\n"
            "  • AWS shared config file (~/.aws/config)\n"
            "  • EC2 instance metadata (if running on EC2)"
        )

    return region
