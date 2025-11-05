"""Validation utilities for CLI commands."""

import sys

from ...services.progress_reporter import ProgressReporter
from ...services.transfer_service import TransferService


def validate_prerequisites_or_exit(
    transfer_service: TransferService, progress_reporter: ProgressReporter
) -> None:
    """Validate prerequisites and exit on failure."""
    progress_reporter.info("Validating prerequisites...")
    if not transfer_service.validate_prerequisites():
        progress_reporter.error("Prerequisites validation failed")
        sys.exit(1)
    progress_reporter.success("Prerequisites validated")


def validate_authentication_or_exit(
    transfer_service: TransferService, progress_reporter: ProgressReporter
) -> str:
    """Test ECR authentication and return registry URL on success."""
    progress_reporter.info("Testing ECR authentication...")
    if not transfer_service.validate_prerequisites():
        progress_reporter.error("Authentication failed")
        sys.exit(1)

    registry_url = transfer_service.get_ecr_registry_url()
    progress_reporter.success("Authentication successful")
    progress_reporter.info(f"Registry URL: {registry_url}")
    return registry_url
