"""Protocols for checking rules and linter components."""

from typing import Protocol, runtime_checkable

from dagruff.models import LintIssue
from dagruff.rules.ast_collector import ASTCollector


@runtime_checkable
class RuleChecker(Protocol):
    """Protocol for rule checking functions.

    All rule checking functions should follow this interface:
    - Accept ASTCollector and file_path as parameters
    - Return List[LintIssue] with found issues
    """

    def __call__(self, collector: ASTCollector, file_path: str) -> list[LintIssue]:
        """Run rule checks.

        Args:
            collector: ASTCollector with collected AST data
            file_path: Path to the file being checked

        Returns:
            List of found issues
        """
        ...


@runtime_checkable
class Linter(Protocol):
    """Protocol for linter classes.

    All linter classes should follow this interface:
    - Accept file_path in __init__
    - Have lint() method that returns List[LintIssue]

    Example:
        ```python
        class MyLinter:
            def __init__(self, file_path: str):
                self.file_path = file_path

            def lint(self) -> List[LintIssue]:
                # Implementation
                return []
        ```
    """

    def __init__(self, file_path: str):
        """Initialize linter for specific file.

        Args:
            file_path: Path to file to lint
        """
        ...

    def lint(self) -> list[LintIssue]:
        """Run file check.

        Returns:
            List of found issues
        """
        ...


@runtime_checkable
class Autofixer(Protocol):
    """Protocol for autofixer functions.

    All autofixer functions should follow this interface:
    - Accept file_path and issues as parameters
    - Return Tuple of (fixed code, list of applied rules)
    """

    def __call__(self, file_path: str, issues: list[LintIssue]) -> tuple[str, list[str]]:
        """Apply autofixes to file.

        Args:
            file_path: Path to file
            issues: List of issues to fix

        Returns:
            Tuple (fixed code, list of applied rules)
        """
        ...
