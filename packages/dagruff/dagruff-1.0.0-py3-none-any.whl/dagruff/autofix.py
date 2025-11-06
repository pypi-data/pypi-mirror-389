"""Module for automatic fixing of issues in DAG files."""

import ast
import os
import re
from pathlib import Path

from dagruff.constants import (
    # Airflow
    AIRFLOW_MODULE_NAME,
    CATCHUP_PARAM_VALUE_TEMPLATE,
    DAG_CALL_PATTERN,
    DAG_CLASS_NAME,
    DAG_IMPORT_STATEMENT,
    FROM_KEYWORD,
    # Python syntax
    IMPORT_KEYWORD,
    MAX_ACTIVE_RUNS_PARAM_VALUE_TEMPLATE,
    MAX_ACTIVE_TASKS_PARAM_VALUE_TEMPLATE,
    MAX_ACTIVE_TASKS_REPLACEMENT,
    # Autofix
    MAX_LINES_TO_SEARCH,
    # Autofix templates
    OWNER_KEY_VALUE_TEMPLATE,
    RETRIES_KEY_VALUE_TEMPLATE,
)
from dagruff.logger import get_logger
from dagruff.models import LintIssue
from dagruff.rules.utils import find_dag_calls
from dagruff.validation import validate_encoding, validate_file_path

logger = get_logger(__name__)


def apply_fixes(file_path: str, issues: list[LintIssue]) -> tuple[str, list[str]]:
    """Apply autofixes to file.

    Args:
        file_path: Path to file
        issues: List of issues to fix

    Returns:
        Tuple (fixed code, list of applied rules)
    """
    # Validate file before processing
    is_valid, error_msg = validate_file_path(file_path)
    if not is_valid:
        logger.error(f"Cannot apply fixes: file validation failed: {error_msg}")
        return "", []

    # Validate encoding
    is_valid_encoding, encoding_error = validate_encoding(file_path)
    if not is_valid_encoding:
        logger.error(f"Cannot apply fixes: encoding validation failed: {encoding_error}")
        return "", []

    # Check write permissions before processing
    path = Path(file_path)
    if not os.access(path, os.W_OK):
        logger.error(f"Cannot apply fixes: no write permission for file: {file_path}")
        return "", []

    with open(file_path, encoding="utf-8") as f:
        source_code = f.read()

    # Split into lines for processing
    lines = source_code.splitlines(keepends=True)
    applied_fixes = []

    # Group issues by rules
    # Dictionary mapping rule IDs to their fix functions
    fixable_rules = {
        "DAG001": fix_dag001,
        "DAG005": fix_dag005,
        "DAG009": fix_dag009,
        "DAG010": fix_dag010,
        "AIR003": fix_air003,
        "AIR013": fix_air013,
        "AIR014": fix_air014,
    }

    # Sort issues by line number (from end to start to avoid index issues)
    sorted_issues = sorted(issues, key=lambda x: x.line, reverse=True)

    # Parse AST once
    try:
        tree = ast.parse(source_code, filename=file_path)
        logger.debug(f"AST successfully parsed for {file_path}")
    except SyntaxError as e:
        logger.error(f"Syntax error in {file_path}, cannot apply autofixes: {e}", exc_info=True)
        return source_code, []

    # Apply fixes one by one
    logger.info(f"Applying autofixes for {len(sorted_issues)} issues in {file_path}")
    for issue in sorted_issues:
        if issue.rule_id in fixable_rules:
            fix_func = fixable_rules[issue.rule_id]
            try:
                logger.debug(f"Applying fix {issue.rule_id} for {file_path}:{issue.line}")
                new_source = fix_func(source_code, tree, issue, lines)
                if new_source != source_code:
                    source_code = new_source
                    # Update lines only once after code change
                    lines = source_code.splitlines(keepends=True)
                    # Reparse tree after changes
                    try:
                        tree = ast.parse(source_code, filename=file_path)
                        logger.debug(f"AST reparsed after applying {issue.rule_id}")
                    except SyntaxError as e:
                        logger.warning(
                            f"Error reparsing AST after {issue.rule_id} in {file_path}: {e}"
                        )
                        # Continue with current tree
                    applied_fixes.append(issue.rule_id)
                    logger.debug(f"Fix {issue.rule_id} successfully applied")
            except (ValueError, IndexError, KeyError, AttributeError) as e:
                # Data access errors when applying fix
                logger.exception(
                    f"Data access error when applying fix {issue.rule_id} for {file_path}:{issue.line}: {e}"
                )
                # Continue with next fix
                continue
            except OSError as e:
                # File handling errors
                logger.exception(
                    f"File handling error when applying fix {issue.rule_id} for {file_path}: {e}"
                )
                # Continue with next fix
                continue
            except (KeyboardInterrupt, SystemExit):
                # System exceptions should not be caught
                raise
            except Exception as e:
                # Last catch-all only for unexpected errors
                logger.exception(
                    f"Unexpected error when applying fix {issue.rule_id} for {file_path}:{issue.line}: {e}"
                )
                # Continue with next fix
                continue

    logger.info(f"Applied {len(applied_fixes)} autofixes in {file_path}: {applied_fixes}")
    return source_code, applied_fixes


