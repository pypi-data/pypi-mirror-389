"""Caching module for linter results."""

import copy
import hashlib
import os
from typing import Optional

from dagruff.logger import get_logger
from dagruff.models import LintIssue

logger = get_logger(__name__)


class LinterCache:
    """Cache for linter results based on file hash."""

    def __init__(self, enabled: bool = True):
        """Initialize cache.

        Args:
            enabled: Whether caching is enabled
        """
        self.enabled = enabled
        self._cache: dict[str, tuple[str, list[LintIssue]]] = {}
        # Cache version - increment to invalidate all cache
        self._cache_version = "1.0"

    def _compute_file_hash(self, file_path: str) -> str:
        """Compute SHA256 hash of file contents.

        Args:
            file_path: Path to file

        Returns:
            SHA256 hash as hex string
        """
        try:
            with open(file_path, "rb") as f:
                file_hash = hashlib.sha256()
                # Read file in chunks to handle large files
                chunk_size = 8192
                while chunk := f.read(chunk_size):
                    file_hash.update(chunk)
                return file_hash.hexdigest()
        except OSError as e:
            logger.warning(f"Failed to compute hash for {file_path}: {e}")
            return ""

    def _get_cache_key(self, file_path: str) -> str:
        """Get cache key for file.

        Args:
            file_path: Path to file

        Returns:
            Cache key including version
        """
        return f"{self._cache_version}:{os.path.abspath(file_path)}"

    def get(self, file_path: str) -> Optional[list[LintIssue]]:
        """Get cached issues for file.

        Args:
            file_path: Path to file

        Returns:
            Cached issues if found and file hasn't changed, None otherwise
        """
        if not self.enabled:
            return None

        cache_key = self._get_cache_key(file_path)

        # Check if file exists
        if not os.path.exists(file_path):
            return None

        # Check if we have cached results
        if cache_key not in self._cache:
            logger.debug(f"Cache miss for {file_path}")
            return None

        cached_hash, cached_issues = self._cache[cache_key]

        # Compute current file hash
        current_hash = self._compute_file_hash(file_path)

        if not current_hash:
            # Failed to compute hash, don't use cache
            logger.debug(f"Failed to compute hash for {file_path}, skipping cache")
            return None

        # Check if file has changed
        if cached_hash != current_hash:
            logger.debug(f"Cache invalidated for {file_path} (file changed)")
            # Remove from cache
            del self._cache[cache_key]
            return None

        logger.debug(f"Cache hit for {file_path}")
        # Return deep copy to prevent modification
        return copy.deepcopy(cached_issues)

    def set(self, file_path: str, issues: list[LintIssue]) -> None:
        """Cache issues for file.

        Args:
            file_path: Path to file
            issues: List of issues to cache
        """
        if not self.enabled:
            return

        cache_key = self._get_cache_key(file_path)

        # Check if file exists
        if not os.path.exists(file_path):
            return

        # Compute file hash
        file_hash = self._compute_file_hash(file_path)

        if not file_hash:
            # Failed to compute hash, don't cache
            logger.debug(f"Failed to compute hash for {file_path}, skipping cache")
            return

        # Store deep copy in cache to prevent modification
        self._cache[cache_key] = (file_hash, copy.deepcopy(issues))
        logger.debug(f"Cached results for {file_path} ({len(issues)} issues)")

    def clear(self, file_path: Optional[str] = None) -> None:
        """Clear cache for specific file or all files.

        Args:
            file_path: Path to file to clear cache for, or None to clear all
        """
        if file_path is None:
            self._cache.clear()
            logger.debug("Cleared all cache")
        else:
            cache_key = self._get_cache_key(file_path)
            if cache_key in self._cache:
                del self._cache[cache_key]
                logger.debug(f"Cleared cache for {file_path}")

    def invalidate_version(self) -> None:
        """Invalidate all cache by incrementing version."""
        self._cache_version = f"{float(self._cache_version.split(':')[0]) + 0.1:.1f}"
        self._cache.clear()
        logger.debug(f"Invalidated cache (new version: {self._cache_version})")

    def get_stats(self) -> dict[str, int]:
        """Get cache statistics.

        Returns:
            Dictionary with cache statistics
        """
        return {
            "size": len(self._cache),
            "enabled": self.enabled,
        }
