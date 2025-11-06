"""Linter functions for CLI."""

import os
import sys
from pathlib import Path
from typing import Callable, Optional

try:
    from tqdm import tqdm

    HAS_TQDM = True
except ImportError:
    HAS_TQDM = False
    tqdm = None

from dagruff.cli.utils.files import is_dag_file, should_ignore_path
from dagruff.constants import PYTHON_FILE_EXTENSION, STANDARD_IGNORE_PATTERNS
from dagruff.linter import DAGLinter
from dagruff.logger import get_logger
from dagruff.models import LintIssue
from dagruff.rules.base import Linter
from dagruff.validation import validate_directory_path, validate_file_path

logger = get_logger(__name__)


def lint_file(
    file_path: str,
    linter_factory: Optional[Callable[[str], Linter]] = None,
) -> list[LintIssue]:
    """Run linter for a single file.

    Args:
        file_path: Path to file to lint
        linter_factory: Optional factory function to create linter instance.
                       If None, uses DAGLinter by default (dependency injection).

    Returns:
        List of found issues
    """
    file_path_obj = Path(file_path)

    # Validate file path before processing
    is_valid, error_msg = validate_file_path(file_path)
    if not is_valid:
        logger.error(f"File validation failed: {error_msg}")
        return []

    # Check that it's a DAG file
    if not is_dag_file(file_path_obj):
        return []

    # Use dependency injection: create linter via factory or default
    if linter_factory is None:
        linter_factory = DAGLinter

    linter = linter_factory(file_path)
    return linter.lint()


def lint_directory(
    directory: str,
    linter_factory: Optional[Callable[[str], Linter]] = None,
) -> list[LintIssue]:
    """Run linter for a directory with memory optimization.

    Processes files one at a time to allow garbage collection between files.

    Args:
        directory: Path to directory to lint
        linter_factory: Optional factory function to create linter instance.
                       If None, uses DAGLinter by default (dependency injection).

    Returns:
        List of all found issues
    """
    all_issues = []
    directory_path = Path(directory)

    # Validate directory path
    is_valid, error_msg = validate_directory_path(directory)
    if not is_valid:
        logger.error(f"Directory validation failed: {error_msg}")
        print(f"Directory validation failed: {error_msg}", file=sys.stderr)
        return all_issues

    # Find all Python files and filter only DAG files
    # Use generator to avoid loading all paths into memory at once
    python_files = [
        py_file
        for py_file in directory_path.rglob(PYTHON_FILE_EXTENSION)
        if not should_ignore_path(py_file, STANDARD_IGNORE_PATTERNS) and is_dag_file(py_file)
    ]

    if not python_files:
        logger.warning(f"DAG files not found in {directory}")
        print(f"DAG files not found in {directory}", file=sys.stderr)
        return all_issues

    logger.info(f"Found {len(python_files)} DAG files in {directory}")

    # Process files one at a time to allow garbage collection
    # Use progress bar if tqdm is available and output is to terminal
    use_progress = HAS_TQDM and sys.stdout.isatty() and len(python_files) > 1

    if use_progress:
        file_iter = tqdm(
            python_files,
            total=len(python_files),
            desc=f"Checking {os.path.basename(directory)}",
            unit="file",
        )
    else:
        file_iter = python_files

    for python_file in file_iter:
        try:
            logger.debug(f"Checking file: {python_file}")
            issues = lint_file(str(python_file), linter_factory=linter_factory)
            all_issues.extend(issues)
            # Clear local reference to help GC
            del issues
        except Exception as e:
            # Log error but continue with other files
            logger.exception(f"Error processing file {python_file}: {e}")
            continue

    logger.info(
        f"Directory check completed: found {len(all_issues)} issues in {len(python_files)} files"
    )
    return all_issues


def run_linter_for_paths(
    paths_to_check: list[str],
    linter_factory: Optional[Callable[[str], Linter]] = None,
) -> list[LintIssue]:
    """Run linter for all specified paths with memory optimization.

    Processes files one at a time to avoid accumulating all issues in memory
    for very large projects. However, for statistics and filtering, all issues
    are collected at the end.

    Args:
        paths_to_check: List of paths to check
        linter_factory: Optional factory function to create linter instance.
                       If None, uses DAGLinter by default (dependency injection).

    Returns:
        List of all found issues
    """
    all_issues: list[LintIssue] = []

    # Use progress bar if tqdm is available and output is to terminal
    use_progress = HAS_TQDM and sys.stdout.isatty() and len(paths_to_check) > 1

    # Process each path individually to allow garbage collection
    if use_progress:
        path_iter = tqdm(
            paths_to_check,
            total=len(paths_to_check),
            desc="Checking paths",
            unit="path",
        )
    else:
        path_iter = paths_to_check

    for path_str in path_iter:
        path = Path(path_str)

        try:
            if path.is_file():
                logger.debug(f"Checking file: {path_str}")
                issues = lint_file(str(path), linter_factory=linter_factory)
            else:
                logger.debug(f"Checking directory: {path_str}")
                issues = lint_directory(str(path), linter_factory=linter_factory)

            # Extend issues list (this is necessary for statistics)
            all_issues.extend(issues)
            logger.debug(f"Found {len(issues)} issues in {path_str}")

            # Explicitly clear local references to help GC (though Python does this automatically)
            del issues

        except Exception as e:
            # Log error but continue with other paths
            logger.exception(f"Error processing {path_str}: {e}")
            continue

    return all_issues
