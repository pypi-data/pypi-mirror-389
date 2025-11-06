"""JSON output formatter."""

import json

from dagruff.models import LintIssue


def format_output_json(filtered_issues: list[LintIssue]) -> None:
    """Format and print output in JSON format.

    Args:
        filtered_issues: List of filtered issues
    """
    output = [
        {
            "file": issue.file_path,
            "line": issue.line,
            "column": issue.column,
            "severity": issue.severity.value,
            "rule_id": issue.rule_id,
            "message": issue.message,
        }
        for issue in filtered_issues
    ]
    print(json.dumps(output, indent=2, ensure_ascii=False))
