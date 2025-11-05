"""Batch configuration service for parsing YAML configuration files."""

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, Generator, List, Optional, Type, TypeVar, Union

import yaml

from .error_handler import ConfigurationError

logger = logging.getLogger(__name__)

DEFAULT_CONCURRENT_TRANSFERS = 3
DEFAULT_RETRY_ATTEMPTS = 3
DEFAULT_VERIFY_DIGESTS = True

T = TypeVar("T")


# Field parsing helpers for reducing validation complexity


@dataclass
class FieldSpec:
    """Specification for how to parse and validate a configuration field.

    This enables declarative field validation, reducing cyclomatic complexity
    by replacing repetitive if-isinstance-raise patterns with reusable logic.
    """

    name: str
    field_type: Type
    required: bool = False
    allow_none: bool = False
    transform: Optional[Callable[[Any], Any]] = None


def parse_field(
    data: Dict, spec: FieldSpec, default: Optional[T] = None
) -> Optional[T]:
    """Parse and validate a single field from configuration data.

    This helper consolidates the common pattern of:
    1. Check if field exists
    2. Validate type
    3. Apply transformations (e.g., strip strings)
    4. Handle None values

    Args:
        data: Configuration dictionary
        spec: Field specification defining validation rules
        default: Default value if field not present

    Returns:
        Parsed and validated field value

    Raises:
        ConfigurationError: If validation fails

    Example:
        >>> region = parse_field(
        ...     settings_data,
        ...     FieldSpec('region', str, allow_none=True,
        ...              transform=lambda s: s.strip() if s else None)
        ... )
    """
    # Field not present - return default or raise if required
    if spec.name not in data:
        if spec.required:
            raise ConfigurationError(f"Missing required field '{spec.name}'")
        return default

    value = data[spec.name]

    # Handle None values
    if value is None:
        if not spec.allow_none:
            raise ConfigurationError(f"Field '{spec.name}' cannot be None")
        return None

    # Type validation
    if not isinstance(value, spec.field_type):
        # Format type name for error message (e.g., str -> string, bool -> boolean)
        type_name_map = {
            "str": "a string",
            "int": "an integer",
            "bool": "a boolean",
            "list": "a list",
            "dict": "a dictionary",
        }
        type_name = type_name_map.get(
            spec.field_type.__name__, spec.field_type.__name__
        )
        raise ConfigurationError(f"'{spec.name}' must be {type_name}")

    # Apply transformation (e.g., strip whitespace from strings)
    if spec.transform:
        value = spec.transform(value)

    return value


@dataclass
class BatchTransferRequest:
    """Configuration for a single transfer in a batch operation."""

    source: str
    target: str
    source_tag: str = "latest"
    target_tag: Optional[str] = None
    verify_digest: Optional[bool] = None
    preserve_architectures: Optional[bool] = None
    platforms: Optional[List[str]] = None

    def __post_init__(self):
        """Process fields after initialization."""
        # Track if explicit tags were provided (defaults indicate no explicit tags)
        explicit_source_tag = self.source_tag != "latest"
        explicit_target_tag = self.target_tag is not None

        # Parse source image and tag if colon notation used and no explicit source_tag
        if ":" in self.source and not explicit_source_tag:
            source_parts = self.source.rsplit(":", 1)
            if len(source_parts) == 2:
                self.source = source_parts[0]
                self.source_tag = source_parts[1]

        # Parse target repository and tag if colon notation used and no explicit target_tag
        if ":" in self.target and not explicit_target_tag:
            target_parts = self.target.rsplit(":", 1)
            if len(target_parts) == 2:
                self.target = target_parts[0]
                self.target_tag = target_parts[1]

        # If target_tag still not specified, use source_tag
        if self.target_tag is None:
            self.target_tag = self.source_tag


@dataclass
class BatchSettings:
    """Settings for batch transfer operations."""

    concurrent_transfers: int = DEFAULT_CONCURRENT_TRANSFERS
    retry_attempts: int = DEFAULT_RETRY_ATTEMPTS
    verify_digests: bool = DEFAULT_VERIFY_DIGESTS
    region: Optional[str] = None
    registry_id: Optional[str] = None
    preserve_architectures: Optional[bool] = None
    target_platforms: Optional[List[str]] = None