def fix_dag001(source_code: str, tree: ast.AST, issue: LintIssue, lines: list[str]) -> str:
    """DAG001: Add DAG import."""
    # Check if DAG import already exists
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            if node.module and AIRFLOW_MODULE_NAME in node.module:
                for alias in node.names:
                    if alias.name == DAG_CLASS_NAME:
                        return source_code  # Import already exists
        elif isinstance(node, ast.Import):
            for alias in node.names:
                if AIRFLOW_MODULE_NAME in alias.name and DAG_CLASS_NAME in alias.name:
                    return source_code  # Import already exists

    # Use passed lines if available, otherwise split again
    # Make a copy to avoid modifying original list
    lines_list = lines[:] if lines else source_code.splitlines(keepends=True)

    # Find end of import block
    insert_pos = 0
    for i, line in enumerate(lines_list):
        stripped = line.strip()
        if (
            stripped.startswith("#")
            or stripped.startswith(IMPORT_KEYWORD)
            or stripped.startswith(FROM_KEYWORD)
        ):
            insert_pos = i + 1
        elif stripped and insert_pos == 0:
            # First non-empty line that's not an import - insert here
            insert_pos = i
            break

    lines_list.insert(insert_pos, DAG_IMPORT_STATEMENT)
    return "".join(lines_list)


def fix_dag005(source_code: str, tree: ast.AST, issue: LintIssue, lines: list[str]) -> str:
    """DAG005: Remove spaces in dag_id using AST-based approach.

    Uses AST to find DAG call and dag_id parameter, then applies precise fix.
    """
    # Find DAG calls via AST
    dag_calls = find_dag_calls(tree)
    if not dag_calls:
        return source_code

    # Use passed lines if available, otherwise split again
    lines_list = lines[:] if lines else source_code.splitlines(keepends=True)

    # Find DAG call on the issue line
    target_dag_call = None
    for dag_call in dag_calls:
        if dag_call.lineno == issue.line:
            target_dag_call = dag_call
            break

    if not target_dag_call:
        # Fallback to regex if AST didn't find it
        if issue.line > 0 and issue.line <= len(lines_list):
            line = lines_list[issue.line - 1]
            # More precise regex: match dag_id= with quotes and optional whitespace in value
            pattern = r"(dag_id\s*=\s*)([\"'])\s*([^\"']*?)\s*(\2)"
            new_line = re.sub(
                pattern, lambda m: f"{m.group(1)}{m.group(2)}{m.group(3).strip()}{m.group(4)}", line
            )
            if new_line != line:
                lines_list[issue.line - 1] = new_line
                return "".join(lines_list)
        return source_code

    # Find dag_id parameter in AST
    dag_id_keyword = None
    for keyword in target_dag_call.keywords:
        if keyword.arg == "dag_id":
            dag_id_keyword = keyword
            break

    if not dag_id_keyword:
        return source_code

    # Get dag_id value from AST
    if isinstance(dag_id_keyword.value, (ast.Str, ast.Constant)):
        # Extract original value
        if isinstance(dag_id_keyword.value, ast.Constant):
            original_value = dag_id_keyword.value.value
            if not isinstance(original_value, str):
                return source_code
        else:
            original_value = dag_id_keyword.value.s

        # Strip spaces from value
        stripped_value = original_value.strip()
        if stripped_value == original_value:
            return source_code  # No spaces to remove

        # Find the line and apply fix
        line_index = dag_id_keyword.lineno - 1
        if 0 <= line_index < len(lines_list):
            line = lines_list[line_index]
            # Use more precise regex to replace only the value part
            # Match dag_id="  value  " or dag_id='  value  '
            pattern = r"(dag_id\s*=\s*)([\"'])\s*([^\"']*?)\s*(\2)"
            new_line = re.sub(
                pattern, lambda m: f"{m.group(1)}{m.group(2)}{stripped_value}{m.group(4)}", line
            )
            if new_line != line:
                lines_list[line_index] = new_line
                return "".join(lines_list)

    return source_code


