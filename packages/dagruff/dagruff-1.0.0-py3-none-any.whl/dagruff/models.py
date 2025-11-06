"""Data models for the linter."""

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class Severity(Enum):
    """Error severity levels."""

    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass
class LintIssue:
    """Representation of an issue found by the linter."""

    file_path: str
    line: int
    column: int
    severity: Severity
    rule_id: str
    message: str
    fix: Optional[str] = None
