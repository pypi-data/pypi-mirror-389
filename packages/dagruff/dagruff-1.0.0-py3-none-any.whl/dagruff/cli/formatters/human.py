"""Human-readable output formatter."""

from collections import Counter

from dagruff.constants import EXAMPLE_MESSAGE_TRUNCATE_LENGTH, TOP_RULES_COUNT
from dagruff.models import LintIssue, Severity


def format_issue(issue: LintIssue) -> str:
    """Format lint issue as human-readable string.

    Args:
        issue: LintIssue to format

    Returns:
        Formatted string with severity symbol, location, rule ID and message
    """
    severity_symbol = {
        Severity.ERROR: "❌",
        Severity.WARNING: "⚠️",
        Severity.INFO: "ℹ️",
    }
    symbol = severity_symbol.get(issue.severity, "•")
    return (
        f"{symbol} {issue.file_path}:{issue.line}:{issue.column} [{issue.rule_id}] {issue.message}"
    )


def print_statistics(filtered_issues: list[LintIssue]) -> None:
    """Print statistics about found issues.

    Args:
        filtered_issues: List of filtered issues
    """
    if not filtered_issues:
        print("✅ No issues found!")
        return

    print(f"\nFound {len(filtered_issues)} issues:\n")
    for issue in filtered_issues:
        print(format_issue(issue))
    print()

    # Count errors by severity level
    error_count = sum(1 for issue in filtered_issues if issue.severity == Severity.ERROR)
    warning_count = sum(1 for issue in filtered_issues if issue.severity == Severity.WARNING)
    info_count = sum(1 for issue in filtered_issues if issue.severity == Severity.INFO)

    # Summary statistics
    print("=" * 80)
    print("SUMMARY STATISTICS")
    print("=" * 80)
    print(f"🔴 Critical errors (ERROR): {error_count}")
    print(f"⚠️  Warnings (WARNING): {warning_count}")
    print(f"ℹ️  Information (INFO): {info_count}")
    print(f"📊 Total issues: {len(filtered_issues)}")
    print()

    # Top-5 most common errors
    rule_counter = Counter(issue.rule_id for issue in filtered_issues)
    top_rules = rule_counter.most_common(TOP_RULES_COUNT)

    if top_rules:
        print("🏆 TOP-5 MOST COMMON ISSUES:")
        for i, (rule_id, count) in enumerate(top_rules, 1):
            # Get example message for this rule
            example_message = next(
                (issue.message for issue in filtered_issues if issue.rule_id == rule_id),
                "Description unavailable",
            )
            severity_symbol = {
                Severity.ERROR: "🔴",
                Severity.WARNING: "⚠️",
                Severity.INFO: "ℹ️",
            }
            rule_severity = next(
                (issue.severity for issue in filtered_issues if issue.rule_id == rule_id),
                Severity.INFO,
            )
            symbol = severity_symbol.get(rule_severity, "•")
            print(
                f"  {i}. {symbol} [{rule_id}] - {count} time(s): {example_message[:EXAMPLE_MESSAGE_TRUNCATE_LENGTH]}..."
            )

    print("=" * 80)