def _add_key_to_dict_block(
    source_code: str,
    tree: ast.AST,
    dict_name: str,
    key_name: str,
    key_value: str,
    check_ast: bool = True,
    lines: list[str] = None,
) -> str:
    """Helper function to add key to dictionary (e.g., default_args).

    Args:
        source_code: Source code
        tree: AST tree
        dict_name: Variable name with dictionary (e.g., "default_args")
        key_name: Key name to add (e.g., "owner")
        key_value: String with value to insert (e.g., '"owner": "airflow",')
        check_ast: Check for key existence via AST
        lines: Pre-split code into lines (optional)

    Returns:
        Modified source code
    """
    # Check via AST if key already exists
    if check_ast:
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if (
                        isinstance(target, ast.Name)
                        and target.id == dict_name
                        and isinstance(node.value, ast.Dict)
                    ):
                        keys = [
                            k.value if isinstance(k, ast.Constant) else None
                            for k in node.value.keys
                        ]
                        if key_name in keys:
                            return source_code  # Key already exists

    # Use passed lines if available, otherwise split again
    lines_list = lines[:] if lines else source_code.splitlines(keepends=True)

    # Find line with dict_name
    for i, line in enumerate(lines_list):
        if dict_name in line and "=" in line:
            # Search for dictionary block
            start_line = i
            bracket_count = 0
            found_dict = False

            for j in range(i, min(i + MAX_LINES_TO_SEARCH, len(lines_list))):
                line_content = lines_list[j]
                bracket_count += line_content.count("{") - line_content.count("}")

                if "{" in line_content:
                    found_dict = True

                if found_dict and bracket_count == 0 and "}" in line_content:
                    # Found closing brace
                    # Check if key already exists in this block
                    has_key = False
                    key_patterns = [f'"{key_name}"', f"'{key_name}'"]
                    for k in range(start_line, j):
                        if any(pattern in lines_list[k] for pattern in key_patterns):
                            has_key = True
                            break

                    if not has_key:
                        # Insert before closing brace
                        indent = len(lines_list[j]) - len(lines_list[j].lstrip())
                        key_line = " " * indent + key_value + "\n"

                        # Find last comma or key before }
                        insert_pos = j
                        for k in range(j - 1, start_line - 1, -1):
                            if lines_list[k].strip() and not lines_list[k].strip().startswith("#"):
                                insert_pos = k + 1
                                break

                        lines_list.insert(insert_pos, key_line)
                    break
            break

    return "".join(lines_list)


def fix_dag009(source_code: str, tree: ast.AST, issue: LintIssue, lines: list[str]) -> str:
    """DAG009: Add owner to default_args."""
    return _add_key_to_dict_block(
        source_code, tree, "default_args", "owner", OWNER_KEY_VALUE_TEMPLATE, lines=lines
    )


def fix_dag010(source_code: str, tree: ast.AST, issue: LintIssue, lines: list[str]) -> str:
    """DAG010: Add retries to default_args."""
    return _add_key_to_dict_block(
        source_code, tree, "default_args", "retries", RETRIES_KEY_VALUE_TEMPLATE, lines=lines
    )


