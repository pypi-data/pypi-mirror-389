"""Rules from airflint (use ASTCollector for optimization)."""

import ast

from dagruff.models import LintIssue, Severity
from dagruff.rules.ast_collector import ASTCollector


def check_all_airflint_rules(collector: ASTCollector, file_path: str) -> list[LintIssue]:
    """Apply all airflint rules using collected data.

    This function implements the RuleChecker protocol.

    Args:
        collector: ASTCollector with collected data
        file_path: Path to file

    Returns:
        List of all found issues
    """
    issues: list[LintIssue] = []

    # AIRFLINT001: Check task dependencies
    has_dependencies = len(collector.rshift_lshift_ops) > 0

    if collector.task_assignments and not has_dependencies and len(collector.task_assignments) > 1:
        issues.append(
            LintIssue(
                file_path=file_path,
                line=1,
                column=0,
                severity=Severity.WARNING,
                rule_id="AIRFLINT001",
                message="Tasks without explicit dependencies found. Use >> or << to set dependencies",
            )
        )

    # AIRFLINT002: Check XCom (empty for now)
    # Can be extended in the future

    # AIRFLINT004: Check required operator parameters
    operator_required_params = {
        "BashOperator": ["bash_command"],
        "PythonOperator": ["python_callable"],
        "EmailOperator": ["to"],
    }

    for operator_node in collector.operators:
        func = operator_node.func
        operator_name = None

        if isinstance(func, ast.Name):
            operator_name = func.id
        elif isinstance(func, ast.Attribute):
            operator_name = func.attr

        if operator_name and operator_name in operator_required_params:
            required_params = operator_required_params[operator_name]
            provided_params = set()

            # Check positional arguments
            if len(operator_node.args) > 0:
                provided_params.add("task_id")

            # Check keyword arguments
            for keyword in operator_node.keywords:
                if keyword.arg:
                    provided_params.add(keyword.arg)

            # Check missing required parameters
            missing_params = set(required_params) - provided_params
            if missing_params:
                issues.append(
                    LintIssue(
                        file_path=file_path,
                        line=operator_node.lineno,
                        column=operator_node.col_offset,
                        severity=Severity.ERROR,
                        rule_id="AIRFLINT004",
                        message=f"{operator_name} requires required parameters: {', '.join(missing_params)}",
                    )
                )

    return issues
