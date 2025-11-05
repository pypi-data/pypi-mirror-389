"""Output mode definitions and constants for batch operations."""

from enum import Enum


class OutputMode(Enum):
    """Available output modes for batch operations."""

    CONSOLE = "console"
    LOG = "log"


OUTPUT_MODE_CONSOLE = OutputMode.CONSOLE.value
OUTPUT_MODE_LOG = OutputMode.LOG.value
