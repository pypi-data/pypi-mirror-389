"""Autofix handling utilities."""

import sys
from typing import Callable, Optional

from dagruff.autofix import apply_fixes
from dagruff.config import Config
from dagruff.constants import FIXABLE_RULE_IDS
from dagruff.logger import get_logger
from dagruff.models import LintIssue, Severity
from dagruff.rules.base import Autofixer, Linter

logger = get_logger(__name__)


def determine_fixable_rules(fix_arg: Optional[list[str]]) -> tuple[set[str], list[str]]:
    """Determine which rules can be fixed based on --fix argument.

    Args:
        fix_arg: List of rules from --fix argument (None if not specified, [] if specified without args)

    Returns:
        Tuple of (fixable_rules_set, list_of_warnings)
    """
    warnings = []

    if fix_arg is None:
        return set(), warnings

    # All available rules for autofix
    all_fixable_rules = FIXABLE_RULE_IDS

    # If specific rules are specified, use them, otherwise fix all available
    if fix_arg:  # Non-empty list - specific rules specified
        # Convert to set and check that all rules are available for autofix
        requested_rules = set(fix_arg)
        invalid_rules = requested_rules - all_fixable_rules
        if invalid_rules:
            warning_msg = (
                f"The following rules cannot be automatically fixed: {', '.join(sorted(invalid_rules))}\n"
                f"Available rules for autofix: {', '.join(sorted(all_fixable_rules))}"
            )
            logger.warning(warning_msg)
            warnings.append(warning_msg)
        fixable_rules = requested_rules & all_fixable_rules
    else:
        # If --fix is specified without arguments (empty list), fix all available rules
        fixable_rules = all_fixable_rules

    return fixable_rules, warnings


def apply_autofixes(
    paths_to_check: list[str],
    fixable_rules: set[str],
    min_severity: list[Severity],
    ignored_rules: list[str],
    config: Config,
    linter_factory: Optional[Callable[[str], Linter]] = None,
    autofixer: Optional[Autofixer] = None,
) -> tuple[list[LintIssue], int]:
    """Apply autofixes to files.

    Args:
        paths_to_check: List of paths to check
        fixable_rules: Set of rule IDs that can be fixed
        min_severity: List of severity levels to include
        ignored_rules: List of rule IDs to ignore
        config: Configuration object
        linter_factory: Optional factory function to create linter instance.
                       If None, uses DAGLinter by default (dependency injection).
        autofixer: Optional autofixer function. If None, uses apply_fixes by default
                  (dependency injection).

    Returns:
        Tuple of (filtered_issues_after_fix, total_fixed_count)
    """
    # Import here to avoid circular dependency
    from dagruff.cli.linter import run_linter_for_paths

    if not fixable_rules:
        logger.warning("No available rules for autofix")
        print("❌ No available rules for autofix", file=sys.stderr)
        return [], 0

    # Use dependency injection: default autofixer if not provided
    if autofixer is None:
        autofixer = apply_fixes

    # Run linter for all paths
    all_issues = run_linter_for_paths(paths_to_check, linter_factory=linter_factory)

    # Filter only needed rules for autofix
    fixable_issues = [issue for issue in all_issues if issue.rule_id in fixable_rules]

    # Filter by severity level
    fixable_issues = [issue for issue in fixable_issues if issue.severity in min_severity]

    # Filter by ignored rules
    ignored_rules_list = ignored_rules if ignored_rules else config.get_ignore()
    if ignored_rules_list:
        ignored_rules_set = set(ignored_rules_list)
        fixable_issues = [
            issue for issue in fixable_issues if issue.rule_id not in ignored_rules_set
        ]

    if not fixable_issues:
        return [], 0

    # Group issues by file
    issues_by_file = {}
    for issue in fixable_issues:
        if issue.file_path not in issues_by_file:
            issues_by_file[issue.file_path] = []
        issues_by_file[issue.file_path].append(issue)

    # Apply fixes for each file
    total_fixed = 0
    for file_path, file_issues in issues_by_file.items():
        try:
            fixed_code, applied_rules = autofixer(file_path, file_issues)
            if applied_rules:
                # Save fixed file
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(fixed_code)
                total_fixed += len(applied_rules)
                logger.info(f"Fixed {len(applied_rules)} issues in {file_path}: {applied_rules}")
                print(
                    f"✅ Fixed {len(applied_rules)} issues in {file_path}: {', '.join(applied_rules)}"
                )
        except (OSError, PermissionError) as e:
            # File writing errors
            logger.exception(f"Error writing file when fixing {file_path}: {e}")
            print(f"⚠️  Error writing file when fixing {file_path}: {str(e)}", file=sys.stderr)
        except (ValueError, AttributeError, KeyError) as e:
            # Data handling errors
            logger.exception(f"Error processing data when fixing {file_path}: {e}")
            print(f"⚠️  Error processing data when fixing {file_path}: {str(e)}", file=sys.stderr)
        except (KeyboardInterrupt, SystemExit):
            # System exceptions should not be caught
            raise
        except Exception as e:
            # Last catch-all only for unexpected errors
            logger.exception(f"Unexpected error when fixing {file_path}: {e}")
            print(f"⚠️  Unexpected error when fixing {file_path}: {str(e)}", file=sys.stderr)

    if total_fixed > 0:
        print(f"\n🎉 Total fixed {total_fixed} issues.\n")
        # After fixing, check only fixed rules for confirmation
        # Import here to avoid circular dependency
        from dagruff.cli.linter import run_linter_for_paths

        all_issues = run_linter_for_paths(paths_to_check)

        # Filter only fixed rules
        filtered_issues = [issue for issue in all_issues if issue.rule_id in fixable_rules]
        filtered_issues = [issue for issue in filtered_issues if issue.severity in min_severity]
        if ignored_rules_list:
            ignored_rules_set = set(ignored_rules_list)
            filtered_issues = [
                issue for issue in filtered_issues if issue.rule_id not in ignored_rules_set
            ]
        return filtered_issues, total_fixed
    else:
        # If nothing was fixed, show only issues for specified rules
        return fixable_issues, 0
