"""Batch processing service for concurrent image transfers with async rate limiting."""

import asyncio
import logging
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from .batch_config import BatchRequest, BatchTransferRequest, BatchSettings
from .batch_progress import BatchProgressReporter
from .hybrid_transfer_service import HybridTransferService
from .transfer_service import TransferResult
from .transfer_request_builder import TransferRequestBuilder

logger = logging.getLogger(__name__)


@dataclass
class BatchResult:
    """Result of a batch processing operation."""

    batch_request: BatchRequest
    transfer_results: List[TransferResult]
    success_count: int
    failure_count: int
    total_duration: float
    total_retries: int

    @property
    def success_rate(self) -> float:
        """Calculate success rate as percentage."""
        total = len(self.transfer_results)
        return (self.success_count / total * 100) if total > 0 else 0

    @property
    def overall_success(self) -> bool:
        """Check if entire batch succeeded."""
        return self.failure_count == 0


class AsyncRateLimiter:
    """Async rate limiter using asyncio.Semaphore for controlling concurrent operations."""

    def __init__(self, max_concurrent: int, min_interval: float = 0.1):
        """Initialize async rate limiter.

        Args:
            max_concurrent: Maximum concurrent operations
            min_interval: Minimum interval between operation starts in seconds
        """
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.min_interval = min_interval
        self._last_start_times: List[float] = []
        self._lock = asyncio.Lock()

    async def acquire(self) -> None:
        """Acquire rate limiter permit asynchronously."""
        await self.semaphore.acquire()

        # Ensure minimum interval between starts
        async with self._lock:
            current_time = time.time()

            # Clean up old timestamps (older than min_interval)
            cutoff_time = current_time - self.min_interval
            self._last_start_times = [
                t for t in self._last_start_times if t > cutoff_time
            ]

            # If we have recent starts, wait before proceeding
            if self._last_start_times:
                time_since_last = current_time - max(self._last_start_times)
                if time_since_last < self.min_interval:
                    wait_time = self.min_interval - time_since_last
                    await asyncio.sleep(wait_time)

            # Record this start time
            self._last_start_times.append(time.time())

    def release(self) -> None:
        """Release rate limiter permit."""
        self.semaphore.release()

    async def __aenter__(self):
        """Async context manager entry."""
        await self.acquire()
        return self

    async def __aexit__(self, _exc_type, _exc_val, _exc_tb):
        """Async context manager exit."""
        self.release()


