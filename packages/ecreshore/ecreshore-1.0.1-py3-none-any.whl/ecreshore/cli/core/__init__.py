"""Core ecreshore commands module.

This module contains the primary functionality commands that users interact with most:

- **auth-test**: Test AWS ECR authentication and connectivity
  - Validates ECR credentials and access
  - Shows registry URL on successful authentication
  - Minimal complexity, async implementation

- **copy**: Copy individual container images to ECR
  - Smart multi-architecture detection and preservation
  - Skip-if-present functionality with digest verification
  - Rich progress display with terminal auto-detection
  - Comprehensive platform and tag handling
  - Force transfer and custom repository naming options

- **batch**: Execute multiple image transfers from YAML configuration
  - Processes multiple transfers with progress tracking
  - Support for dry-run preview mode
  - Multiple output formats (console with rich UI, structured JSON logs)
  - Advanced error handling and keyboard interrupt support
  - Real-time progress reporting with skip tracking

These commands represent the core business logic of ecreshore and are the most
frequently used by end users. They have been designed with comprehensive error
handling, rich user interfaces, and async operation support.
"""
