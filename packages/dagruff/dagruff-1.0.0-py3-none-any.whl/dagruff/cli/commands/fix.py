"""Fix command implementation."""

from dagruff.cli.commands.base import BaseCommand
from dagruff.cli.utils.autofix_handler import apply_autofixes
from dagruff.models import LintIssue


class FixCommand(BaseCommand):
    """Command to automatically fix DAG files."""

    def __init__(self, *args, fixable_rules: set[str], **kwargs):
        """Initialize fix command.

        Args:
            *args: Arguments passed to base class
            fixable_rules: Set of rule IDs that can be fixed
            **kwargs: Keyword arguments passed to base class
        """
        super().__init__(*args, **kwargs)
        self.fixable_rules = fixable_rules

    def execute(self, paths_to_check: list[str]) -> list[LintIssue]:
        """Execute fix command.

        Args:
            paths_to_check: List of paths to check

        Returns:
            List of filtered lint issues after fixing
        """
        # Apply autofixes
        filtered_issues, total_fixed = apply_autofixes(
            paths_to_check,
            self.fixable_rules,
            self.min_severity,
            self.ignored_rules,
            self.config,
            linter_factory=self.linter_factory,
        )

        return filtered_issues
