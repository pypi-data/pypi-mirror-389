"""Argument parsing and normalization utilities."""

import argparse
from pathlib import Path


def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments.

    Returns:
        Parsed arguments namespace
    """
    parser = argparse.ArgumentParser(
        description="Custom linter for Airflow DAG files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--log-level",
        type=str,
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default="INFO",
        help="Logging level (default: INFO)",
    )
    parser.add_argument(
        "--log-file",
        type=str,
        default=None,
        help="Path to log file (optional)",
    )
    parser.add_argument(
        "path",
        type=str,
        nargs="*",
        default=None,
        help="Path to file or directory to check (can specify multiple). "
        "If not specified, paths from configuration are used.",
    )
    parser.add_argument(
        "--config",
        type=str,
        default=None,
        help="Path to configuration file (if not specified, default is used)",
    )
    parser.add_argument(
        "--severity",
        type=str,
        choices=["error", "warning", "info"],
        default="info",
        help="Minimum severity level for output (default: info)",
    )
    parser.add_argument(
        "--exit-zero",
        action="store_true",
        help="Always return exit code 0, even if errors are found",
    )
    parser.add_argument(
        "--format",
        type=str,
        choices=["human", "json"],
        default="human",
        help="Output format (default: human)",
    )
    parser.add_argument(
        "--ignore",
        type=str,
        nargs="+",
        default=[],
        help="List of rules (rule_id) to ignore (e.g.: --ignore DAG001 DAG002)",
    )
    parser.add_argument(
        "--fix",
        type=str,
        nargs="*",
        metavar="RULE_ID",
        help="Automatically fix specified issues (e.g.: --fix DAG001 DAG005). "
        "If only --fix is specified without arguments, all available rules are fixed.",
    )
    parser.add_argument(
        "--no-cache",
        action="store_true",
        help="Disable caching of linter results (default: cache enabled)",
    )
    return parser.parse_args()


def normalize_arguments(args: argparse.Namespace) -> None:
    """Normalize arguments by extracting paths from --ignore and --fix flags.

    Args:
        args: Arguments namespace to normalize (modified in place)
    """
    # Fix case when paths were specified after --ignore
    # Check arguments in args.ignore - if they are existing paths,
    # move them to args.path
    if args.ignore:
        actual_ignore_rules = []
        paths_from_ignore = []

        for item in args.ignore:
            path = Path(item)
            # If this is an existing path, it's a path, not a rule to ignore
            if path.exists():
                paths_from_ignore.append(item)
            else:
                actual_ignore_rules.append(item)

        # Update args.ignore - keep only rules
        args.ignore = actual_ignore_rules if actual_ignore_rules else []

        # Move found paths to args.path
        if paths_from_ignore:
            if args.path is None:
                args.path = paths_from_ignore
            else:
                args.path.extend(paths_from_ignore)

    # Process --fix arguments:
    # Split arguments into rules and paths
    if args.fix is not None and args.fix:
        actual_fix_rules = []
        paths_from_fix = []

        for item in args.fix:
            path = Path(item)
            # If this is an existing path, it's a path, not a rule
            if path.exists():
                paths_from_fix.append(item)
            else:
                actual_fix_rules.append(item)

        # Update args.fix - keep only rules
        if actual_fix_rules:
            args.fix = actual_fix_rules
        else:
            # If all were paths, --fix was without arguments (all available rules)
            args.fix = []

        # Move found paths to args.path
        if paths_from_fix:
            if args.path is None:
                args.path = paths_from_fix
            else:
                args.path.extend(paths_from_fix)