class BatchProcessor:
    """Service for processing batch transfer operations with concurrency and rate limiting."""

    def __init__(self, transfer_service: Optional[HybridTransferService] = None):
        """Initialize batch processor.

        Args:
            transfer_service: Transfer service instance, creates default if None
        """
        self.transfer_service = transfer_service

    async def process_batch(
        self,
        batch_request: BatchRequest,
        progress_reporter: Optional[BatchProgressReporter] = None,
        force: bool = False,
    ) -> BatchResult:
        """Process a batch of image transfers with async concurrency and progress reporting.

        Args:
            batch_request: Batch request to process
            progress_reporter: Progress reporter for UI updates

        Returns:
            BatchResult with operation details
        """
        start_time = time.time()

        # Initialize progress reporter if not provided
        if progress_reporter is None:
            progress_reporter = BatchProgressReporter(verbose=True)

        progress_reporter.start_batch(batch_request)

        # Configure transfer service
        transfer_service = self._get_transfer_service(batch_request.settings)

        # Setup async rate limiting
        rate_limiter = AsyncRateLimiter(
            max_concurrent=batch_request.settings.concurrent_transfers,
            min_interval=0.1,  # 100ms minimum between starts
        )

        # Process transfers
        transfer_results = []
        total_retries = 0

        try:
            with progress_reporter.live_display():
                if batch_request.settings.concurrent_transfers == 1:
                    # Sequential processing
                    transfer_results = await self._process_sequential(
                        batch_request, transfer_service, progress_reporter, force
                    )
                else:
                    # Async concurrent processing
                    transfer_results = await self._process_concurrent_async(
                        batch_request,
                        transfer_service,
                        progress_reporter,
                        rate_limiter,
                        force,
                    )

                # Calculate retry statistics
                total_retries = sum(
                    getattr(result, "retry_count", 0) for result in transfer_results
                )

        finally:
            progress_reporter.finish_batch()

        # Build result
        end_time = time.time()
        success_count = sum(1 for r in transfer_results if r.success and not r.skipped)
        failure_count = sum(1 for r in transfer_results if not r.success)

        return BatchResult(
            batch_request=batch_request,
            transfer_results=transfer_results,
            success_count=success_count,
            failure_count=failure_count,
            total_duration=end_time - start_time,
            total_retries=total_retries,
        )

    def _get_transfer_service(self, settings: BatchSettings) -> HybridTransferService:
        """Get or create transfer service with batch settings.

        Args:
            settings: Batch settings

        Returns:
            Configured transfer service
        """
        if self.transfer_service is not None:
            return self.transfer_service

        return HybridTransferService(
            region_name=settings.region,
            registry_id=settings.registry_id,
        )

    async def _process_sequential(
        self,
        batch_request: BatchRequest,
        transfer_service: HybridTransferService,
        progress_reporter: BatchProgressReporter,
        force: bool = False,
    ) -> List[TransferResult]:
        """Process transfers sequentially (but still with async operations).

        Args:
            batch_request: Batch request
            transfer_service: Transfer service
            progress_reporter: Progress reporter

        Returns:
            List of transfer results
        """
        results = []

        for i, batch_transfer in enumerate(batch_request.transfers):
            transfer_id = f"transfer_{i}"

            try:
                result = await self._execute_single_transfer_async(
                    batch_transfer,
                    transfer_service,
                    progress_reporter,
                    transfer_id,
                    batch_request.settings,
                    force,
                )
                results.append(result)

            except Exception as e:
                logger.error(f"Unexpected error in transfer {transfer_id}: {e}")
                progress_reporter.complete_transfer(transfer_id, False, str(e))

                # Create failed result using builder
                request = TransferRequestBuilder.for_batch_transfer(
                    batch_transfer, batch_request.settings, force
                )
                failed_result = TransferResult(
                    request=request,
                    success=False,
                    error_message=f"Unexpected error: {e}",
                )
                failed_result.retry_count = 0
                results.append(failed_result)

        return results

    async def _process_concurrent_async(
        self,
        batch_request: BatchRequest,
        transfer_service: HybridTransferService,
        progress_reporter: BatchProgressReporter,
        rate_limiter: AsyncRateLimiter,
        force: bool = False,
    ) -> List[TransferResult]:
        """Process transfers concurrently using asyncio.gather.

        Args:
            batch_request: Batch request
            transfer_service: Transfer service
            progress_reporter: Progress reporter
            rate_limiter: Async rate limiter

        Returns:
            List of transfer results
        """
        # Create async tasks for all transfers
        tasks = []

        for i, batch_transfer in enumerate(batch_request.transfers):
            transfer_id = f"transfer_{i}"

            task = self._execute_single_transfer_with_rate_limit_async(
                batch_transfer,
                transfer_service,
                progress_reporter,
                transfer_id,
                batch_request.settings,
                rate_limiter,
                index=i,
                force=force,
            )
            tasks.append(task)

        # Execute all transfers concurrently and gather results
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results and handle exceptions
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                # Handle exception case
                transfer_id = f"transfer_{i}"
                logger.error(f"Unexpected error in transfer {transfer_id}: {result}")
                progress_reporter.complete_transfer(transfer_id, False, str(result))

                # Create failed result using builder
                batch_transfer = batch_request.transfers[i]
                request = TransferRequestBuilder.for_batch_transfer(
                    batch_transfer, batch_request.settings, force
                )
                failed_result = TransferResult(
                    request=request,
                    success=False,
                    error_message=f"Unexpected error: {result}",
                )
                failed_result.retry_count = 0
                processed_results.append(failed_result)
            else:
                processed_results.append(result)

        return processed_results

    async def _execute_single_transfer_with_rate_limit_async(
        self,
        batch_transfer: BatchTransferRequest,
        transfer_service: HybridTransferService,
        progress_reporter: BatchProgressReporter,
        transfer_id: str,
        settings: BatchSettings,
        rate_limiter: AsyncRateLimiter,
        index: int,
        force: bool = False,
    ) -> TransferResult:
        """Execute single transfer with async rate limiting.

        Args:
            batch_transfer: Transfer to execute
            transfer_service: Transfer service
            progress_reporter: Progress reporter
            transfer_id: Transfer identifier
            settings: Batch settings
            rate_limiter: Async rate limiter
            index: Transfer index for ordering

        Returns:
            Transfer result
        """
        # Acquire rate limit permit asynchronously
        async with rate_limiter:
            return await self._execute_single_transfer_async(
                batch_transfer,
                transfer_service,
                progress_reporter,
                transfer_id,
                settings,
                force,
            )

    async def _execute_single_transfer_async(
        self,
        batch_transfer: BatchTransferRequest,
        transfer_service: HybridTransferService,
        progress_reporter: BatchProgressReporter,
        transfer_id: str,
        settings: BatchSettings,
        force: bool = False,
    ) -> TransferResult:
        """Execute a single transfer with async progress reporting.

        Args:
            batch_transfer: Transfer to execute
            transfer_service: Transfer service
            progress_reporter: Progress reporter
            transfer_id: Transfer identifier
            settings: Batch settings

        Returns:
            Transfer result
        """
        # Create transfer request using builder pattern
        request = TransferRequestBuilder.for_batch_transfer(
            batch_transfer, settings, force
        )

        # Start transfer
        progress_reporter.start_transfer(transfer_id)

        try:
            # Update progress through different operations
            progress_reporter.update_transfer_operation(transfer_id, "Pulling", 0)

            # For retry tracking, we need to wrap the transfer
            retry_count = 0

            # Execute transfer using async service
            result = await transfer_service.transfer_image(request)

            # Add retry count to result
            result.retry_count = retry_count

            # Report completion based on result type
            if result.skipped:
                skip_reason = result.skip_reason or "Unknown reason"
                progress_reporter.skip_transfer(transfer_id, skip_reason)
            elif result.success:
                progress_reporter.complete_transfer(transfer_id, True)
            else:
                progress_reporter.complete_transfer(
                    transfer_id, False, result.error_message
                )

            return result

        except Exception as e:
            error_msg = str(e)
            progress_reporter.complete_transfer(transfer_id, False, error_msg)

            # Create failed result
            failed_result = TransferResult(
                request=request,
                success=False,
                error_message=error_msg,
            )
            failed_result.retry_count = retry_count
            return failed_result

    def validate_batch_prerequisites(self, batch_request: BatchRequest) -> bool:
        """Validate that batch can be executed.

        Args:
            batch_request: Batch request to validate

        Returns:
            True if batch can be executed
        """
        if not batch_request.transfers:
            logger.error("Batch request contains no transfers")
            return False

        # Create temporary transfer service for validation
        transfer_service = self._get_transfer_service(batch_request.settings)

        try:
            return transfer_service.validate_prerequisites()
        except Exception as e:
            logger.error(f"Batch prerequisites validation failed: {e}")
            return False

    def estimate_batch_duration(self, batch_request: BatchRequest) -> float:
        """Estimate batch processing duration in seconds.

        Args:
            batch_request: Batch request

        Returns:
            Estimated duration in seconds
        """
        # Base estimate per transfer (pulling + tagging + pushing)
        base_transfer_time = 30.0  # seconds

        # Adjust for concurrency
        concurrent = batch_request.settings.concurrent_transfers
        total_transfers = len(batch_request.transfers)

        if concurrent >= total_transfers:
            # All transfers can run in parallel
            estimated_time = base_transfer_time
        else:
            # Some transfers will wait
            parallel_batches = (total_transfers + concurrent - 1) // concurrent
            estimated_time = base_transfer_time * parallel_batches

        # Add overhead for retries
        retry_overhead = batch_request.settings.retry_attempts * 0.3
        estimated_time *= 1 + retry_overhead

        # Add batch coordination overhead
        estimated_time += 5.0

        return estimated_time

    def dry_run_batch(self, batch_request: BatchRequest) -> Dict[str, Any]:
        """Perform a dry run of batch operation without executing transfers.

        Args:
            batch_request: Batch request to analyze

        Returns:
            Dictionary with dry run analysis
        """
        analysis = {
            "total_transfers": len(batch_request.transfers),
            "concurrent_transfers": batch_request.settings.concurrent_transfers,
            "retry_attempts": batch_request.settings.retry_attempts,
            "verify_digests": batch_request.settings.verify_digests,
            "estimated_duration_seconds": self.estimate_batch_duration(batch_request),
            "prerequisites_valid": False,
            "transfers": [],
        }

        # Validate prerequisites
        try:
            analysis["prerequisites_valid"] = self.validate_batch_prerequisites(
                batch_request
            )
        except Exception as e:
            analysis["prerequisites_error"] = str(e)

        # Analyze each transfer
        for i, transfer in enumerate(batch_request.transfers):
            transfer_analysis = {
                "index": i,
                "source": f"{transfer.source}:{transfer.source_tag}",
                "target": f"{transfer.target}:{transfer.target_tag}",
                "verify_digest": transfer.verify_digest
                or batch_request.settings.verify_digests,
                "estimated_duration_seconds": 30.0,  # Base estimate
            }
            analysis["transfers"].append(transfer_analysis)

        return analysis

    async def load_and_validate_config(self, config_file: str) -> dict:
        """Load and validate batch configuration without executing transfers.

        This method only loads the config and validates prerequisites,
        returning the same structure as execute_batch_enhanced but without
        executing any transfers.

        Args:
            config_file: Path to batch configuration file

        Returns:
            Dict containing:
                - config_loaded: bool
                - config_file: str
                - batch_request: BatchRequest (if loaded)
                - prerequisites_valid: bool (if config loaded)
                - error_message: str (if error occurred)
                - error_type: str (if error occurred)
        """
        from .batch_config import BatchConfigService

        result = {
            "config_loaded": False,
            "config_file": config_file,
            "batch_request": None,
            "prerequisites_valid": False,
            "error_message": None,
            "error_type": None,
        }

        try:
            # Load configuration
            batch_request = BatchConfigService.load_from_file(config_file)
            result["config_loaded"] = True
            result["batch_request"] = batch_request

            # Validate prerequisites
            prerequisites_valid = self.validate_batch_prerequisites(batch_request)
            result["prerequisites_valid"] = prerequisites_valid

            if not prerequisites_valid:
                result["error_message"] = "Prerequisites validation failed"
                result["error_type"] = "prerequisites"

        except Exception as e:
            result["error_message"] = str(e)
            result["error_type"] = "config_load"

        return result

    async def execute_batch_enhanced(
        self,
        config_file: str,
        dry_run: bool = False,
        use_rich_ui: bool = False,
        force: bool = False,
        progress_reporter=None,
    ) -> dict:
        """Execute enhanced batch operation with comprehensive result data.

        This method contains the pure business logic for batch execution,
        separated from UI concerns for testability.

        Args:
            config_file: Path to batch configuration file
            dry_run: If True, validate and analyze but don't execute transfers
            use_rich_ui: If True, use rich UI components for progress display
            force: If True, disable skip-if-present for all transfers

        Returns:
            Dict containing:
                - config_loaded: bool
                - config_file: str
                - batch_request: BatchRequest (if loaded)
                - prerequisites_valid: bool (if config loaded)
                - dry_run_result: dict (if dry_run=True)
                - batch_result: BatchResult (if executed)
                - error_message: str (if error occurred)
                - error_type: str (if error occurred)
        """
        from .batch_config import BatchConfigService

        result = {
            "config_loaded": False,
            "config_file": config_file,
            "batch_request": None,
            "prerequisites_valid": False,
            "dry_run_result": None,
            "batch_result": None,
            "error_message": None,
            "error_type": None,
        }

        try:
            # Load configuration
            batch_request = BatchConfigService.load_from_file(config_file)
            result["config_loaded"] = True
            result["batch_request"] = batch_request

            # Validate prerequisites
            prerequisites_valid = self.validate_batch_prerequisites(batch_request)
            result["prerequisites_valid"] = prerequisites_valid

            if not prerequisites_valid:
                result["error_message"] = "Prerequisites validation failed"
                result["error_type"] = "prerequisites"
                return result

            # Handle dry run
            if dry_run:
                dry_run_result = self.dry_run_batch(batch_request)
                result["dry_run_result"] = dry_run_result
                return result

            # Execute batch transfers
            try:
                if progress_reporter:
                    # Use provided progress reporter for UI integration
                    batch_result = await self.process_batch(
                        batch_request, progress_reporter, force
                    )
                else:
                    # Create minimal progress reporter for business logic only
                    from .batch_progress import BatchProgressReporter
                    from rich.console import Console

                    minimal_console = Console(
                        file=open("/dev/null", "w"), force_terminal=False
                    )
                    minimal_progress = BatchProgressReporter(
                        console=minimal_console,
                        verbose=False,
                        simple_mode=True,
                        output_mode="log",
                    )
                    batch_result = await self.process_batch(
                        batch_request, minimal_progress, force
                    )
                result["batch_result"] = batch_result
            except Exception as batch_error:
                logger.error(
                    f"Batch processing failed: {type(batch_error).__name__}: {batch_error}"
                )
                import traceback

                traceback.print_exc()
                raise

        except Exception as e:
            result["error_message"] = str(e)
            result["error_type"] = type(e).__name__

        return result
