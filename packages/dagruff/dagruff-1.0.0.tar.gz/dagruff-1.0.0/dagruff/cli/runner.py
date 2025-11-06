"""CLI runner - orchestrates all commands."""

import sys

from dagruff.cli.commands.check import CheckCommand
from dagruff.cli.commands.fix import FixCommand
from dagruff.cli.formatters import format_output_json, print_statistics
from dagruff.cli.utils import (
    determine_fixable_rules,
    determine_paths_to_check,
    get_severity_levels,
    load_configuration,
    normalize_arguments,
    parse_arguments,
)
from dagruff.linter import get_cache, set_cache
from dagruff.logger import get_logger, setup_logging
from dagruff.models import LintIssue, Severity

logger = get_logger(__name__)

# Re-export linter functions for backward compatibility


def main():
    """Main CLI function - coordinates all operations."""
    # Parse and normalize arguments
    args = parse_arguments()

    # Setup logging
    setup_logging(level=args.log_level, log_file=args.log_file)
    logger.info("Starting dagruff CLI")
    logger.debug(f"Command line arguments: {vars(args)}")

    # Setup cache
    cache = get_cache(enabled=not args.no_cache)
    set_cache(cache)
    if args.no_cache:
        logger.debug("Caching disabled")
    else:
        logger.debug("Caching enabled")

    # Normalize arguments (extract paths from --ignore and --fix)
    normalize_arguments(args)

    # Get severity levels
    min_severity = get_severity_levels(args.severity)

    # Load configuration
    config = load_configuration(args.config)

    # Determine paths to check
    paths_to_check = determine_paths_to_check(args.path, config)

    # Determine which command to execute
    if args.fix is not None:
        # Fix command
        fixable_rules, warnings = determine_fixable_rules(args.fix)
        for warning in warnings:
            print(f"⚠️  Warning: {warning}", file=sys.stderr)

        command = FixCommand(
            config=config,
            min_severity=min_severity,
            ignored_rules=args.ignore or [],
            fixable_rules=fixable_rules,
        )
    else:
        # Check command
        command = CheckCommand(
            config=config,
            min_severity=min_severity,
            ignored_rules=args.ignore or [],
        )

    # Execute command
    filtered_issues: list[LintIssue] = command.execute(paths_to_check)

    # Output results
    if args.format == "json":
        format_output_json(filtered_issues)
    else:
        print_statistics(filtered_issues)

    # Exit code
    error_count = sum(1 for issue in filtered_issues if issue.severity == Severity.ERROR)
    if error_count > 0 and not args.exit_zero:
        sys.exit(1)
    else:
        sys.exit(0)
