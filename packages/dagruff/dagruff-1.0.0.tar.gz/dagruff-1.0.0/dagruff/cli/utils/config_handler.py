"""Configuration handling utilities."""

import sys
from pathlib import Path
from typing import Optional

from dagruff.config import Config
from dagruff.logger import get_logger
from dagruff.models import LintIssue, Severity
from dagruff.validation import validate_directory_path, validate_file_path

logger = get_logger(__name__)


def get_severity_levels(severity_arg: str) -> list[Severity]:
    """Get list of severity levels based on argument.

    Args:
        severity_arg: Severity argument ("error", "warning", or "info")

    Returns:
        List of severity levels to include
    """
    severity_levels = {
        "error": [Severity.ERROR],
        "warning": [Severity.ERROR, Severity.WARNING],
        "info": [Severity.ERROR, Severity.WARNING, Severity.INFO],
    }
    return severity_levels.get(severity_arg, severity_levels["info"])


def load_configuration(config_path_arg: Optional[str]) -> Config:
    """Load configuration from file.

    Args:
        config_path_arg: Path to configuration file (optional)

    Returns:
        Loaded configuration object

    Raises:
        SystemExit: If configuration file is specified but doesn't exist
    """
    config_path = Path(config_path_arg) if config_path_arg else None
    if config_path and not config_path.exists():
        logger.error(f"Configuration file not found: {config_path_arg}")
        print(f"Configuration file {config_path_arg} not found", file=sys.stderr)
        sys.exit(1)

    logger.debug(f"Loading configuration from {config_path}")
    return Config.load(config_path)


def determine_paths_to_check(args_paths: Optional[list[str]], config: Config) -> list[str]:
    """Determine paths to check based on CLI arguments and configuration.

    Args:
        args_paths: Paths specified in CLI arguments (optional)
        config: Configuration object

    Returns:
        List of validated paths to check

    Raises:
        SystemExit: If no valid paths found
    """
    paths_to_check: list[str] = []

    if args_paths:
        # If paths specified in CLI, use them (priority over config)
        for path_str in args_paths:
            path = Path(path_str)

            # Validate path
            if path.is_file():
                is_valid, error_msg = validate_file_path(path_str)
                if not is_valid:
                    logger.error(f"File validation failed: {error_msg}")
                    print(f"File validation failed: {error_msg}", file=sys.stderr)
                    continue
            elif path.is_dir():
                is_valid, error_msg = validate_directory_path(path_str)
                if not is_valid:
                    logger.error(f"Directory validation failed: {error_msg}")
                    print(f"Directory validation failed: {error_msg}", file=sys.stderr)
                    continue
            else:
                logger.error(f"Path does not exist: {path_str}")
                print(f"Path {path_str} does not exist", file=sys.stderr)
                continue

            paths_to_check.append(str(path))

        if not paths_to_check:
            logger.error("No valid paths found for checking")
            print("Failed to find any valid paths for checking", file=sys.stderr)
            sys.exit(1)
    else:
        # Use paths from config
        paths_to_check = config.get_paths()
        if not paths_to_check:
            error_msg = (
                "No path specified for checking and no paths found in configuration.\n"
                "Specify path directly or add paths to configuration file."
            )
            logger.error(error_msg)
            print(error_msg, file=sys.stderr)
            sys.exit(1)

    logger.info(f"Checking {len(paths_to_check)} paths: {paths_to_check}")
    return paths_to_check


def filter_issues(
    issues: list[LintIssue],
    min_severity: list[Severity],
    ignored_rules: list[str],
    config: Config,
) -> list[LintIssue]:
    """Filter issues by severity and ignored rules.

    Args:
        issues: List of issues to filter
        min_severity: List of severity levels to include
        ignored_rules: List of rule IDs to ignore
        config: Configuration object

    Returns:
        Filtered list of issues
    """
    # Filter by severity level
    filtered_issues = [issue for issue in issues if issue.severity in min_severity]

    # Filter by ignored rules
    # CLI parameter has priority over config
    ignored_rules_list = ignored_rules if ignored_rules else config.get_ignore()
    if ignored_rules_list:
        ignored_rules_set = set(ignored_rules_list)
        filtered_issues = [
            issue for issue in filtered_issues if issue.rule_id not in ignored_rules_set
        ]

    return filtered_issues
