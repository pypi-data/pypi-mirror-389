"""Module for input validation."""

import os
from pathlib import Path
from typing import Optional

from dagruff.logger import get_logger

logger = get_logger(__name__)

# Constants
MAX_FILE_SIZE_MB = 10  # Maximum file size in megabytes
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024


def validate_file_path(file_path: str) -> tuple[bool, Optional[str]]:
    """Validate file path.

    Args:
        file_path: Path to file

    Returns:
        Tuple (is_valid, error_message)
    """
    try:
        path = Path(file_path)

        # Check if path is absolute and resolve it
        if not path.is_absolute():
            path = path.resolve()

        # Check if file exists
        if not path.exists():
            return False, f"File does not exist: {file_path}"

        # Check if it's a file (not directory)
        if not path.is_file():
            return False, f"Path is not a file: {file_path}"

        # Check file size
        file_size = path.stat().st_size
        if file_size > MAX_FILE_SIZE_BYTES:
            size_mb = file_size / (1024 * 1024)
            return False, f"File too large: {size_mb:.2f}MB (max {MAX_FILE_SIZE_MB}MB): {file_path}"

        # Check read permissions
        if not os.access(path, os.R_OK):
            return False, f"No read permission for file: {file_path}"

        return True, None

    except (OSError, ValueError) as e:
        return False, f"Invalid file path: {str(e)}"


def validate_directory_path(directory_path: str) -> tuple[bool, Optional[str]]:
    """Validate directory path.

    Args:
        directory_path: Path to directory

    Returns:
        Tuple (is_valid, error_message)
    """
    try:
        path = Path(directory_path)

        # Check if path is absolute and resolve it
        if not path.is_absolute():
            path = path.resolve()

        # Check if directory exists
        if not path.exists():
            return False, f"Directory does not exist: {directory_path}"

        # Check if it's a directory
        if not path.is_dir():
            return False, f"Path is not a directory: {directory_path}"

        # Check read permissions
        if not os.access(path, os.R_OK):
            return False, f"No read permission for directory: {directory_path}"

        return True, None

    except (OSError, ValueError) as e:
        return False, f"Invalid directory path: {str(e)}"


def sanitize_path(file_path: str) -> str:
    """Sanitize and normalize file path.

    Args:
        file_path: Path to sanitize

    Returns:
        Sanitized absolute path

    Raises:
        ValueError: If path is invalid or contains dangerous components
    """
    try:
        path = Path(file_path)

        # Resolve to absolute path
        if not path.is_absolute():
            path = path.resolve()

        # Check for dangerous path components
        parts = path.parts
        dangerous_components = ["..", "~", "//"]

        for part in parts:
            if part in dangerous_components:
                raise ValueError(f"Path contains dangerous component: {part}")

        # Normalize path (remove redundant separators, etc.)
        normalized = path.resolve()

        return str(normalized)

    except (OSError, ValueError) as e:
        raise ValueError(f"Invalid path: {str(e)}") from e


def validate_encoding(file_path: str, encoding: str = "utf-8") -> tuple[bool, Optional[str]]:
    """Validate that file can be read with specified encoding.

    Args:
        file_path: Path to file
        encoding: Encoding to check (default: utf-8)

    Returns:
        Tuple (is_valid, error_message)
    """
    try:
        with open(file_path, encoding=encoding) as f:
            # Try to read first few bytes to check encoding
            f.read(1024)
        return True, None
    except UnicodeDecodeError as e:
        return False, f"Cannot read file with {encoding} encoding: {str(e)}"
    except Exception as e:
        return False, f"Error reading file: {str(e)}"
