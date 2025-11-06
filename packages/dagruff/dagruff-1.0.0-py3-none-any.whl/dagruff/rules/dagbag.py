"""DAG validation check via Airflow DagBag."""

import os
import re

from dagruff.logger import get_logger
from dagruff.models import LintIssue, Severity
from dagruff.validation import sanitize_path, validate_file_path

logger = get_logger(__name__)

try:
    from airflow.models import DagBag
except ImportError:
    DagBag = None


def check_dagbag_validation(file_path: str) -> list[LintIssue]:
    """Check DAG validity via Airflow DagBag.

    Args:
        file_path: Path to file for checking

    Returns:
        List of found issues
    """
    issues: list[LintIssue] = []

    if DagBag is None:
        # Airflow not installed, skip check
        logger.debug(f"Airflow not installed, skipping DagBag check for {file_path}")
        return issues

    try:
        # Validate and sanitize file path before using it
        is_valid, error_msg = validate_file_path(file_path)
        if not is_valid:
            logger.warning(f"File validation failed for DagBag check: {error_msg}")
            issues.append(
                LintIssue(
                    file_path=file_path,
                    line=0,
                    column=0,
                    severity=Severity.WARNING,
                    rule_id="DAGBAG002",
                    message=f"Cannot validate file for DagBag check: {error_msg}",
                )
            )
            return issues

        # Sanitize path before passing to DagBag
        try:
            abs_file_path = sanitize_path(file_path)
        except ValueError as e:
            logger.warning(f"Path sanitization failed: {str(e)}")
            issues.append(
                LintIssue(
                    file_path=file_path,
                    line=0,
                    column=0,
                    severity=Severity.WARNING,
                    rule_id="DAGBAG002",
                    message=f"Invalid file path: {str(e)}",
                )
            )
            return issues

        dag_directory = os.path.dirname(abs_file_path)
        dag_filename = os.path.basename(abs_file_path)

        # Create DagBag for file checking
        dagbag = DagBag(dag_folder=dag_directory, include_examples=False)

        # Check import errors for our file
        if dagbag.import_errors:
            # Search for errors for our file
            for file_path_in_bag, error_message in dagbag.import_errors.items():
                # Normalize paths for comparison
                # DagBag may use different path formats (relative, absolute)
                file_path_in_bag_abs = os.path.abspath(file_path_in_bag)

                # Compare various path variants
                matches = (
                    file_path_in_bag in (abs_file_path, file_path)
                    or file_path_in_bag_abs == abs_file_path
                    or file_path_in_bag.endswith(dag_filename)
                    or os.path.basename(file_path_in_bag) == dag_filename
                )

                if matches:
                    # Try to extract line number from error
                    line_number = 0
                    error_str = str(error_message)

                    # Try to find line number in error message
                    # Search for patterns like "line 5", "line: 5", "line 5:" etc.
                    line_patterns = [
                        r"line\s*:?\s*(\d+)",
                        r"File.*line\s+(\d+)",
                        r"line\s+(\d+)\s*,",
                    ]

                    for pattern in line_patterns:
                        line_match = re.search(pattern, error_str, re.IGNORECASE)
                        if line_match:
                            try:
                                line_number = int(line_match.group(1))
                                break
                            except (ValueError, IndexError):
                                pass

                    issues.append(
                        LintIssue(
                            file_path=file_path,
                            line=line_number,
                            column=0,
                            severity=Severity.ERROR,
                            rule_id="DAGBAG001",
                            message=f"DAG loading error: {error_message}",
                        )
                    )
                    break

    except (OSError, PermissionError) as e:
        # File or directory access errors
        logger.warning(
            f"Access error when checking DAG via DagBag for {file_path}: {str(e)}", exc_info=True
        )
        issues.append(
            LintIssue(
                file_path=file_path,
                line=0,
                column=0,
                severity=Severity.WARNING,
                rule_id="DAGBAG002",
                message=f"Access error when checking via DagBag: {str(e)}",
            )
        )
    except (ImportError, AttributeError) as e:
        # Import or Airflow API errors
        logger.debug(f"Airflow API error for {file_path}: {str(e)}")
        # Don't add issue, as this may be an environment issue, not a file issue
    except (KeyboardInterrupt, SystemExit):
        # System exceptions should not be caught
        raise
    except Exception as e:
        # Last catch-all only for unexpected DagBag errors
        # This is not critical, as it may be an environment issue, not a file issue
        logger.warning(
            f"Unexpected error checking DAG via DagBag for {file_path}: {str(e)}", exc_info=True
        )
        issues.append(
            LintIssue(
                file_path=file_path,
                line=0,
                column=0,
                severity=Severity.WARNING,
                rule_id="DAGBAG002",
                message=f"Failed to check DAG via DagBag: {str(e)}",
            )
        )

    return issues
