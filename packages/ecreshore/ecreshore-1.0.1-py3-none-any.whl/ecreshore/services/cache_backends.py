"""Cache storage backend implementations.

Provides multiple backend options for cache storage:
- MemoryBackend: Fast in-memory cache (default, lost on exit)
- DiskBackend: Persistent SQLite-based cache (survives restarts)
- HybridBackend: Two-level cache with memory L1 and disk L2
"""

import asyncio
import logging
import os
import pickle
import sqlite3
from collections import OrderedDict
from pathlib import Path
from typing import Optional

from .cache_service import CacheBackend, CacheEntry

logger = logging.getLogger(__name__)


class MemoryBackend(CacheBackend):
    """In-memory cache backend using OrderedDict.

    Fast but ephemeral - all data lost when process exits.
    Thread-safe for async operations via asyncio.Lock.

    Features:
    - O(1) get/set operations
    - LRU tracking via OrderedDict move_to_end
    - No external dependencies
    """

    def __init__(self):
        """Initialize memory backend."""
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._lock = asyncio.Lock()

    async def get(self, key: str) -> Optional[CacheEntry]:
        """Retrieve entry from memory cache."""
        async with self._lock:
            entry = self._cache.get(key)
            if entry:
                # Move to end for LRU tracking
                self._cache.move_to_end(key)
            return entry

    async def set(self, key: str, entry: CacheEntry) -> None:
        """Store entry in memory cache."""
        async with self._lock:
            self._cache[key] = entry
            # Move to end to mark as recently used
            self._cache.move_to_end(key)

    async def delete(self, key: str) -> bool:
        """Remove entry from memory cache."""
        async with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False

    async def clear(self) -> int:
        """Clear all entries from memory cache."""
        async with self._lock:
            count = len(self._cache)
            self._cache.clear()
            return count

    async def keys(self) -> list[str]:
        """Get all cache keys."""
        async with self._lock:
            return list(self._cache.keys())

    async def size(self) -> int:
        """Get number of entries in cache."""
        async with self._lock:
            return len(self._cache)


