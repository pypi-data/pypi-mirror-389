"""Base command class."""

from abc import ABC, abstractmethod
from typing import Callable, Optional

from dagruff.config import Config
from dagruff.models import LintIssue, Severity
from dagruff.rules.base import Linter


class BaseCommand(ABC):
    """Base class for CLI commands."""

    def __init__(
        self,
        config: Config,
        min_severity: list[Severity],
        ignored_rules: list[str],
        linter_factory: Optional[Callable[[str], Linter]] = None,
    ):
        """Initialize command.

        Args:
            config: Configuration object
            min_severity: List of severity levels to include
            ignored_rules: List of rule IDs to ignore
            linter_factory: Optional factory function to create linter instance
        """
        self.config = config
        self.min_severity = min_severity
        self.ignored_rules = ignored_rules
        self.linter_factory = linter_factory

    @abstractmethod
    def execute(self, paths_to_check: list[str]) -> list[LintIssue]:
        """Execute command.

        Args:
            paths_to_check: List of paths to check

        Returns:
            List of lint issues
        """
        pass
