"""File utilities for CLI."""

import fnmatch
from pathlib import Path

from dagruff.constants import (
    AIRFLOW_DECORATORS_IMPORT_PATTERN,
    AIRFLOW_IMPORT_FROM_PATTERN,
    AIRFLOW_IMPORT_PATTERN,
    CONFIG_FILE_EXCEPTION,
    DAGRUFF_PACKAGE_NAME,
    STANDARD_IGNORE_PATTERNS,
)
from dagruff.logger import get_logger
from dagruff.validation import validate_file_path

logger = get_logger(__name__)


def is_dag_file(file_path: Path) -> bool:
    """Check if file is a DAG file.

    Checks if file contains Airflow imports (from airflow import DAG, etc.).
    Only reads first 64KB of file to avoid loading large files into memory.
    Excludes files from the dagruff package itself.

    Args:
        file_path: Path to file to check

    Returns:
        True if file appears to be a DAG file, False otherwise
    """
    try:
        # Exclude files from the linter package itself
        file_str = str(file_path)
        if DAGRUFF_PACKAGE_NAME in file_str:
            return False

        # Validate file path and size before reading
        is_valid, error_msg = validate_file_path(str(file_path))
        if not is_valid:
            logger.debug(f"File validation failed for {file_path}: {error_msg}")
            return False

        # Read only first 64KB to check for imports (sufficient for import detection)
        # This prevents loading very large files into memory
        max_preview_size = 64 * 1024  # 64KB

        try:
            with open(file_path, encoding="utf-8") as f:
                content = f.read(max_preview_size)
                # Check for airflow imports - this is the most reliable sign of a DAG file
                # Look for imports that clearly indicate Airflow usage
                has_airflow_import = (
                    AIRFLOW_IMPORT_FROM_PATTERN in content
                    or AIRFLOW_IMPORT_PATTERN in content
                    or AIRFLOW_DECORATORS_IMPORT_PATTERN in content
                )

                # If there's an airflow import, it's most likely a DAG file
                # Additionally check DAG usage in code (not in comments)
                # But if there's an import, consider it a DAG file even without explicit usage
                return has_airflow_import
        except (OSError, PermissionError, UnicodeDecodeError) as e:
            # Specific file reading errors
            logger.debug(f"Failed to read file for DAG check: {file_path}: {e}")
            return False
        except (KeyboardInterrupt, SystemExit):
            # System exceptions should not be caught
            raise
        except Exception as e:
            # Last catch-all for other unexpected errors
            logger.warning(f"Unexpected error checking file {file_path}: {e}", exc_info=True)
            return False

    except (KeyboardInterrupt, SystemExit):
        # System exceptions should not be caught
        raise
    except Exception as e:
        # Last catch-all for other unexpected errors
        logger.warning(f"Unexpected error in is_dag_file for {file_path}: {e}", exc_info=True)
        return False


def should_ignore_path(file_path: Path, ignore_patterns: list[str] = None) -> bool:
    """Check if file should be ignored using optimized pattern matching.

    Uses fnmatch for wildcard patterns to avoid O(n*m) complexity.

    Args:
        file_path: Path to check
        ignore_patterns: List of ignore patterns (defaults to STANDARD_IGNORE_PATTERNS)

    Returns:
        True if path should be ignored, False otherwise
    """
    if ignore_patterns is None:
        ignore_patterns = STANDARD_IGNORE_PATTERNS

    # Precompile patterns for better performance
    exact_patterns = {p for p in ignore_patterns if "*" not in p}
    wildcard_patterns = [p for p in ignore_patterns if "*" in p]

    parts = file_path.parts

    # Check each part of path
    for part in parts:
        # Check exact match (O(1) lookup)
        if part in exact_patterns:
            return True

        # Check patterns (starts with dot or ends with certain suffixes)
        if part.startswith(".") and part not in [".", ".."] and part not in [CONFIG_FILE_EXCEPTION]:
            return True

        # Check wildcard patterns using fnmatch (O(n) instead of O(n*m))
        for pattern in wildcard_patterns:
            if fnmatch.fnmatch(part, pattern):
                return True

    return False