class DiskBackend(CacheBackend):
    """Persistent disk-based cache using SQLite.

    Survives process restarts but slower than memory cache.
    Uses SQLite's built-in locking for multi-process safety.

    Features:
    - Persistent storage across restarts
    - WAL mode for crash safety
    - Automatic corruption recovery
    - Large capacity (limited by disk space)

    Note:
        This implementation uses basic SQLite without the diskcache library
        for minimal dependencies. For production, consider using diskcache.
    """

    def __init__(self, cache_dir: Optional[str] = None):
        """Initialize disk backend.

        Args:
            cache_dir: Directory for cache database (default: ~/.ecreshore/cache)
        """
        if cache_dir is None:
            cache_dir = os.path.expanduser("~/.ecreshore/cache")

        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = self.cache_dir / "cache.db"
        self._lock = asyncio.Lock()
        self._connection: Optional[sqlite3.Connection] = None
        self._initialized = False

    def _get_connection(self) -> sqlite3.Connection:
        """Get or create SQLite connection."""
        if self._connection is None:
            try:
                self._connection = sqlite3.connect(
                    str(self.db_path),
                    check_same_thread=False,
                    isolation_level=None,  # Autocommit mode
                )
                # Enable WAL mode for better concurrency and crash safety
                self._connection.execute("PRAGMA journal_mode=WAL")
                self._connection.execute("PRAGMA synchronous=NORMAL")
            except sqlite3.Error as e:
                logger.error(f"Failed to connect to cache database: {e}")
                raise

        if not self._initialized:
            self._init_schema()
            self._initialized = True

        return self._connection

    def _init_schema(self) -> None:
        """Initialize database schema."""
        try:
            # Use the existing connection directly to avoid recursion
            if self._connection is None:
                raise sqlite3.Error("No connection available for schema initialization")
            conn = self._connection
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS cache_entries (
                    key TEXT PRIMARY KEY,
                    value BLOB,
                    expires_at REAL,
                    created_at REAL,
                    last_accessed REAL
                )
                """
            )
            # Create index for expiration cleanup
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_expires_at
                ON cache_entries(expires_at)
                """
            )
        except sqlite3.Error as e:
            logger.error(f"Failed to initialize cache schema: {e}")
            # Try to recover by deleting corrupted database
            self._recover_from_corruption()

    def _recover_from_corruption(self) -> None:
        """Attempt to recover from database corruption."""
        try:
            logger.warning("Attempting to recover from cache database corruption")
            if self._connection:
                self._connection.close()
                self._connection = None

            if self.db_path.exists():
                # Backup corrupted DB
                backup_path = self.db_path.with_suffix(".db.corrupted")
                self.db_path.rename(backup_path)
                logger.info(f"Moved corrupted DB to {backup_path}")

            # Create fresh database
            self._initialized = False
            self._get_connection()
            logger.info("Successfully recovered cache database")

        except Exception as e:
            logger.error(f"Failed to recover cache database: {e}")

    async def get(self, key: str) -> Optional[CacheEntry]:
        """Retrieve entry from disk cache."""
        async with self._lock:
            try:
                conn = self._get_connection()
                cursor = conn.execute(
                    """
                    SELECT value, expires_at, created_at, last_accessed
                    FROM cache_entries WHERE key = ?
                    """,
                    (key,),
                )
                row = cursor.fetchone()

                if row is None:
                    return None

                # Deserialize entry
                value = pickle.loads(row[0])
                entry = CacheEntry(
                    value=value,
                    expires_at=row[1],
                    created_at=row[2],
                    last_accessed=row[3],
                )
                return entry

            except (sqlite3.Error, pickle.PickleError) as e:
                logger.warning(f"Disk cache get error for {key}: {e}")
                return None

    async def set(self, key: str, entry: CacheEntry) -> None:
        """Store entry in disk cache."""
        async with self._lock:
            try:
                conn = self._get_connection()
                value_blob = pickle.dumps(entry.value)

                conn.execute(
                    """
                    INSERT OR REPLACE INTO cache_entries
                    (key, value, expires_at, created_at, last_accessed)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        key,
                        value_blob,
                        entry.expires_at,
                        entry.created_at,
                        entry.last_accessed,
                    ),
                )

            except (sqlite3.Error, pickle.PickleError) as e:
                logger.warning(f"Disk cache set error for {key}: {e}")

    async def delete(self, key: str) -> bool:
        """Remove entry from disk cache."""
        async with self._lock:
            try:
                conn = self._get_connection()
                cursor = conn.execute(
                    "DELETE FROM cache_entries WHERE key = ?", (key,)
                )
                return cursor.rowcount > 0

            except sqlite3.Error as e:
                logger.warning(f"Disk cache delete error for {key}: {e}")
                return False

    async def clear(self) -> int:
        """Clear all entries from disk cache."""
        async with self._lock:
            try:
                conn = self._get_connection()
                cursor = conn.execute("SELECT COUNT(*) FROM cache_entries")
                count = cursor.fetchone()[0]
                conn.execute("DELETE FROM cache_entries")
                return count

            except sqlite3.Error as e:
                logger.warning(f"Disk cache clear error: {e}")
                return 0

    async def keys(self) -> list[str]:
        """Get all cache keys."""
        async with self._lock:
            try:
                conn = self._get_connection()
                cursor = conn.execute("SELECT key FROM cache_entries")
                return [row[0] for row in cursor.fetchall()]

            except sqlite3.Error as e:
                logger.warning(f"Disk cache keys error: {e}")
                return []

    async def size(self) -> int:
        """Get number of entries in cache."""
        async with self._lock:
            try:
                conn = self._get_connection()
                cursor = conn.execute("SELECT COUNT(*) FROM cache_entries")
                return cursor.fetchone()[0]

            except sqlite3.Error as e:
                logger.warning(f"Disk cache size error: {e}")
                return 0

    def close(self) -> None:
        """Close database connection."""
        if self._connection:
            self._connection.close()
            self._connection = None

    def __del__(self):
        """Ensure connection is closed on deletion."""
        self.close()


class HybridBackend(CacheBackend):
    """Two-level cache with fast memory L1 and persistent disk L2.

    Combines the speed of memory cache with the persistence of disk cache.
    Uses write-through strategy: writes go to both levels.
    Reads check L1 first, then L2 on miss.

    Features:
    - Fast reads from memory (L1)
    - Persistent storage (L2)
    - Automatic promotion from L2 to L1 on access
    - Write-through consistency

    Strategy:
    - Read: Check L1 → if miss, check L2 → if hit, promote to L1
    - Write: Write to L1 and L2 simultaneously
    - Delete: Delete from both L1 and L2
    """

    def __init__(
        self, memory_backend: Optional[MemoryBackend] = None, disk_backend: Optional[DiskBackend] = None
    ):
        """Initialize hybrid backend.

        Args:
            memory_backend: L1 cache (default: new MemoryBackend)
            disk_backend: L2 cache (default: new DiskBackend)
        """
        self.l1 = memory_backend or MemoryBackend()
        self.l2 = disk_backend or DiskBackend()

    async def get(self, key: str) -> Optional[CacheEntry]:
        """Retrieve entry from hybrid cache (L1 then L2)."""
        # Check L1 first
        entry = await self.l1.get(key)
        if entry is not None:
            logger.debug(f"Hybrid cache L1 hit: {key}")
            return entry

        # Check L2 on L1 miss
        entry = await self.l2.get(key)
        if entry is not None:
            # Promote to L1 for faster future access
            await self.l1.set(key, entry)
            logger.debug(f"Hybrid cache L2 hit, promoted to L1: {key}")
            return entry

        logger.debug(f"Hybrid cache miss (L1 and L2): {key}")
        return None

    async def set(self, key: str, entry: CacheEntry) -> None:
        """Store entry in both L1 and L2 (write-through)."""
        # Write to both levels
        await self.l1.set(key, entry)
        await self.l2.set(key, entry)

    async def delete(self, key: str) -> bool:
        """Remove entry from both L1 and L2."""
        l1_deleted = await self.l1.delete(key)
        l2_deleted = await self.l2.delete(key)
        return l1_deleted or l2_deleted

    async def clear(self) -> int:
        """Clear all entries from both L1 and L2."""
        l1_count = await self.l1.clear()
        l2_count = await self.l2.clear()
        return max(l1_count, l2_count)

    async def keys(self) -> list[str]:
        """Get all cache keys from L2 (authoritative)."""
        return await self.l2.keys()

    async def size(self) -> int:
        """Get number of entries (from L2, which has all entries)."""
        return await self.l2.size()
