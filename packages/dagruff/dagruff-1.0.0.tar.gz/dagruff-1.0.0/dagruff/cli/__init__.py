"""CLI package for dagruff linter."""

# Main entry point
# Exports for backward compatibility with tests
from dagruff.cli.formatters import format_issue, format_output_json, print_statistics
from dagruff.cli.linter import lint_directory, lint_file, run_linter_for_paths
from dagruff.cli.runner import main
from dagruff.cli.utils import (
    apply_autofixes,
    determine_fixable_rules,
    determine_paths_to_check,
    filter_issues,
    get_severity_levels,
    is_dag_file,
    load_configuration,
    normalize_arguments,
    parse_arguments,
)

__all__ = [
    "main",
    # Runner functions
    "lint_file",
    "lint_directory",
    "run_linter_for_paths",
    # Formatters
    "format_issue",
    "print_statistics",
    "format_output_json",
    # Utils
    "parse_arguments",
    "normalize_arguments",
    "is_dag_file",
    "load_configuration",
    "determine_paths_to_check",
    "get_severity_levels",
    "filter_issues",
    "determine_fixable_rules",
    "apply_autofixes",
]
