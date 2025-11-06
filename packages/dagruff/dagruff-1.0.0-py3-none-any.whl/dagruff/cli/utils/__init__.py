"""CLI utilities."""

from dagruff.cli.utils.args import normalize_arguments, parse_arguments
from dagruff.cli.utils.autofix_handler import apply_autofixes, determine_fixable_rules
from dagruff.cli.utils.config_handler import (
    determine_paths_to_check,
    filter_issues,
    get_severity_levels,
    load_configuration,
)
from dagruff.cli.utils.files import is_dag_file, should_ignore_path

__all__ = [
    "parse_arguments",
    "normalize_arguments",
    "is_dag_file",
    "should_ignore_path",
    "load_configuration",
    "determine_paths_to_check",
    "get_severity_levels",
    "filter_issues",
    "determine_fixable_rules",
    "apply_autofixes",
]
