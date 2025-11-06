"""Rules from Ruff AIR series (use ASTCollector for optimization)."""

import ast

from dagruff.models import LintIssue, Severity
from dagruff.rules.ast_collector import ASTCollector


def check_all_ruff_air_rules(collector: ASTCollector, file_path: str) -> list[LintIssue]:
    """Apply all Ruff AIR rules using collected data.

    This function implements the RuleChecker protocol.

    Args:
        collector: ASTCollector with collected data
        file_path: Path to file

    Returns:
        List of all found issues
    """
    issues: list[LintIssue] = []

    # AIR002: Check start_date
    has_default_args_start_date = collector.has_default_args_key("start_date")

    for dag_call in collector.dag_calls:
        has_start_date = any(kw.arg == "start_date" for kw in dag_call.keywords)

        if not has_start_date and not has_default_args_start_date:
            issues.append(
                LintIssue(
                    file_path=file_path,
                    line=dag_call.lineno,
                    column=dag_call.col_offset,
                    severity=Severity.ERROR,
                    rule_id="AIR002",
                    message="DAG must have start_date parameter (in DAG or default_args)",
                )
            )

    # AIR003: Check catchup
    for dag_call in collector.dag_calls:
        has_catchup = False
        catchup_value = None

        for keyword in dag_call.keywords:
            if keyword.arg == "catchup":
                has_catchup = True
                if (
                    isinstance(keyword.value, ast.Constant)
                    or hasattr(ast, "NameConstant")
                    and isinstance(keyword.value, ast.NameConstant)
                ):
                    catchup_value = keyword.value.value
                break

        if not has_catchup:
            issues.append(
                LintIssue(
                    file_path=file_path,
                    line=dag_call.lineno,
                    column=dag_call.col_offset,
                    severity=Severity.WARNING,
                    rule_id="AIR003",
                    message="It is recommended to explicitly specify catchup=False to prevent execution of missed tasks",
                )
            )
        elif catchup_value is True:
            issues.append(
                LintIssue(
                    file_path=file_path,
                    line=dag_call.lineno,
                    column=dag_call.col_offset,
                    severity=Severity.WARNING,
                    rule_id="AIR003",
                    message="catchup=True may lead to execution of many missed tasks",
                )
            )

    # AIR013: Check max_active_runs
    for dag_call in collector.dag_calls:
        has_max_active_runs = any(kw.arg == "max_active_runs" for kw in dag_call.keywords)

        if not has_max_active_runs:
            issues.append(
                LintIssue(
                    file_path=file_path,
                    line=dag_call.lineno,
                    column=dag_call.col_offset,
                    severity=Severity.INFO,
                    rule_id="AIR013",
                    message="It is recommended to specify max_active_runs to limit parallel DAG runs",
                )
            )

    # AIR014: Check concurrency/max_active_tasks
    for dag_call in collector.dag_calls:
        has_max_active_tasks = False
        has_concurrency = False
        concurrency_line = None
        concurrency_col = None

        for keyword in dag_call.keywords:
            if keyword.arg == "max_active_tasks":
                has_max_active_tasks = True
                break
            elif keyword.arg == "concurrency":
                has_concurrency = True
                concurrency_line = dag_call.lineno
                concurrency_col = dag_call.col_offset
                break

        if has_concurrency and not has_max_active_tasks:
            issues.append(
                LintIssue(
                    file_path=file_path,
                    line=concurrency_line or dag_call.lineno,
                    column=concurrency_col or dag_call.col_offset,
                    severity=Severity.WARNING,
                    rule_id="AIR014",
                    message="Deprecated concurrency parameter used. It is recommended to use max_active_tasks for Airflow 2+",
                )
            )
        elif not has_max_active_tasks:
            issues.append(
                LintIssue(
                    file_path=file_path,
                    line=dag_call.lineno,
                    column=dag_call.col_offset,
                    severity=Severity.INFO,
                    rule_id="AIR014",
                    message="It is recommended to specify max_active_tasks to limit parallel tasks in DAG (Airflow 2+)",
                )
            )

    return issues
