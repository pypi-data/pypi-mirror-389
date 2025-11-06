"""Best practices from Astronomer and official documentation (use ASTCollector for optimization)."""

import ast

from dagruff.models import LintIssue, Severity
from dagruff.rules.ast_collector import ASTCollector


def check_all_best_practices_rules(collector: ASTCollector, file_path: str) -> list[LintIssue]:
    """Apply all Best Practices rules using collected data.

    This function implements the RuleChecker protocol.

    Args:
        collector: ASTCollector with collected data
        file_path: Path to file

    Returns:
        List of all found issues
    """
    issues: list[LintIssue] = []

    # BP003: Check execution_timeout
    has_default_args_timeout = collector.has_default_args_key("execution_timeout")

    for operator_node in collector.operators:
        has_execution_timeout = any(kw.arg == "execution_timeout" for kw in operator_node.keywords)

        if not has_execution_timeout and not has_default_args_timeout:
            issues.append(
                LintIssue(
                    file_path=file_path,
                    line=operator_node.lineno,
                    column=operator_node.col_offset,
                    severity=Severity.INFO,
                    rule_id="BP003",
                    message="It is recommended to specify execution_timeout for task to prevent infinite execution",
                )
            )

    # BP005: Check task docstrings
    for operator_node in collector.operators:
        has_task_id = False
        task_id_value = None

        for keyword in operator_node.keywords:
            if keyword.arg == "task_id":
                has_task_id = True
                if isinstance(keyword.value, ast.Constant):
                    task_id_value = keyword.value.value
                break

        has_docstring = any(
            kw.arg in ["doc", "doc_md", "doc_json", "doc_yaml"] for kw in operator_node.keywords
        )

        if not has_docstring and has_task_id:
            issues.append(
                LintIssue(
                    file_path=file_path,
                    line=operator_node.lineno,
                    column=operator_node.col_offset,
                    severity=Severity.INFO,
                    rule_id="BP005",
                    message=f"It is recommended to add docstring (doc_md) for task '{task_id_value or 'task'}' for better documentation",
                )
            )

    # BP006: Check dagrun_timeout
    for dag_call in collector.dag_calls:
        has_dagrun_timeout = any(kw.arg == "dagrun_timeout" for kw in dag_call.keywords)

        if not has_dagrun_timeout:
            issues.append(
                LintIssue(
                    file_path=file_path,
                    line=dag_call.lineno,
                    column=dag_call.col_offset,
                    severity=Severity.INFO,
                    rule_id="BP006",
                    message="It is recommended to specify dagrun_timeout for DAG to set maximum DAG Run execution time",
                )
            )

    # BP001, BP002, AIRFLINT003: Check top-level code
    dangerous_patterns = [
        ("get_records", "Hook"),
        ("execute", "Hook"),
        ("get", "requests"),
        ("post", "requests"),
        ("fetch", "API"),
        ("read", "s3"),
        ("read", "gcs"),
    ]

    # Check top-level calls (simplified version - detailed check requires additional logic)
    for call_node in collector.top_level_calls:
        func = call_node.func

        if isinstance(func, ast.Attribute):
            attr_name = func.attr

            # BP001: External system calls
            if any(
                pattern[0] in attr_name.lower() for pattern in dangerous_patterns
            ) and isinstance(func.value, ast.Name):
                var_name = func.value.id
                if "Hook" in var_name or "Client" in var_name:
                    issues.append(
                        LintIssue(
                            file_path=file_path,
                            line=call_node.lineno,
                            column=call_node.col_offset,
                            severity=Severity.WARNING,
                            rule_id="BP001",
                            message=f"Top-level code with {attr_name} call found. Move this code inside a task so it executes only when the task runs, not on every DAG parse",
                        )
                    )

            # BP002: datetime functions
            if attr_name in ["today", "now", "utcnow"]:
                call_str = ""
                if isinstance(func.value, ast.Name) and func.value.id == "datetime":
                    call_str = f"datetime.{attr_name}()"
                elif (
                    isinstance(func.value, ast.Attribute)
                    and func.value.attr == "datetime"
                    and isinstance(func.value.value, ast.Name)
                    and func.value.value.id == "datetime"
                ):
                    call_str = f"datetime.datetime.{attr_name}()"

                if call_str:
                    issues.append(
                        LintIssue(
                            file_path=file_path,
                            line=call_node.lineno,
                            column=call_node.col_offset,
                            severity=Severity.WARNING,
                            rule_id="BP002",
                            message=f"Using {call_str} in top-level code violates DAG idempotency. Use Airflow variables and macros (e.g., {{{{ ds }}}}, {{{{ prev_start_date_success }}}}) instead",
                        )
                    )

            # AIRFLINT003: Variable.get()
            if attr_name == "get" and isinstance(func.value, ast.Name):
                var_name = func.value.id
                if var_name == "Variable":
                    issues.append(
                        LintIssue(
                            file_path=file_path,
                            line=call_node.lineno,
                            column=call_node.col_offset,
                            severity=Severity.INFO,
                            rule_id="AIRFLINT003",
                            message="Variable.get() at module level executes on every DAG parse. Use Variable.get() inside functions or tasks",
                        )
                    )

    # BP004: Check dependency consistency
    has_bitwise_ops = len(collector.rshift_lshift_ops) > 0
    has_upstream_downstream = len(collector.upstream_downstream_calls) > 0

    if has_bitwise_ops and has_upstream_downstream:
        issues.append(
            LintIssue(
                file_path=file_path,
                line=1,
                column=0,
                severity=Severity.WARNING,
                rule_id="BP004",
                message="Mixing dependency methods (>>/<< and set_upstream/set_downstream) found. It is recommended to use one consistent method for better readability",
            )
        )

    return issues
