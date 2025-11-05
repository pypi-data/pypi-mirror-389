"""Transfer resumption service for handling partial transfers and recovery."""

import json
import logging
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional
from hashlib import sha256

from .transfer_service import TransferRequest
from .batch_config import BatchRequest, BatchTransferRequest

logger = logging.getLogger(__name__)

DEFAULT_STATE_DIR = ".ecreshore_state"
DEFAULT_MAX_STATE_AGE_HOURS = 24


@dataclass
class TransferState:
    """State information for a transfer operation."""

    request: TransferRequest
    status: str  # "pending", "in_progress", "completed", "failed"
    start_time: float
    end_time: Optional[float] = None
    error_message: Optional[str] = None
    retry_count: int = 0
    checksum: Optional[str] = None  # For resume validation
    partial_layers: List[str] = None  # Docker layers already pulled/pushed

    def __post_init__(self):
        if self.partial_layers is None:
            self.partial_layers = []


@dataclass
class BatchState:
    """State information for a batch operation."""

    batch_request: BatchRequest
    batch_id: str
    start_time: float
    transfers: Dict[str, TransferState]
    completed_count: int = 0
    failed_count: int = 0

    @property
    def total_count(self) -> int:
        """Get total number of transfers."""
        return len(self.transfers)

    @property
    def pending_transfers(self) -> List[str]:
        """Get list of pending transfer IDs."""
        return [
            tid
            for tid, state in self.transfers.items()
            if state.status in ["pending", "failed"]
        ]

    @property
    def is_complete(self) -> bool:
        """Check if batch is complete."""
        return self.completed_count + self.failed_count == self.total_count


