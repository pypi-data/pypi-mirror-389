"""Check command implementation."""

from dagruff.cli.commands.base import BaseCommand
from dagruff.cli.linter import run_linter_for_paths
from dagruff.cli.utils.config_handler import filter_issues
from dagruff.models import LintIssue


class CheckCommand(BaseCommand):
    """Command to check DAG files for issues."""

    def execute(self, paths_to_check: list[str]) -> list[LintIssue]:
        """Execute check command.

        Args:
            paths_to_check: List of paths to check

        Returns:
            List of filtered lint issues
        """
        # Run linter for all paths
        all_issues = run_linter_for_paths(paths_to_check, linter_factory=self.linter_factory)

        # Filter issues by severity and ignored rules
        filtered_issues = filter_issues(
            all_issues,
            self.min_severity,
            self.ignored_rules,
            self.config,
        )

        return filtered_issues
