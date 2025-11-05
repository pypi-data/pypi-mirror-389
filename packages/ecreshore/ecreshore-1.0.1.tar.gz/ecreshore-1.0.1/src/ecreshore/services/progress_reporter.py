"""Progress reporting service for transfer operations."""

import logging
from typing import Any, Dict, Optional, Protocol
from rich.console import Console


logger = logging.getLogger(__name__)

# Global flag to suppress console output when in log mode
_SUPPRESS_CONSOLE_OUTPUT = False


def set_console_suppression(suppress: bool) -> None:
    """Set global console output suppression."""
    global _SUPPRESS_CONSOLE_OUTPUT
    _SUPPRESS_CONSOLE_OUTPUT = suppress


class ProgressCallback(Protocol):
    """Protocol for progress callback functions."""

    def __call__(self, message: str, **kwargs) -> None:
        """Called with progress updates."""
        ...


class ProgressReporter:
    """Service for reporting transfer operation progress."""

    def __init__(self, console: Optional[Console] = None, verbose: bool = False):
        """Initialize progress reporter.

        Args:
            console: Rich console instance, creates new one if None
            verbose: Enable verbose progress reporting
        """
        self.console = console or Console()
        self.verbose = verbose
        self._callbacks: Dict[str, ProgressCallback] = {}

    def add_callback(self, name: str, callback: ProgressCallback) -> None:
        """Add a progress callback.

        Args:
            name: Callback identifier
            callback: Function to call with progress updates
        """
        self._callbacks[name] = callback

    def remove_callback(self, name: str) -> None:
        """Remove a progress callback.

        Args:
            name: Callback identifier to remove
        """
        self._callbacks.pop(name, None)

    def _notify_callbacks(self, message: str, **kwargs) -> None:
        """Notify all registered callbacks of progress."""
        for callback in self._callbacks.values():
            try:
                callback(message, **kwargs)
            except Exception as e:
                logger.warning(f"Progress callback failed: {e}")

    def info(self, message: str, **kwargs) -> None:
        """Report informational progress message.

        Args:
            message: Progress message
            **kwargs: Additional context data
        """
        if not _SUPPRESS_CONSOLE_OUTPUT:
            self.console.print(f"[blue]ℹ[/blue] {message}")
        if self.verbose and kwargs:
            logger.debug(f"Progress info: {message}, context: {kwargs}")
        self._notify_callbacks(message, level="info", **kwargs)

    def success(self, message: str, **kwargs) -> None:
        """Report successful operation.

        Args:
            message: Success message
            **kwargs: Additional context data
        """
        if not _SUPPRESS_CONSOLE_OUTPUT:
            self.console.print(f"[green]✓[/green] {message}")
        if self.verbose and kwargs:
            logger.debug(f"Progress success: {message}, context: {kwargs}")
        self._notify_callbacks(message, level="success", **kwargs)

    def warning(self, message: str, **kwargs) -> None:
        """Report warning condition.

        Args:
            message: Warning message
            **kwargs: Additional context data
        """
        if not _SUPPRESS_CONSOLE_OUTPUT:
            self.console.print(f"[yellow]⚠[/yellow] {message}")
        if self.verbose and kwargs:
            logger.debug(f"Progress warning: {message}, context: {kwargs}")
        self._notify_callbacks(message, level="warning", **kwargs)

    def error(self, message: str, **kwargs) -> None:
        """Report error condition.

        Args:
            message: Error message
            **kwargs: Additional context data
        """
        if not _SUPPRESS_CONSOLE_OUTPUT:
            self.console.print(f"[red]✗[/red] {message}")
        if self.verbose and kwargs:
            logger.debug(f"Progress error: {message}, context: {kwargs}")
        self._notify_callbacks(message, level="error", **kwargs)

    def status(self, message: str) -> Any:
        """Create a status context manager for long-running operations.

        Args:
            message: Status message to display

        Returns:
            Rich status context manager
        """
        return self.console.status(message)

    def start_transfer(
        self,
        source_image: str,
        target_repository: str,
        source_tag: str = "latest",
        target_tag: str = "latest",
    ) -> None:
        """Report start of transfer operation.

        Args:
            source_image: Source image repository
            target_repository: Target repository name
            source_tag: Source image tag
            target_tag: Target image tag
        """
        message = f"Starting transfer: {source_image}:{source_tag} → {target_repository}:{target_tag}"
        if not _SUPPRESS_CONSOLE_OUTPUT:
            self.console.print(f"[bold blue]{message}[/bold blue]")
        self._notify_callbacks(
            message,
            level="transfer_start",
            source_image=source_image,
            target_repository=target_repository,
            source_tag=source_tag,
            target_tag=target_tag,
        )

    def transfer_complete(
        self,
        source_image: str,
        target_repository: str,
        source_tag: str = "latest",
        target_tag: str = "latest",
        success: bool = True,
    ) -> None:
        """Report completion of transfer operation.

        Args:
            source_image: Source image repository
            target_repository: Target repository name
            source_tag: Source image tag
            target_tag: Target image tag
            success: Whether transfer succeeded
        """
        if success:
            message = f"Transfer completed: {source_image}:{source_tag} → {target_repository}:{target_tag}"
            if not _SUPPRESS_CONSOLE_OUTPUT:
                self.console.print(f"[bold green]{message}[/bold green]")
            level = "transfer_success"
        else:
            message = f"Transfer failed: {source_image}:{source_tag} → {target_repository}:{target_tag}"
            if not _SUPPRESS_CONSOLE_OUTPUT:
                self.console.print(f"[bold red]{message}[/bold red]")
            level = "transfer_failed"

        self._notify_callbacks(
            message,
            level=level,
            source_image=source_image,
            target_repository=target_repository,
            source_tag=source_tag,
            target_tag=target_tag,
            success=success,
        )

    def pull_progress(self, repository: str, tag: str) -> None:
        """Report image pull progress.

        Args:
            repository: Image repository being pulled
            tag: Image tag being pulled
        """
        message = f"Pulling {repository}:{tag}"
        if self.verbose:
            self.info(message)
        self._notify_callbacks(message, level="pull", repository=repository, tag=tag)

    def tag_progress(self, source: str, target: str) -> None:
        """Report image tagging progress.

        Args:
            source: Source image name
            target: Target image name
        """
        message = f"Tagged {source} → {target}"
        if self.verbose:
            self.info(message)
        self._notify_callbacks(message, level="tag", source=source, target=target)

    def push_progress(self, repository: str, tag: str) -> None:
        """Report image push progress.

        Args:
            repository: Repository being pushed to
            tag: Tag being pushed
        """
        message = f"Pushing {repository}:{tag}"
        if self.verbose:
            self.info(message)
        self._notify_callbacks(message, level="push", repository=repository, tag=tag)

    def verification_progress(
        self, source_digest: Optional[str], target_digest: Optional[str]
    ) -> None:
        """Report digest verification progress.

        Args:
            source_digest: Source image digest
            target_digest: Target image digest
        """
        if source_digest and target_digest:
            if source_digest == target_digest:
                self.success("Image digest verified")
                level = "verification_success"
            else:
                self.warning("Image digest mismatch detected")
                level = "verification_failed"
        else:
            self.warning("Could not verify image digest")
            level = "verification_unavailable"

        self._notify_callbacks(
            "Digest verification completed",
            level=level,
            source_digest=source_digest,
            target_digest=target_digest,
        )