class ResumeService:
    """Service for managing transfer state and resumption capabilities."""

    def __init__(
        self,
        state_dir: Optional[str] = None,
        max_state_age_hours: float = DEFAULT_MAX_STATE_AGE_HOURS,
    ):
        """Initialize resume service.

        Args:
            state_dir: Directory for storing state files
            max_state_age_hours: Maximum age of state files to consider valid
        """
        self.state_dir = Path(state_dir or DEFAULT_STATE_DIR)
        self.max_state_age_seconds = max_state_age_hours * 3600

        # Ensure state directory exists
        self.state_dir.mkdir(exist_ok=True)

        # Clean up old state files
        self._cleanup_old_state_files()

    def generate_batch_id(self, batch_request: BatchRequest) -> str:
        """Generate unique ID for batch request.

        Args:
            batch_request: Batch request

        Returns:
            Unique batch ID
        """
        # Create hash based on transfer details
        content = []
        for transfer in batch_request.transfers:
            content.append(
                f"{transfer.source}:{transfer.source_tag}->{transfer.target}:{transfer.target_tag}"
            )

        content_str = "|".join(sorted(content))
        hash_obj = sha256(content_str.encode())
        return hash_obj.hexdigest()[:16]

    def save_batch_state(self, batch_state: BatchState) -> None:
        """Save batch state to disk.

        Args:
            batch_state: Batch state to save
        """
        state_file = self.state_dir / f"batch_{batch_state.batch_id}.json"

        try:
            # Convert to serializable format
            state_dict = {
                "batch_id": batch_state.batch_id,
                "start_time": batch_state.start_time,
                "completed_count": batch_state.completed_count,
                "failed_count": batch_state.failed_count,
                "batch_request": self._serialize_batch_request(
                    batch_state.batch_request
                ),
                "transfers": {
                    tid: self._serialize_transfer_state(state)
                    for tid, state in batch_state.transfers.items()
                },
            }

            # Write atomically
            temp_file = state_file.with_suffix(".tmp")
            with temp_file.open("w") as f:
                json.dump(state_dict, f, indent=2)

            temp_file.rename(state_file)
            logger.debug(f"Saved batch state to {state_file}")

        except Exception as e:
            logger.error(f"Failed to save batch state: {e}")

    def load_batch_state(self, batch_id: str) -> Optional[BatchState]:
        """Load batch state from disk.

        Args:
            batch_id: Batch ID to load

        Returns:
            BatchState if found and valid, None otherwise
        """
        state_file = self.state_dir / f"batch_{batch_id}.json"

        if not state_file.exists():
            return None

        try:
            with state_file.open("r") as f:
                state_dict = json.load(f)

            # Check if state is too old
            if time.time() - state_dict["start_time"] > self.max_state_age_seconds:
                logger.info(f"State file {state_file} is too old, ignoring")
                return None

            # Deserialize batch request
            batch_request = self._deserialize_batch_request(state_dict["batch_request"])

            # Deserialize transfer states
            transfers = {
                tid: self._deserialize_transfer_state(state_data)
                for tid, state_data in state_dict["transfers"].items()
            }

            return BatchState(
                batch_request=batch_request,
                batch_id=state_dict["batch_id"],
                start_time=state_dict["start_time"],
                completed_count=state_dict["completed_count"],
                failed_count=state_dict["failed_count"],
                transfers=transfers,
            )

        except Exception as e:
            logger.error(f"Failed to load batch state from {state_file}: {e}")
            return None

    def list_resumable_batches(self) -> List[Dict[str, any]]:
        """List all resumable batch operations.

        Returns:
            List of resumable batch information
        """
        resumable = []

        for state_file in self.state_dir.glob("batch_*.json"):
            try:
                with state_file.open("r") as f:
                    state_dict = json.load(f)

                # Check age
                age_seconds = time.time() - state_dict["start_time"]
                if age_seconds > self.max_state_age_seconds:
                    continue

                # Calculate progress
                total = len(state_dict["transfers"])
                completed = state_dict["completed_count"]
                failed = state_dict["failed_count"]
                pending = total - completed - failed

                batch_info = {
                    "batch_id": state_dict["batch_id"],
                    "start_time": state_dict["start_time"],
                    "age_hours": age_seconds / 3600,
                    "total_transfers": total,
                    "completed": completed,
                    "failed": failed,
                    "pending": pending,
                    "can_resume": pending > 0,
                    "state_file": str(state_file),
                }

                resumable.append(batch_info)

            except Exception as e:
                logger.warning(f"Failed to read state file {state_file}: {e}")

        # Sort by start time (newest first)
        resumable.sort(key=lambda x: x["start_time"], reverse=True)
        return resumable

    def create_batch_state(
        self, batch_request: BatchRequest, batch_id: Optional[str] = None
    ) -> BatchState:
        """Create initial batch state for tracking.

        Args:
            batch_request: Batch request to track
            batch_id: Optional batch ID, generates one if not provided

        Returns:
            Initial batch state
        """
        if batch_id is None:
            batch_id = self.generate_batch_id(batch_request)

        transfers = {}
        for i, transfer in enumerate(batch_request.transfers):
            transfer_id = f"transfer_{i}"

            # Create transfer request
            verify_digest = transfer.verify_digest
            if verify_digest is None:
                verify_digest = batch_request.settings.verify_digests

            request = TransferRequest(
                source_image=transfer.source,
                source_tag=transfer.source_tag,
                target_repository=transfer.target,
                target_tag=transfer.target_tag,
                verify_digest=verify_digest,
            )

            transfers[transfer_id] = TransferState(
                request=request, status="pending", start_time=time.time()
            )

        return BatchState(
            batch_request=batch_request,
            batch_id=batch_id,
            start_time=time.time(),
            transfers=transfers,
        )

    def update_transfer_state(
        self,
        batch_state: BatchState,
        transfer_id: str,
        status: str,
        error_message: Optional[str] = None,
        retry_count: int = 0,
    ) -> None:
        """Update state of a specific transfer.

        Args:
            batch_state: Batch state to update
            transfer_id: Transfer ID to update
            status: New status
            error_message: Error message if failed
            retry_count: Current retry count
        """
        if transfer_id not in batch_state.transfers:
            logger.warning(f"Transfer {transfer_id} not found in batch state")
            return

        transfer_state = batch_state.transfers[transfer_id]
        old_status = transfer_state.status
        transfer_state.status = status
        transfer_state.retry_count = retry_count

        if error_message:
            transfer_state.error_message = error_message

        if status in ["completed", "failed"]:
            transfer_state.end_time = time.time()

        # Update batch counters
        if old_status != "completed" and status == "completed":
            batch_state.completed_count += 1
        elif old_status != "failed" and status == "failed":
            batch_state.failed_count += 1

        # Save updated state
        self.save_batch_state(batch_state)

    def cleanup_completed_batch(self, batch_id: str) -> bool:
        """Remove state file for completed batch.

        Args:
            batch_id: Batch ID to clean up

        Returns:
            True if cleaned up successfully
        """
        state_file = self.state_dir / f"batch_{batch_id}.json"

        try:
            if state_file.exists():
                state_file.unlink()
                logger.info(f"Cleaned up batch state: {batch_id}")
                return True
        except Exception as e:
            logger.error(f"Failed to cleanup batch state {batch_id}: {e}")

        return False

    def get_resume_recommendations(self, batch_state: BatchState) -> Dict[str, any]:
        """Get recommendations for resuming a batch operation.

        Args:
            batch_state: Batch state to analyze

        Returns:
            Dictionary with resume recommendations
        """
        pending_transfers = batch_state.pending_transfers
        failed_transfers = [
            tid
            for tid, state in batch_state.transfers.items()
            if state.status == "failed"
        ]

        recommendations = {
            "can_resume": len(pending_transfers) > 0,
            "total_transfers": batch_state.total_count,
            "completed": batch_state.completed_count,
            "failed": batch_state.failed_count,
            "pending": len(pending_transfers),
            "resume_strategy": "full",  # or 'failed_only'
            "estimated_time_saved_minutes": 0,
        }

        # Estimate time savings
        if batch_state.completed_count > 0:
            avg_transfer_time = 30  # seconds per transfer estimate
            time_saved = batch_state.completed_count * avg_transfer_time
            recommendations["estimated_time_saved_minutes"] = time_saved / 60

        # Recommend strategy
        if len(failed_transfers) > 0 and len(pending_transfers) == len(
            failed_transfers
        ):
            recommendations["resume_strategy"] = "failed_only"

        return recommendations

    def _cleanup_old_state_files(self) -> None:
        """Clean up old state files."""
        current_time = time.time()

        for state_file in self.state_dir.glob("batch_*.json"):
            try:
                # Check file modification time
                if (
                    current_time - state_file.stat().st_mtime
                    > self.max_state_age_seconds
                ):
                    state_file.unlink()
                    logger.debug(f"Cleaned up old state file: {state_file}")
            except Exception as e:
                logger.warning(f"Failed to cleanup old state file {state_file}: {e}")

    def _serialize_batch_request(self, batch_request: BatchRequest) -> Dict:
        """Serialize batch request to dictionary."""
        return {
            "transfers": [
                {
                    "source": t.source,
                    "source_tag": t.source_tag,
                    "target": t.target,
                    "target_tag": t.target_tag,
                    "verify_digest": t.verify_digest,
                }
                for t in batch_request.transfers
            ],
            "settings": {
                "concurrent_transfers": batch_request.settings.concurrent_transfers,
                "retry_attempts": batch_request.settings.retry_attempts,
                "verify_digests": batch_request.settings.verify_digests,
                "region": batch_request.settings.region,
                "registry_id": batch_request.settings.registry_id,
            },
        }

    def _deserialize_batch_request(self, data: Dict) -> BatchRequest:
        """Deserialize batch request from dictionary."""
        from .batch_config import BatchSettings  # Avoid circular import

        transfers = []
        for t_data in data["transfers"]:
            transfers.append(
                BatchTransferRequest(
                    source=t_data["source"],
                    source_tag=t_data["source_tag"],
                    target=t_data["target"],
                    target_tag=t_data["target_tag"],
                    verify_digest=t_data["verify_digest"],
                )
            )

        settings_data = data["settings"]
        settings = BatchSettings(
            concurrent_transfers=settings_data["concurrent_transfers"],
            retry_attempts=settings_data["retry_attempts"],
            verify_digests=settings_data["verify_digests"],
            region=settings_data["region"],
            registry_id=settings_data["registry_id"],
        )

        return BatchRequest(transfers=transfers, settings=settings)

    def _serialize_transfer_state(self, transfer_state: TransferState) -> Dict:
        """Serialize transfer state to dictionary."""
        return {
            "request": {
                "source_image": transfer_state.request.source_image,
                "source_tag": transfer_state.request.source_tag,
                "target_repository": transfer_state.request.target_repository,
                "target_tag": transfer_state.request.target_tag,
                "verify_digest": transfer_state.request.verify_digest,
            },
            "status": transfer_state.status,
            "start_time": transfer_state.start_time,
            "end_time": transfer_state.end_time,
            "error_message": transfer_state.error_message,
            "retry_count": transfer_state.retry_count,
            "checksum": transfer_state.checksum,
            "partial_layers": transfer_state.partial_layers,
        }

    def _deserialize_transfer_state(self, data: Dict) -> TransferState:
        """Deserialize transfer state from dictionary."""
        request_data = data["request"]
        request = TransferRequest(
            source_image=request_data["source_image"],
            source_tag=request_data["source_tag"],
            target_repository=request_data["target_repository"],
            target_tag=request_data["target_tag"],
            verify_digest=request_data["verify_digest"],
        )

        return TransferState(
            request=request,
            status=data["status"],
            start_time=data["start_time"],
            end_time=data["end_time"],
            error_message=data["error_message"],
            retry_count=data["retry_count"],
            checksum=data["checksum"],
            partial_layers=data["partial_layers"] or [],
        )
