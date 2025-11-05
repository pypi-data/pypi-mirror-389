"""Logging configuration utilities."""

import io
import logging
import sys

import structlog
from rich.console import Console
from rich.logging import RichHandler


def setup_logging(verbosity: int = 0) -> None:
    """Setup logging with rich formatting."""
    stderr_console = Console(stderr=True)

    if verbosity >= 2:
        level = logging.DEBUG
    elif verbosity == 1:
        level = logging.INFO
    else:
        level = logging.ERROR

    logging.basicConfig(
        level=level,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(console=stderr_console, rich_tracebacks=True)],
    )

    # Reduce noise from boto3/urllib3
    logging.getLogger("boto3").setLevel(logging.WARNING)
    logging.getLogger("botocore").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)


def setup_structured_logging():
    """Configure structlog for JSON output and suppress all console output."""
    # Clear any existing handlers
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Configure structured logging to only show structlog messages
    class StructlogOnlyFilter(logging.Filter):
        def filter(self, record):
            # Allow messages that contain JSON (structlog output)
            return isinstance(record.msg, str) and (
                "{" in record.msg and '"event"' in record.msg
            )

    # Add stdout handler with filter for JSON only
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter("%(message)s"))
    handler.addFilter(StructlogOnlyFilter())
    root_logger.addHandler(handler)
    root_logger.setLevel(logging.INFO)

    # Suppress Rich console output globally by redirecting Rich console to null
    # Replace the global console with a null console
    import ecreshore.cli

    ecreshore.cli.console = Console(file=io.StringIO(), force_terminal=False)

    # Configure structlog
    structlog.configure(
        processors=[
            structlog.stdlib.add_log_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer(),
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
