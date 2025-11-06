"""Helper functions for rules."""

import ast


def find_dag_calls(tree: ast.AST) -> list[ast.Call]:
    """Find all DAG() calls in tree.

    Args:
        tree: AST tree

    Returns:
        List of ast.Call nodes with DAG calls
    """
    dag_calls = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and (
            isinstance(node.func, ast.Name)
            and node.func.id == "DAG"
            or isinstance(node.func, ast.Attribute)
            and node.func.attr == "DAG"
        ):
            dag_calls.append(node)

    return dag_calls


def find_operators(tree: ast.AST) -> list[ast.Call]:
    """Find all operator calls in tree.

    Args:
        tree: AST tree

    Returns:
        List of ast.Call nodes with operators
    """
    operators = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func = node.func
            operator_name = None

            if isinstance(func, ast.Name):
                operator_name = func.id
            elif isinstance(func, ast.Attribute):
                operator_name = func.attr

            if operator_name and "Operator" in operator_name:
                operators.append(node)

    return operators


def is_inside_task_or_operator(node: ast.AST) -> bool:
    """Check if node is inside task or operator.

    Args:
        node: AST node

    Returns:
        True if node is inside operator
    """
    # Simplified check: look for operators in the same scope
    # For more accurate check, AST traversal with context preservation is needed
    if isinstance(node, ast.Call):
        # If node is an operator call, don't check it
        func = node.func
        if isinstance(func, ast.Name):
            if "Operator" in func.id:
                return True
        elif isinstance(func, ast.Attribute) and "Operator" in func.attr:
            return True

    return False


def get_default_args_start_date(tree: ast.AST) -> bool:
    """Check for start_date presence in default_args.

    Args:
        tree: AST tree

    Returns:
        True if start_date found in default_args
    """
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if (
                    isinstance(target, ast.Name)
                    and target.id == "default_args"
                    and isinstance(node.value, ast.Dict)
                ):
                    keys = [
                        k.value if isinstance(k, ast.Constant) else None for k in node.value.keys
                    ]
                    if "start_date" in keys:
                        return True
    return False


def has_start_date_in_dag(tree: ast.AST) -> bool:
    """Check for start_date presence in DAG parameters.

    Args:
        tree: AST tree

    Returns:
        True if start_date found in DAG parameters
    """
    dag_calls = find_dag_calls(tree)
    for dag_call in dag_calls:
        for keyword in dag_call.keywords:
            if keyword.arg == "start_date":
                return True
    return False


def has_retries_in_operators(tree: ast.AST) -> bool:
    """Check for retries presence in operator parameters.

    Args:
        tree: AST tree

    Returns:
        True if retries found in at least one operator
    """
    operators = find_operators(tree)
    for operator_node in operators:
        for keyword in operator_node.keywords:
            if keyword.arg == "retries":
                return True
    return False