def _add_param_to_dag_call(
    source_code: str,
    tree: ast.AST,
    issue: LintIssue,
    param_name: str,
    param_value: str,
    check_ast: bool = True,
    lines: list[str] = None,
) -> str:
    """Helper function to add parameter to DAG call.

    Args:
        source_code: Source code
        tree: AST tree
        issue: Issue with line information
        param_name: Parameter name to add (e.g., "catchup")
        param_value: String with parameter value to insert (e.g., "catchup=False,")
        check_ast: Check for parameter existence via AST
        lines: Pre-split code into lines (optional)

    Returns:
        Modified source code
    """
    dag_calls = find_dag_calls(tree)
    if not dag_calls:
        return source_code

    # Check via AST if parameter already exists
    if check_ast:
        for dag_call in dag_calls:
            if dag_call.lineno == issue.line:
                for keyword in dag_call.keywords:
                    if keyword.arg == param_name:
                        return source_code  # Parameter already exists

    # Use passed lines if available, otherwise split again
    lines_list = lines[:] if lines else source_code.splitlines(keepends=True)

    # Find DAG call by line number from issue
    target_line = issue.line - 1

    if target_line < 0 or target_line >= len(lines_list):
        return source_code

    # Search for DAG call in this area
    for dag_call in dag_calls:
        if dag_call.lineno == issue.line:
            # Find closing parenthesis of DAG call
            bracket_count = 0
            found_call = False
            start_line = dag_call.lineno - 1

            for j in range(start_line, min(start_line + MAX_LINES_TO_SEARCH, len(lines_list))):
                line_content = lines_list[j]
                bracket_count += line_content.count("(") - line_content.count(")")

                if DAG_CALL_PATTERN in line_content or (found_call and "(" in line_content):
                    found_call = True

                if found_call and bracket_count == 0 and ")" in line_content:
                    # Check if parameter already exists in this block
                    has_param = False
                    param_patterns = [f'"{param_name}"', f"'{param_name}'", f"{param_name}="]
                    for k in range(start_line, j):
                        if any(pattern in lines_list[k] for pattern in param_patterns):
                            has_param = True
                            break

                    if not has_param:
                        # Found closing parenthesis
                        # Insert before closing parenthesis
                        indent = len(lines_list[j]) - len(lines_list[j].lstrip())
                        param_line = " " * indent + param_value + "\n"

                        # Find last comma before )
                        insert_pos = j
                        for k in range(j - 1, start_line - 1, -1):
                            if lines_list[k].strip() and not lines_list[k].strip().startswith("#"):
                                insert_pos = k + 1
                                break

                        lines_list.insert(insert_pos, param_line)
                    break
            break

    return "".join(lines_list)


def fix_air003(source_code: str, tree: ast.AST, issue: LintIssue, lines: list[str]) -> str:
    """AIR003: Add catchup=False to DAG."""
    return _add_param_to_dag_call(
        source_code, tree, issue, "catchup", CATCHUP_PARAM_VALUE_TEMPLATE, lines=lines
    )


def fix_air013(source_code: str, tree: ast.AST, issue: LintIssue, lines: list[str]) -> str:
    """AIR013: Add max_active_runs=1 to DAG."""
    return _add_param_to_dag_call(
        source_code,
        tree,
        issue,
        "max_active_runs",
        MAX_ACTIVE_RUNS_PARAM_VALUE_TEMPLATE,
        lines=lines,
    )


def fix_air014(source_code: str, tree: ast.AST, issue: LintIssue, lines: list[str]) -> str:
    """AIR014: Replace concurrency with max_active_tasks or add max_active_tasks using AST-based approach."""
    dag_calls = find_dag_calls(tree)
    if not dag_calls:
        return source_code

    # Use passed lines if available, otherwise split again
    lines_list = lines[:] if lines else source_code.splitlines(keepends=True)

    # Check if concurrency exists in message
    has_concurrency = "concurrency" in issue.message.lower()

    if has_concurrency:
        # Find concurrency parameter via AST and replace precisely
        for dag_call in dag_calls:
            if dag_call.lineno == issue.line:
                for keyword in dag_call.keywords:
                    if keyword.arg == "concurrency":
                        # Found concurrency parameter, replace it
                        line_index = keyword.lineno - 1
                        if 0 <= line_index < len(lines_list):
                            line = lines_list[line_index]
                            # More precise regex: match word boundary and exact parameter name
                            pattern = r"\bconcurrency\s*="
                            new_line = re.sub(pattern, MAX_ACTIVE_TASKS_REPLACEMENT, line)
                            if new_line != line:
                                lines_list[line_index] = new_line
                                return "".join(lines_list)
                        break

        # Fallback: search all lines if AST didn't find it (e.g., if parameter is on different line)
        for i, line in enumerate(lines_list):
            # More precise regex: match word boundary to avoid partial matches
            pattern = r"\bconcurrency\s*="
            new_line = re.sub(pattern, MAX_ACTIVE_TASKS_REPLACEMENT, line)
            if new_line != line:
                lines_list[i] = new_line
    else:
        # Add max_active_tasks=1 using helper function
        # Rebuild source_code from lines_list for checking
        temp_source = "".join(lines_list)
        result = _add_param_to_dag_call(
            temp_source,
            tree,
            issue,
            "max_active_tasks",
            MAX_ACTIVE_TASKS_PARAM_VALUE_TEMPLATE,
            check_ast=False,
            lines=lines_list,
        )
        return result

    return "".join(lines_list)
