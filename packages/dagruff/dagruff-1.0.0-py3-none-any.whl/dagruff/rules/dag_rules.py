"""DAG checking rules (use ASTCollector for optimization)."""

import ast

from dagruff.models import LintIssue, Severity
from dagruff.rules.ast_collector import ASTCollector


def check_all_dag_rules(collector: ASTCollector, file_path: str) -> list[LintIssue]:
    """Apply all DAG rules using collected data.

    This function implements the RuleChecker protocol.

    Args:
        collector: ASTCollector with collected data
        file_path: Path to file

    Returns:
        List of all found issues
    """
    issues: list[LintIssue] = []

    # DAG001: Check DAG import
    if not collector.has_dag_import():
        issues.append(
            LintIssue(
                file_path=file_path,
                line=1,
                column=0,
                severity=Severity.ERROR,
                rule_id="DAG001",
                message="Missing DAG import from airflow",
            )
        )

    # DAG002: Check DAG definition
    # Use collector.dag_calls which already includes DAG calls from all contexts
    # (including with statements, as they are processed recursively)
    has_dag_definition = len(collector.dag_calls) > 0

    if not has_dag_definition:
        issues.append(
            LintIssue(
                file_path=file_path,
                line=1,
                column=0,
                severity=Severity.WARNING,
                rule_id="DAG002",
                message="DAG definition not found. Ensure DAG is created via DAG()",
            )
        )

    # DAG003, DAG004, DAG005: Check dag_id
    dag_ids = []
    for dag_call in collector.dag_calls:
        has_dag_id = False
        dag_id_value = None

        # Check positional arguments
        if dag_call.args and len(dag_call.args) > 0 and isinstance(dag_call.args[0], ast.Constant):
            has_dag_id = True
            dag_id_value = dag_call.args[0].value

        # Check keyword arguments
        if not has_dag_id:
            for keyword in dag_call.keywords:
                if keyword.arg == "dag_id":
                    has_dag_id = True
                    if isinstance(keyword.value, ast.Constant):
                        dag_id_value = keyword.value.value
                    break

        if not has_dag_id:
            issues.append(
                LintIssue(
                    file_path=file_path,
                    line=dag_call.lineno,
                    column=dag_call.col_offset,
                    severity=Severity.ERROR,
                    rule_id="DAG003",
                    message="DAG must have dag_id parameter",
                )
            )
        else:
            if dag_id_value:
                dag_ids.append((dag_id_value, dag_call.lineno))

    # Check dag_id uniqueness
    if len(dag_ids) > 1:
        unique_ids = {id_val for id_val, _ in dag_ids}
        if len(unique_ids) < len(dag_ids):
            issues.append(
                LintIssue(
                    file_path=file_path,
                    line=dag_ids[0][1],
                    column=0,
                    severity=Severity.ERROR,
                    rule_id="DAG004",
                    message="Duplicate dag_id found in file",
                )
            )

    # Check dag_id format
    for dag_id, line in dag_ids:
        if isinstance(dag_id, str) and dag_id.strip() != dag_id:
            issues.append(
                LintIssue(
                    file_path=file_path,
                    line=line,
                    column=0,
                    severity=Severity.WARNING,
                    rule_id="DAG005",
                    message=f"dag_id '{dag_id}' contains extra spaces",
                )
            )

    # DAG006: Check description
    for dag_call in collector.dag_calls:
        has_description = False
        for keyword in dag_call.keywords:
            if keyword.arg == "description":
                has_description = True
                break

        if not has_description:
            issues.append(
                LintIssue(
                    file_path=file_path,
                    line=dag_call.lineno,
                    column=dag_call.col_offset,
                    severity=Severity.WARNING,
                    rule_id="DAG006",
                    message="It is recommended to add DAG description via description parameter",
                )
            )

    # DAG007: Check schedule_interval
    for dag_call in collector.dag_calls:
        params = {kw.arg: kw.value for kw in dag_call.keywords if kw.arg}
        if "schedule_interval" not in params and "schedule" not in params:
            issues.append(
                LintIssue(
                    file_path=file_path,
                    line=dag_call.lineno,
                    column=dag_call.col_offset,
                    severity=Severity.WARNING,
                    rule_id="DAG007",
                    message="It is recommended to explicitly specify schedule_interval or schedule for DAG",
                )
            )

    # DAG009: Check owner in default_args
    if collector.default_args and isinstance(collector.default_args.value, ast.Dict):
        keys = [
            k.value if isinstance(k, ast.Constant) else None
            for k in collector.default_args.value.keys
        ]
        if "owner" not in keys:
            issues.append(
                LintIssue(
                    file_path=file_path,
                    line=collector.default_args.lineno,
                    column=collector.default_args.col_offset,
                    severity=Severity.WARNING,
                    rule_id="DAG009",
                    message="default_args should include owner parameter",
                )
            )

    # DAG010: Check retries in default_args
    # Check if retries exists in operators
    has_retries_in_ops = any(
        any(kw.arg == "retries" for kw in op.keywords) for op in collector.operators
    )

    if (
        not has_retries_in_ops
        and collector.default_args
        and isinstance(collector.default_args.value, ast.Dict)
    ):
        keys = [
            k.value if isinstance(k, ast.Constant) else None
            for k in collector.default_args.value.keys
        ]
        if "retries" not in keys:
            issues.append(
                LintIssue(
                    file_path=file_path,
                    line=collector.default_args.lineno,
                    column=collector.default_args.col_offset,
                    severity=Severity.WARNING,
                    rule_id="DAG010",
                    message="default_args should include retries parameter (if retries is not specified in operators)",
                )
            )

    # DAG011: Check dag_md
    for dag_call in collector.dag_calls:
        provided_params = {kw.arg for kw in dag_call.keywords if kw.arg}
        if "dag_md" not in provided_params:
            issues.append(
                LintIssue(
                    file_path=file_path,
                    line=dag_call.lineno,
                    column=dag_call.col_offset,
                    severity=Severity.ERROR,
                    rule_id="DAG011",
                    message="DAG should have dag_md parameter",
                )
            )

    # DAG012: Check KubernetesPodOperator
    for operator_node in collector.kubernetes_operators:
        provided_params = {kw.arg for kw in operator_node.keywords if kw.arg}
        has_executor_resources = (
            "executor_resources" in provided_params or "executor_config" in provided_params
        )

        missing_resources = []
        if "container_resources" not in provided_params:
            missing_resources.append("container_resources")
        if not has_executor_resources:
            missing_resources.append("executor_resources or executor_config")

        if missing_resources:
            issues.append(
                LintIssue(
                    file_path=file_path,
                    line=operator_node.lineno,
                    column=operator_node.col_offset,
                    severity=Severity.ERROR,
                    rule_id="DAG012",
                    message=f"KubernetesPodOperator must have required resource parameters: {', '.join(missing_resources)}",
                )
            )

    # DAG013: Check start_date in default_args
    # Check if start_date exists in DAG
    has_start_date_in_dag = any(
        any(kw.arg == "start_date" for kw in dag_call.keywords) for dag_call in collector.dag_calls
    )

    if (
        not has_start_date_in_dag
        and collector.default_args
        and isinstance(collector.default_args.value, ast.Dict)
    ):
        keys = [
            k.value if isinstance(k, ast.Constant) else None
            for k in collector.default_args.value.keys
        ]
        if "start_date" not in keys:
            issues.append(
                LintIssue(
                    file_path=file_path,
                    line=collector.default_args.lineno,
                    column=collector.default_args.col_offset,
                    severity=Severity.ERROR,
                    rule_id="DAG013",
                    message="default_args must contain start_date parameter (if start_date is not specified in DAG)",
                )
            )

    return issues