@dataclass
class BatchRequest:
    """Complete batch transfer request with transfers and settings."""

    transfers: List[BatchTransferRequest]
    settings: BatchSettings = field(default_factory=BatchSettings)

    def __post_init__(self):
        """Validate batch request after initialization."""
        if not self.transfers:
            raise ConfigurationError("Batch request must contain at least one transfer")

        if self.settings.concurrent_transfers < 1:
            raise ConfigurationError("concurrent_transfers must be at least 1")

        if self.settings.retry_attempts < 0:
            raise ConfigurationError("retry_attempts must be non-negative")


@dataclass
class StreamingBatchRequest:
    """Memory-efficient batch request using generators for large transfer lists."""

    transfer_generator: Generator[BatchTransferRequest, None, None]
    settings: BatchSettings
    total_count: Optional[int] = None  # If known ahead of time

    def to_standard_batch_request(self) -> BatchRequest:
        """Convert to standard BatchRequest by materializing all transfers.

        Use this only when you need the full list in memory.
        """
        transfers = list(self.transfer_generator)
        return BatchRequest(transfers=transfers, settings=self.settings)


class BatchConfigService:
    """Service for parsing and validating batch configuration files."""

    @staticmethod
    def load_from_file(config_path: Union[str, Path]) -> BatchRequest:
        """Load batch configuration from YAML file.

        Args:
            config_path: Path to YAML configuration file

        Returns:
            BatchRequest with parsed configuration

        Raises:
            ConfigurationError: If file cannot be read or parsed
        """
        config_path = Path(config_path)

        if not config_path.exists():
            raise ConfigurationError(f"Configuration file not found: {config_path}")

        try:
            with config_path.open("r", encoding="utf-8") as f:
                config_data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise ConfigurationError(f"Invalid YAML format: {e}")
        except OSError as e:
            raise ConfigurationError(f"Cannot read configuration file: {e}")

        if not isinstance(config_data, dict):
            raise ConfigurationError("Configuration must be a YAML object/dictionary")

        return BatchConfigService._parse_config(config_data)

    @staticmethod
    def load_from_string(config_yaml: str) -> BatchRequest:
        """Load batch configuration from YAML string.

        Args:
            config_yaml: YAML configuration as string

        Returns:
            BatchRequest with parsed configuration

        Raises:
            ConfigurationError: If YAML cannot be parsed
        """
        try:
            config_data = yaml.safe_load(config_yaml)
        except yaml.YAMLError as e:
            raise ConfigurationError(f"Invalid YAML format: {e}")

        if not isinstance(config_data, dict):
            raise ConfigurationError("Configuration must be a YAML object/dictionary")

        return BatchConfigService._parse_config(config_data)

    @staticmethod
    def _parse_config(config_data: Dict) -> BatchRequest:
        """Parse configuration dictionary into BatchRequest.

        Args:
            config_data: Parsed YAML configuration

        Returns:
            BatchRequest with validated configuration

        Raises:
            ConfigurationError: If configuration is invalid
        """
        # Parse transfers
        transfers_data = config_data.get("transfers", [])
        if not isinstance(transfers_data, list):
            raise ConfigurationError("'transfers' must be a list")

        if not transfers_data:
            raise ConfigurationError("'transfers' list cannot be empty")

        transfers = []
        for i, transfer_data in enumerate(transfers_data):
            if not isinstance(transfer_data, dict):
                raise ConfigurationError(f"Transfer {i} must be an object")

            try:
                transfers.append(BatchConfigService._parse_transfer(transfer_data))
            except Exception as e:
                raise ConfigurationError(f"Invalid transfer {i}: {e}")

        # Parse settings
        settings_data = config_data.get("settings", {})
        if not isinstance(settings_data, dict):
            raise ConfigurationError("'settings' must be an object")

        settings = BatchConfigService._parse_settings(settings_data)

        return BatchRequest(transfers=transfers, settings=settings)

    @staticmethod
    def _parse_transfer(transfer_data: Dict) -> BatchTransferRequest:
        """Parse a single transfer configuration.

        Args:
            transfer_data: Transfer configuration dictionary

        Returns:
            BatchTransferRequest with parsed configuration

        Raises:
            ConfigurationError: If transfer configuration is invalid
        """

        # Helper factory to create field-specific non-empty validators
        def make_non_empty_validator(field_name: str):
            def validate(s: str) -> str:
                stripped = s.strip()
                if not stripped:
                    raise ConfigurationError(f"Field '{field_name}' cannot be empty")
                return stripped

            return validate

        # Parse required fields
        source = parse_field(
            transfer_data,
            FieldSpec(
                "source",
                str,
                required=True,
                transform=make_non_empty_validator("source"),
            ),
        )

        target = parse_field(
            transfer_data,
            FieldSpec(
                "target",
                str,
                required=True,
                transform=make_non_empty_validator("target"),
            ),
        )

        # Parse optional fields with defaults
        source_tag = parse_field(
            transfer_data,
            FieldSpec("source_tag", str, transform=str.strip),
            default="latest",
        )

        target_tag = parse_field(
            transfer_data,
            FieldSpec(
                "target_tag",
                str,
                allow_none=True,
                transform=lambda s: s.strip() if s else None,
            ),
        )

        verify_digest = parse_field(
            transfer_data, FieldSpec("verify_digest", bool, allow_none=True)
        )

        preserve_architectures = parse_field(
            transfer_data, FieldSpec("preserve_architectures", bool, allow_none=True)
        )

        # Parse platforms (list requires element validation)
        platforms = parse_field(
            transfer_data, FieldSpec("platforms", list, allow_none=True)
        )
        if platforms is not None:
            # Validate all elements are strings
            if not all(isinstance(p, str) for p in platforms):
                raise ConfigurationError("All platform entries must be strings")

        return BatchTransferRequest(
            source=source,
            target=target,
            source_tag=source_tag,
            target_tag=target_tag,
            verify_digest=verify_digest,
            preserve_architectures=preserve_architectures,
            platforms=platforms,
        )

    @staticmethod
    def _parse_settings(settings_data: Dict) -> BatchSettings:
        """Parse batch settings configuration.

        Args:
            settings_data: Settings configuration dictionary

        Returns:
            BatchSettings with parsed configuration

        Raises:
            ConfigurationError: If settings configuration is invalid
        """
        settings = BatchSettings()

        # Parse simple fields using declarative specifications
        settings.concurrent_transfers = parse_field(
            settings_data,
            FieldSpec("concurrent_transfers", int),
            default=settings.concurrent_transfers,
        )

        settings.retry_attempts = parse_field(
            settings_data,
            FieldSpec("retry_attempts", int),
            default=settings.retry_attempts,
        )

        settings.verify_digests = parse_field(
            settings_data,
            FieldSpec("verify_digests", bool),
            default=settings.verify_digests,
        )

        settings.region = parse_field(
            settings_data,
            FieldSpec(
                "region",
                str,
                allow_none=True,
                transform=lambda s: s.strip() if s else None,
            ),
            default=settings.region,
        )

        settings.registry_id = parse_field(
            settings_data,
            FieldSpec(
                "registry_id",
                str,
                allow_none=True,
                transform=lambda s: s.strip() if s else None,
            ),
            default=settings.registry_id,
        )

        settings.preserve_architectures = parse_field(
            settings_data,
            FieldSpec("preserve_architectures", bool, allow_none=True),
            default=settings.preserve_architectures,
        )

        # Parse target_platforms (list validation requires special handling)
        platforms = parse_field(
            settings_data,
            FieldSpec("target_platforms", list, allow_none=True),
            default=settings.target_platforms,
        )
        if platforms is not None:
            # Validate all elements are strings
            if not all(isinstance(p, str) for p in platforms):
                raise ConfigurationError("All target_platforms entries must be strings")
        settings.target_platforms = platforms

        return settings

    @staticmethod
    def validate_config_schema(config_path: Union[str, Path]) -> bool:
        """Validate configuration file schema without full parsing.

        Args:
            config_path: Path to configuration file

        Returns:
            True if schema is valid

        Raises:
            ConfigurationError: If schema is invalid
        """
        try:
            BatchConfigService.load_from_file(config_path)
            return True
        except ConfigurationError:
            raise

    @staticmethod
    def lazy_load_from_file(
        config_path: Union[str, Path],
    ) -> Generator[BatchTransferRequest, None, BatchSettings]:
        """Lazily load batch transfer requests from YAML file.

        This generator yields individual BatchTransferRequests as they're parsed,
        allowing for memory-efficient processing of large batch configurations.

        Args:
            config_path: Path to YAML configuration file

        Yields:
            BatchTransferRequest: Individual transfer configurations

        Returns:
            BatchSettings: Final batch settings after all transfers processed

        Raises:
            ConfigurationError: If file cannot be read or parsed
        """
        config_path = Path(config_path)

        if not config_path.exists():
            raise ConfigurationError(f"Configuration file not found: {config_path}")

        try:
            with config_path.open("r", encoding="utf-8") as f:
                config_data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise ConfigurationError(f"Invalid YAML format: {e}")
        except OSError as e:
            raise ConfigurationError(f"Cannot read configuration file: {e}")

        # Validate and parse configuration
        BatchConfigService._validate_config_data(config_data)

        # Parse settings first (needed for validation)
        settings_data = config_data.get("settings", {})
        settings = BatchConfigService._parse_settings(settings_data)

        # Yield transfers one by one for memory efficiency
        transfers_data = config_data["transfers"]
        for transfer_data in transfers_data:
            try:
                # Parse individual transfer
                transfer = BatchConfigService._parse_transfer(transfer_data)
                yield transfer
            except (KeyError, ValueError) as e:
                raise ConfigurationError(f"Invalid transfer configuration: {e}")

        return settings

    @staticmethod
    def lazy_load_transfers_from_data(
        config_data: Dict,
    ) -> Generator[BatchTransferRequest, None, None]:
        """Lazily yield transfer requests from already loaded configuration data.

        Args:
            config_data: Already parsed YAML configuration data

        Yields:
            BatchTransferRequest: Individual transfer configurations
        """
        transfers_data = config_data.get("transfers", [])
        for transfer_data in transfers_data:
            try:
                transfer = BatchConfigService._parse_transfer(transfer_data)
                yield transfer
            except (KeyError, ValueError) as e:
                logger.warning(f"Skipping invalid transfer configuration: {e}")
                continue

    @staticmethod
    def load_streaming_from_file(
        config_path: Union[str, Path],
    ) -> StreamingBatchRequest:
        """Load a streaming batch request for memory-efficient processing.

        Args:
            config_path: Path to YAML configuration file

        Returns:
            StreamingBatchRequest: Memory-efficient batch request with generator
        """
        config_path = Path(config_path)

        if not config_path.exists():
            raise ConfigurationError(f"Configuration file not found: {config_path}")

        try:
            with config_path.open("r", encoding="utf-8") as f:
                config_data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise ConfigurationError(f"Invalid YAML format: {e}")
        except OSError as e:
            raise ConfigurationError(f"Cannot read configuration file: {e}")

        # Validate and parse configuration
        BatchConfigService._validate_config_data(config_data)

        # Parse settings
        settings_data = config_data.get("settings", {})
        settings = BatchConfigService._parse_settings(settings_data)

        # Create generator for transfers
        transfer_generator = BatchConfigService.lazy_load_transfers_from_data(
            config_data
        )

        # Get total count for progress tracking (if needed)
        total_count = len(config_data.get("transfers", []))

        return StreamingBatchRequest(
            transfer_generator=transfer_generator,
            settings=settings,
            total_count=total_count,
        )

    @staticmethod
    def generate_example_config() -> str:
        """Generate example YAML configuration.

        Returns:
            Example YAML configuration as string
        """
        return """# ECReshore batch transfer configuration
transfers:
  # Basic transfer - uses 'latest' tag by default
  - source: nginx
    target: my-nginx-repo

  # Transfer with specific tags
  - source: redis
    source_tag: "6.2"
    target: my-redis-repo
    target_tag: stable

  # Transfer with colon notation (equivalent to above)
  - source: postgres:13
    target: my-postgres-repo:production

  # Transfer with digest verification disabled
  - source: alpine
    target: my-alpine-repo
    verify_digest: false

  # Transfer with multi-architecture support
  - source: nginx
    target: my-multi-arch-nginx
    preserve_architectures: true
    platforms:
      - linux/amd64
      - linux/arm64

settings:
  # Number of concurrent transfers (default: 3)
  concurrent_transfers: 2

  # Number of retry attempts for failed transfers (default: 3)
  retry_attempts: 5

  # Whether to verify image digests after transfer (default: true)
  verify_digests: true

  # Preserve all architectures for multi-arch images (default: false)
  preserve_architectures: false

  # Default target platforms when preserve_architectures is true
  target_platforms:
    - linux/amd64
    - linux/arm64

  # AWS region for ECR (optional, uses standard AWS region resolution)
  # region: us-west-2

  # AWS account ID for ECR (optional, uses default if not specified)
  registry_id: "123456789012"
"""
