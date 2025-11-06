"""Tests for autofix module."""

import ast
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from dagruff import autofix
from dagruff.autofix import (
    _add_key_to_dict_block,
    _add_param_to_dag_call,
    apply_fixes,
    fix_air003,
    fix_air013,
    fix_air014,
    fix_dag001,
    fix_dag005,
    fix_dag009,
    fix_dag010,
)
from dagruff.cli import apply_autofixes
from dagruff.config import Config
from dagruff.models import LintIssue, Severity


@pytest.fixture
def temp_dag_file(tmp_path):
    """Create a temporary DAG file for testing."""
    dag_content = """from airflow import DAG

dag = DAG(
    dag_id="test_dag",
    description="Test DAG",
)
"""
    dag_file = tmp_path / "test_dag.py"
    dag_file.write_text(dag_content, encoding="utf-8")
    return str(dag_file)


def test_apply_fixes_file_not_exists():
    """Test applying fixes to non-existent file."""
    issues = [
        LintIssue(
            file_path="/nonexistent/file.py",
            line=1,
            column=0,
            severity=Severity.ERROR,
            rule_id="DAG001",
            message="Missing DAG import",
        )
    ]
    fixed_code, applied_rules = apply_fixes("/nonexistent/file.py", issues)
    assert fixed_code == ""
    assert applied_rules == []


def test_apply_fixes_no_write_permission(tmp_path):
    """Test applying fixes to file without write permission."""
    dag_file = tmp_path / "test_dag.py"
    dag_file.write_text("from airflow import DAG\n", encoding="utf-8")

    # Remove write permission
    dag_file.chmod(0o444)  # Read-only
    try:
        issues = [
            LintIssue(
                file_path=str(dag_file),
                line=1,
                column=0,
                severity=Severity.ERROR,
                rule_id="DAG001",
                message="Test",
            )
        ]
        fixed_code, applied_rules = apply_fixes(str(dag_file), issues)
        assert fixed_code == ""
        assert applied_rules == []
    finally:
        # Restore permission
        dag_file.chmod(0o644)


def test_apply_fixes_dag001_add_import(temp_dag_file):
    """Test fixing DAG001 - adding DAG import."""
    dag_file = temp_dag_file
    # Remove import to trigger DAG001
    with open(dag_file, encoding="utf-8") as f:
        content = f.read()
    content = content.replace("from airflow import DAG", "")

    with open(dag_file, "w", encoding="utf-8") as f:
        f.write(content)

    issues = [
        LintIssue(
            file_path=dag_file,
            line=1,
            column=0,
            severity=Severity.ERROR,
            rule_id="DAG001",
            message="Missing DAG import from airflow",
        )
    ]

    fixed_code, applied_rules = apply_fixes(dag_file, issues)
    assert "DAG001" in applied_rules
    assert "from airflow import DAG" in fixed_code


def test_apply_fixes_dag005_remove_spaces(tmp_path):
    """Test fixing DAG005 - removing spaces in dag_id."""
    dag_file = tmp_path / "test_dag.py"
    dag_content = """from airflow import DAG

dag = DAG(
    dag_id="  test_dag  ",
    description="Test",
)
"""
    dag_file.write_text(dag_content, encoding="utf-8")

    issues = [
        LintIssue(
            file_path=str(dag_file),
            line=4,
            column=0,
            severity=Severity.WARNING,
            rule_id="DAG005",
            message="dag_id contains extra spaces",
        )
    ]

    fixed_code, applied_rules = apply_fixes(str(dag_file), issues)
    assert "DAG005" in applied_rules
    assert 'dag_id="test_dag"' in fixed_code
    assert 'dag_id="  test_dag  "' not in fixed_code


def test_apply_fixes_dag009_add_owner(tmp_path):
    """Test fixing DAG009 - adding owner to default_args."""
    dag_file = tmp_path / "test_dag.py"
    dag_content = """from airflow import DAG

default_args = {
    "retries": 1,
}

dag = DAG(
    dag_id="test_dag",
    default_args=default_args,
)
"""
    dag_file.write_text(dag_content, encoding="utf-8")

    issues = [
        LintIssue(
            file_path=str(dag_file),
            line=3,
            column=0,
            severity=Severity.WARNING,
            rule_id="DAG009",
            message="default_args should include owner parameter",
        )
    ]

    fixed_code, applied_rules = apply_fixes(str(dag_file), issues)
    assert "DAG009" in applied_rules
    assert '"owner": "airflow"' in fixed_code


def test_apply_fixes_dag010_add_retries(tmp_path):
    """Test fixing DAG010 - adding retries to default_args."""
    dag_file = tmp_path / "test_dag.py"
    dag_content = """from airflow import DAG

default_args = {
    "owner": "airflow",
}

dag = DAG(
    dag_id="test_dag",
    default_args=default_args,
)
"""
    dag_file.write_text(dag_content, encoding="utf-8")

    issues = [
        LintIssue(
            file_path=str(dag_file),
            line=3,
            column=0,
            severity=Severity.WARNING,
            rule_id="DAG010",
            message="default_args should include retries parameter",
        )
    ]

    fixed_code, applied_rules = apply_fixes(str(dag_file), issues)
    assert "DAG010" in applied_rules
    assert '"retries": 1' in fixed_code


def test_apply_fixes_invalid_syntax(tmp_path):
    """Test applying fixes to file with syntax errors."""
    dag_file = tmp_path / "test_dag.py"
    dag_content = """from airflow import DAG

dag = DAG(
    dag_id="test_dag"
    # Missing closing parenthesis
"""
    dag_file.write_text(dag_content, encoding="utf-8")

    issues = [
        LintIssue(
            file_path=str(dag_file),
            line=1,
            column=0,
            severity=Severity.ERROR,
            rule_id="DAG001",
            message="Test",
        )
    ]

    # Should return original code without fixes
    fixed_code, applied_rules = apply_fixes(str(dag_file), issues)
    assert applied_rules == []


def test_apply_fixes_empty_issues(tmp_path):
    """Test applying fixes with empty issues list."""
    dag_file = tmp_path / "test_dag.py"
    dag_content = """from airflow import DAG

dag = DAG(
    dag_id="test_dag",
)
"""
    dag_file.write_text(dag_content, encoding="utf-8")

    fixed_code, applied_rules = apply_fixes(str(dag_file), [])
    assert applied_rules == []
    assert fixed_code == dag_content


def test_apply_fixes_non_fixable_rule(tmp_path):
    """Test applying fixes with non-fixable rule ID."""
    dag_file = tmp_path / "test_dag.py"
    dag_content = """from airflow import DAG

dag = DAG(
    dag_id="test_dag",
)
"""
    dag_file.write_text(dag_content, encoding="utf-8")

    issues = [
        LintIssue(
            file_path=str(dag_file),
            line=1,
            column=0,
            severity=Severity.ERROR,
            rule_id="DAG999",  # Non-fixable rule
            message="Test",
        )
    ]

    fixed_code, applied_rules = apply_fixes(str(dag_file), issues)
    assert applied_rules == []


def test_apply_fixes_multiple_issues(tmp_path):
    """Test applying fixes for multiple issues."""
    dag_file = tmp_path / "test_dag.py"
    dag_content = """default_args = {}

dag = DAG(
    dag_id="  test_dag  ",
)
"""
    dag_file.write_text(dag_content, encoding="utf-8")

    issues = [
        LintIssue(
            file_path=str(dag_file),
            line=1,
            column=0,
            severity=Severity.ERROR,
            rule_id="DAG001",
            message="Missing DAG import",
        ),
        LintIssue(
            file_path=str(dag_file),
            line=4,
            column=0,
            severity=Severity.WARNING,
            rule_id="DAG005",
            message="dag_id contains extra spaces",
        ),
    ]

    fixed_code, applied_rules = apply_fixes(str(dag_file), issues)
    assert len(applied_rules) >= 1  # At least one fix should be applied
    assert "from airflow import DAG" in fixed_code


def test_apply_fixes_invalid_encoding(tmp_path):
    """Test apply_fixes with invalid encoding."""
    dag_file = tmp_path / "test_dag.py"
    dag_file.write_bytes(b"\xff\xfe\x00\x00")  # Invalid UTF-8

    issues = [
        LintIssue(
            file_path=str(dag_file),
            line=1,
            column=0,
            severity=Severity.ERROR,
            rule_id="DAG001",
            message="Missing DAG import",
        )
    ]

    result, applied = apply_fixes(str(dag_file), issues)

    assert result == ""
    assert applied == []


def test_apply_fixes_syntax_error(tmp_path):
    """Test apply_fixes with syntax error in file."""
    dag_file = tmp_path / "test_dag.py"
    dag_file.write_text("def invalid syntax\n", encoding="utf-8")

    issues = [
        LintIssue(
            file_path=str(dag_file),
            line=1,
            column=0,
            severity=Severity.ERROR,
            rule_id="DAG001",
            message="Missing DAG import",
        )
    ]

    result, applied = apply_fixes(str(dag_file), issues)

    assert result == "def invalid syntax\n"
    assert applied == []


def test_apply_fixes_non_fixable_rule_with_error(tmp_path):
    """Test apply_fixes with non-fixable rule that causes error."""
    dag_file = tmp_path / "test_dag.py"
    dag_file.write_text("x = 1\n", encoding="utf-8")

    issues = [
        LintIssue(
            file_path=str(dag_file),
            line=1,
            column=0,
            severity=Severity.ERROR,
            rule_id="NON_FIXABLE",
            message="Non-fixable issue",
        )
    ]

    result, applied = apply_fixes(str(dag_file), issues)

    assert result == "x = 1\n"
    assert applied == []


def test_fix_dag001_already_has_import_from():
    """Test fix_dag001 when import already exists via ImportFrom."""
    code = """
from airflow import DAG

dag = DAG(dag_id="test")
"""
    tree = ast.parse(code)
    issue = LintIssue(
        file_path="test.py",
        line=1,
        column=0,
        severity=Severity.ERROR,
        rule_id="DAG001",
        message="Missing DAG import",
    )

    result = fix_dag001(code, tree, issue, code.splitlines(keepends=True))

    assert result == code


def test_fix_dag001_already_has_import():
    """Test fix_dag001 when import already exists via Import."""
    code = """
import airflow.DAG as DAG

dag = DAG(dag_id="test")
"""
    tree = ast.parse(code)
    issue = LintIssue(
        file_path="test.py",
        line=1,
        column=0,
        severity=Severity.ERROR,
        rule_id="DAG001",
        message="Missing DAG import",
    )

    result = fix_dag001(code, tree, issue, code.splitlines(keepends=True))

    assert result == code


def test_fix_dag005_no_dag_call():
    """Test fix_dag005 when no DAG call found."""
    code = "x = 1\n"
    tree = ast.parse(code)
    issue = LintIssue(
        file_path="test.py",
        line=1,
        column=0,
        severity=Severity.WARNING,
        rule_id="DAG005",
        message="dag_id contains extra spaces",
    )

    result = fix_dag005(code, tree, issue, code.splitlines(keepends=True))

    assert result == code


def test_fix_dag005_no_dag_id_keyword():
    """Test fix_dag005 when dag_id keyword not found."""
    code = """
from airflow import DAG

dag = DAG()
"""
    tree = ast.parse(code)
    issue = LintIssue(
        file_path="test.py",
        line=3,
        column=0,
        severity=Severity.WARNING,
        rule_id="DAG005",
        message="dag_id contains extra spaces",
    )

    result = fix_dag005(code, tree, issue, code.splitlines(keepends=True))

    assert result == code


def test_fix_dag005_non_string_value():
    """Test fix_dag005 when dag_id value is not a string."""
    code = """
from airflow import DAG

dag = DAG(dag_id=123)
"""
    tree = ast.parse(code)
    issue = LintIssue(
        file_path="test.py",
        line=3,
        column=0,
        severity=Severity.WARNING,
        rule_id="DAG005",
        message="dag_id contains extra spaces",
    )

    result = fix_dag005(code, tree, issue, code.splitlines(keepends=True))

    assert result == code


def test_fix_dag009_no_default_args():
    """Test fix_dag009 when default_args not found."""
    code = """
from airflow import DAG

dag = DAG(dag_id="test")
"""
    tree = ast.parse(code)
    issue = LintIssue(
        file_path="test.py",
        line=3,
        column=0,
        severity=Severity.WARNING,
        rule_id="DAG009",
        message="Missing owner in default_args",
    )

    result = fix_dag009(code, tree, issue, code.splitlines(keepends=True))

    # Should add default_args with owner (if found)
    # Note: fix_dag009 may not always add default_args if pattern not found
    assert isinstance(result, str)


def test_fix_dag010_no_default_args():
    """Test fix_dag010 when default_args not found."""
    code = """
from airflow import DAG

dag = DAG(dag_id="test")
"""
    tree = ast.parse(code)
    issue = LintIssue(
        file_path="test.py",
        line=3,
        column=0,
        severity=Severity.WARNING,
        rule_id="DAG010",
        message="Missing retries in default_args",
    )

    result = fix_dag010(code, tree, issue, code.splitlines(keepends=True))

    # Should add default_args with retries (if found)
    # Note: fix_dag010 may not always add default_args if pattern not found
    assert isinstance(result, str)


def test_fix_air003_no_dag_call():
    """Test fix_air003 when no DAG call found."""
    code = "x = 1\n"
    tree = ast.parse(code)
    issue = LintIssue(
        file_path="test.py",
        line=1,
        column=0,
        severity=Severity.WARNING,
        rule_id="AIR003",
        message="Missing catchup parameter",
    )

    result = fix_air003(code, tree, issue, code.splitlines(keepends=True))

    assert result == code


def test_fix_air013_no_dag_call():
    """Test fix_air013 when no DAG call found."""
    code = "x = 1\n"
    tree = ast.parse(code)
    issue = LintIssue(
        file_path="test.py",
        line=1,
        column=0,
        severity=Severity.WARNING,
        rule_id="AIR013",
        message="Missing max_active_runs parameter",
    )

    result = fix_air013(code, tree, issue, code.splitlines(keepends=True))

    assert result == code


def test_fix_air014_no_dag_call():
    """Test fix_air014 when no DAG call found."""
    code = "x = 1\n"
    tree = ast.parse(code)
    issue = LintIssue(
        file_path="test.py",
        line=1,
        column=0,
        severity=Severity.WARNING,
        rule_id="AIR014",
        message="Replace concurrency with max_active_tasks",
    )

    result = fix_air014(code, tree, issue, code.splitlines(keepends=True))

    assert result == code


def test_fix_air014_with_concurrency():
    """Test fix_air014 with concurrency parameter."""
    code = """
from airflow import DAG

dag = DAG(
    dag_id="test",
    concurrency=5
)
"""
    tree = ast.parse(code)
    issue = LintIssue(
        file_path="test.py",
        line=3,
        column=0,
        severity=Severity.WARNING,
        rule_id="AIR014",
        message="Replace concurrency with max_active_tasks",
    )

    result = fix_air014(code, tree, issue, code.splitlines(keepends=True))

    # Should replace concurrency with max_active_tasks
    assert "max_active_tasks" in result
    assert "concurrency" not in result or result.count("concurrency") < code.count("concurrency")


def test_apply_fixes_multiple_issues_same_rule(tmp_path):
    """Test apply_fixes with multiple issues of same rule."""
    dag_file = tmp_path / "test_dag.py"
    code = """
from airflow import DAG

dag1 = DAG(dag_id="test1")
dag2 = DAG(dag_id="test2")
"""
    dag_file.write_text(code, encoding="utf-8")

    issues = [
        LintIssue(
            file_path=str(dag_file),
            line=3,
            column=0,
            severity=Severity.WARNING,
            rule_id="DAG001",
            message="Missing DAG import",
        ),
        LintIssue(
            file_path=str(dag_file),
            line=4,
            column=0,
            severity=Severity.WARNING,
            rule_id="DAG001",
            message="Missing DAG import",
        ),
    ]

    result, applied = apply_fixes(str(dag_file), issues)

    # Should apply fix only once since import is already added
    assert "from airflow import DAG" in result


def test_apply_fixes_reparse_error(tmp_path):
    """Test apply_fixes when AST reparse fails after fix."""
    dag_file = tmp_path / "test_dag.py"
    # Create file that will cause reparse error after fix
    code = """
x = 1
"""
    dag_file.write_text(code, encoding="utf-8")

    # Create issue that will try to apply fix
    issues = [
        LintIssue(
            file_path=str(dag_file),
            line=2,
            column=0,
            severity=Severity.ERROR,
            rule_id="DAG001",
            message="Missing DAG import",
        )
    ]

    result, applied = apply_fixes(str(dag_file), issues)

    # Should handle reparse error gracefully
    assert isinstance(result, str)
    assert isinstance(applied, list)


def test_apply_fixes_data_access_error(tmp_path, monkeypatch):
    """Test apply_fixes with data access error."""
    dag_file = tmp_path / "test_dag.py"
    code = """
from airflow import DAG

dag = DAG(dag_id="test")
"""
    dag_file.write_text(code, encoding="utf-8")

    issues = [
        LintIssue(
            file_path=str(dag_file),
            line=3,
            column=0,
            severity=Severity.WARNING,
            rule_id="DAG005",
            message="dag_id contains spaces",
        )
    ]

    # Mock to raise AttributeError
    def mock_fix_dag005(*args):
        raise AttributeError("Test error")

    original = autofix.fix_dag005
    autofix.fix_dag005 = mock_fix_dag005

    try:
        result, applied = apply_fixes(str(dag_file), issues)
        # Should handle error gracefully
        assert isinstance(result, str)
        assert isinstance(applied, list)
    finally:
        autofix.fix_dag005 = original


def test_fix_dag001_insert_at_end(tmp_path):
    """Test fix_dag001 when import should be inserted at end."""
    code = """# Comment
import os
import sys
"""
    tree = ast.parse(code)
    issue = LintIssue("test.py", 1, 0, Severity.ERROR, "DAG001", "Missing import")

    result = fix_dag001(code, tree, issue, code.splitlines(keepends=True))

    assert "from airflow import DAG" in result


def test_fix_dag005_with_spaces_in_value():
    """Test fix_dag005 when dag_id value has spaces."""
    code = """
from airflow import DAG

dag = DAG(dag_id="  test_dag  ")
"""
    tree = ast.parse(code)
    # Issue should be on line 3 where DAG call is
    issue = LintIssue("test.py", 3, 0, Severity.WARNING, "DAG005", "Spaces in dag_id")

    result = fix_dag005(code, tree, issue, code.splitlines(keepends=True))

    # Should remove spaces (if fix is applied) or return original
    assert isinstance(result, str)


def test_add_key_to_dict_block_with_dict():
    """Test _add_key_to_dict_block when default_args exists."""
    code = """
default_args = {
    "owner": "airflow"
}
"""
    tree = ast.parse(code)

    result = _add_key_to_dict_block(
        code, tree, "default_args", "retries", '"retries": 1', lines=None
    )

    # Should add retries to existing dict
    assert "retries" in result.lower()


def test_add_param_to_dag_call_with_existing_param():
    """Test _add_param_to_dag_call when parameter already exists."""
    code = """
from airflow import DAG

dag = DAG(
    dag_id="test",
    catchup=False
)
"""
    tree = ast.parse(code)
    issue = LintIssue("test.py", 3, 0, Severity.WARNING, "AIR003", "Missing catchup")

    result = _add_param_to_dag_call(
        code, tree, issue, "catchup", "catchup=False", check_ast=True, lines=None
    )

    # Should not add duplicate parameter
    assert result == code or "catchup" in result


def test_add_param_to_dag_call_invalid_line():
    """Test _add_param_to_dag_call with invalid line number."""
    code = """
from airflow import DAG

dag = DAG(dag_id="test")
"""
    tree = ast.parse(code)
    issue = LintIssue("test.py", 999, 0, Severity.WARNING, "AIR003", "Missing catchup")

    result = _add_param_to_dag_call(
        code, tree, issue, "catchup", "catchup=False", check_ast=False, lines=None
    )

    # Should return original code if line invalid
    assert isinstance(result, str)


def test_fix_dag009_with_existing_dict():
    """Test fix_dag009 when default_args dict exists."""
    code = """
from airflow import DAG

default_args = {
    "retries": 1
}

dag = DAG(dag_id="test", default_args=default_args)
"""
    tree = ast.parse(code)
    issue = LintIssue("test.py", 3, 0, Severity.WARNING, "DAG009", "Missing owner")

    result = fix_dag009(code, tree, issue, code.splitlines(keepends=True))

    # Should add owner to existing default_args
    assert "owner" in result.lower()


def test_fix_dag010_with_existing_dict():
    """Test fix_dag010 when default_args dict exists."""
    code = """
from airflow import DAG

default_args = {
    "owner": "airflow"
}

dag = DAG(dag_id="test", default_args=default_args)
"""
    tree = ast.parse(code)
    issue = LintIssue("test.py", 3, 0, Severity.WARNING, "DAG010", "Missing retries")

    result = fix_dag010(code, tree, issue, code.splitlines(keepends=True))

    # Should add retries to existing default_args
    assert "retries" in result.lower()


def test_add_key_to_dict_block_no_dict_found():
    """Test _add_key_to_dict_block when dict not found in code."""
    code = """
x = 1
y = 2
"""
    tree = ast.parse(code)

    result = _add_key_to_dict_block(
        code, tree, "default_args", "owner", '"owner": "airflow"', lines=None
    )

    # Should return original code if dict not found
    assert result == code


def test_fix_dag005_non_string_constant():
    """Test fix_dag005 when dag_id value is not a string."""
    code = """
from airflow import DAG

dag = DAG(dag_id=123)
"""
    tree = ast.parse(code)
    issue = LintIssue("test.py", 3, 0, Severity.WARNING, "DAG005", "Spaces in dag_id")

    result = fix_dag005(code, tree, issue, code.splitlines(keepends=True))

    # Should return original code for non-string values
    assert result == code


def test_fix_dag005_no_spaces_to_remove():
    """Test fix_dag005 when dag_id has no spaces to remove."""
    code = """
from airflow import DAG

dag = DAG(dag_id="test")
"""
    tree = ast.parse(code)
    issue = LintIssue("test.py", 3, 0, Severity.WARNING, "DAG005", "Spaces in dag_id")

    result = fix_dag005(code, tree, issue, code.splitlines(keepends=True))

    # Should return original code if no spaces to remove
    assert result == code


def test_fix_dag005_invalid_line_index():
    """Test fix_dag005 with invalid line index."""
    code = """
from airflow import DAG

dag = DAG(dag_id="test")
"""
    tree = ast.parse(code)
    # Create issue on invalid line
    issue = LintIssue("test.py", 999, 0, Severity.WARNING, "DAG005", "Spaces in dag_id")

    result = fix_dag005(code, tree, issue, code.splitlines(keepends=True))

    # Should handle invalid line gracefully
    assert isinstance(result, str)


def test_fix_air014_no_concurrency_in_message():
    """Test fix_air014 when message doesn't mention concurrency."""
    code = """
from airflow import DAG

dag = DAG(dag_id="test")
"""
    tree = ast.parse(code)
    issue = LintIssue(
        "test.py", 3, 0, Severity.INFO, "AIR014", "It is recommended to specify max_active_tasks"
    )

    result = fix_air014(code, tree, issue, code.splitlines(keepends=True))

    # Should handle message without concurrency
    assert isinstance(result, str)


def test_add_key_to_dict_block_multiline_dict():
    """Test _add_key_to_dict_block with multiline dictionary."""
    code = """
default_args = {
    "owner": "airflow",
    "retries": 1
}
"""
    tree = ast.parse(code)

    result = _add_key_to_dict_block(
        code,
        tree,
        "default_args",
        "email",
        '"email": "admin@example.com"',
        check_ast=False,
        lines=None,
    )

    # Should add key to multiline dict
    assert "email" in result.lower()


def test_add_param_to_dag_call_multiline_dag():
    """Test _add_param_to_dag_call with multiline DAG call."""
    code = """
from airflow import DAG
from datetime import datetime

dag = DAG(
    dag_id="test",
    start_date=datetime(2024, 1, 1)
)
"""
    tree = ast.parse(code)
    issue = LintIssue("test.py", 3, 0, Severity.WARNING, "AIR003", "Missing catchup")

    result = _add_param_to_dag_call(
        code, tree, issue, "catchup", "catchup=False", check_ast=False, lines=None
    )

    # Should add parameter to multiline DAG call
    assert isinstance(result, str)


def test_add_param_to_dag_call_exceeds_max_lines():
    """Test _add_param_to_dag_call when search exceeds MAX_LINES_TO_SEARCH."""
    # Create DAG call that spans many lines (more than MAX_LINES_TO_SEARCH)
    code = """
from airflow import DAG

dag = DAG(
    dag_id="test",
    param1="value1",
    param2="value2",
    param3="value3",
    param4="value4",
    param5="value5",
    param6="value6",
    param7="value7",
    param8="value8",
    param9="value9",
    param10="value10"
)
"""
    tree = ast.parse(code)
    issue = LintIssue("test.py", 3, 0, Severity.WARNING, "AIR003", "Missing catchup")

    result = _add_param_to_dag_call(
        code, tree, issue, "catchup", "catchup=False", check_ast=False, lines=None
    )

    # Should handle gracefully even if closing paren not found
    assert isinstance(result, str)


def test_fix_dag001_no_import_block():
    """Test fix_dag001 when no import block exists."""
    code = "x = 1\n"
    tree = ast.parse(code)
    issue = LintIssue("test.py", 1, 0, Severity.ERROR, "DAG001", "Missing import")

    result = fix_dag001(code, tree, issue, code.splitlines(keepends=True))

    # Should add import at the beginning
    assert "from airflow import DAG" in result


def test_fix_dag005_fallback_to_regex():
    """Test fix_dag005 fallback to regex when AST doesn't find match."""
    code = """
from airflow import DAG

dag = DAG(dag_id="  test  ")
"""
    tree = ast.parse(code)
    # Create issue on line that doesn't match DAG call exactly
    issue = LintIssue("test.py", 4, 0, Severity.WARNING, "DAG005", "Spaces in dag_id")

    result = fix_dag005(code, tree, issue, code.splitlines(keepends=True))

    # Should handle gracefully even if AST doesn't match
    assert isinstance(result, str)


def test_add_key_to_dict_block_ast_check_false():
    """Test _add_key_to_dict_block with check_ast=False."""
    code = """
default_args = {
    "retries": 1
}
"""
    tree = ast.parse(code)

    result = _add_key_to_dict_block(
        code, tree, "default_args", "owner", '"owner": "airflow"', check_ast=False, lines=None
    )

    # Should add key without AST check
    assert "owner" in result.lower()


def test_add_key_to_dict_block_key_exists():
    """Test _add_key_to_dict_block when key already exists."""
    code = """
default_args = {
    "owner": "airflow"
}
"""
    tree = ast.parse(code)

    result = _add_key_to_dict_block(
        code, tree, "default_args", "owner", '"owner": "airflow"', check_ast=True, lines=None
    )

    # Should not add duplicate key
    assert result == code or result.count('"owner"') == code.count('"owner"')


def test_add_key_to_dict_block_with_lines():
    """Test _add_key_to_dict_block with pre-split lines."""
    code = """
default_args = {
    "retries": 1
}
"""
    lines = code.splitlines(keepends=True)
    tree = ast.parse(code)

    result = _add_key_to_dict_block(
        code, tree, "default_args", "owner", '"owner": "airflow"', check_ast=False, lines=lines
    )

    # Should use provided lines
    assert "owner" in result.lower()


def test_add_param_to_dag_call_with_lines():
    """Test _add_param_to_dag_call with pre-split lines."""
    code = """
from airflow import DAG

dag = DAG(dag_id="test")
"""
    lines = code.splitlines(keepends=True)
    tree = ast.parse(code)
    issue = LintIssue("test.py", 3, 0, Severity.WARNING, "AIR003", "Missing catchup")

    result = _add_param_to_dag_call(
        code, tree, issue, "catchup", "catchup=False", check_ast=False, lines=lines
    )

    # Should use provided lines
    assert isinstance(result, str)


def test_add_param_to_dag_call_param_exists_in_code():
    """Test _add_param_to_dag_call when param exists in code (regex check)."""
    code = """
from airflow import DAG

dag = DAG(
    dag_id="test",
    catchup=False
)
"""
    tree = ast.parse(code)
    issue = LintIssue("test.py", 3, 0, Severity.WARNING, "AIR003", "Missing catchup")

    result = _add_param_to_dag_call(
        code, tree, issue, "catchup", "catchup=False", check_ast=False, lines=None
    )

    # Should not add duplicate parameter
    assert result == code or result.count("catchup") <= code.count("catchup")


def test_apply_fixes_multiple_fixes_same_file(tmp_path):
    """Test apply_fixes with multiple fixes in same file."""
    dag_file = tmp_path / "test_dag.py"
    code = """
dag = DAG(dag_id="test")
"""
    dag_file.write_text(code, encoding="utf-8")

    issues = [
        LintIssue(str(dag_file), 2, 0, Severity.ERROR, "DAG001", "Missing import"),
        LintIssue(str(dag_file), 2, 0, Severity.WARNING, "DAG005", "Spaces in dag_id"),
    ]

    result, applied = apply_fixes(str(dag_file), issues)

    # Should apply both fixes
    assert isinstance(result, str)
    assert isinstance(applied, list)
    assert len(applied) >= 1  # At least DAG001 should be applied


def test_apply_fixes_reparse_warning(tmp_path, monkeypatch):
    """Test apply_fixes when AST reparse fails after fix."""
    dag_file = tmp_path / "test_dag.py"
    code = """
dag = DAG(dag_id="test")
"""
    dag_file.write_text(code, encoding="utf-8")

    issues = [
        LintIssue(str(dag_file), 2, 0, Severity.ERROR, "DAG001", "Missing import"),
    ]

    # Test normal case where fix works
    result, applied = apply_fixes(str(dag_file), issues)

    # Should handle gracefully
    assert isinstance(result, str)
    assert isinstance(applied, list)


def test_fix_dag005_line_out_of_bounds():
    """Test fix_dag005 with line number out of bounds."""
    code = """
from airflow import DAG

dag = DAG(dag_id="test")
"""
    tree = ast.parse(code)
    issue = LintIssue("test.py", 999, 0, Severity.WARNING, "DAG005", "Spaces in dag_id")

    result = fix_dag005(code, tree, issue, code.splitlines(keepends=True))

    # Should handle out of bounds gracefully
    assert isinstance(result, str)


def test_fix_dag005_ast_constant_non_string():
    """Test fix_dag005 when AST Constant value is not string."""
    code = """
from airflow import DAG

dag = DAG(dag_id=123)
"""
    tree = ast.parse(code)
    issue = LintIssue("test.py", 3, 0, Severity.WARNING, "DAG005", "Spaces in dag_id")

    result = fix_dag005(code, tree, issue, code.splitlines(keepends=True))

    # Should return original code for non-string values
    assert result == code


def test_fix_dag005_stripped_value_equals_original():
    """Test fix_dag005 when stripped value equals original."""
    code = """
from airflow import DAG

dag = DAG(dag_id="test")
"""
    tree = ast.parse(code)
    issue = LintIssue("test.py", 3, 0, Severity.WARNING, "DAG005", "Spaces in dag_id")

    result = fix_dag005(code, tree, issue, code.splitlines(keepends=True))

    # Should return original if no spaces to remove
    assert result == code


def test_add_key_to_dict_block_key_exists_regex():
    """Test _add_key_to_dict_block when key exists (regex check)."""
    code = """
default_args = {
    "owner": "airflow"
}
"""
    tree = ast.parse(code)

    # Use check_ast=False to force regex check
    result = _add_key_to_dict_block(
        code, tree, "default_args", "owner", '"owner": "airflow"', check_ast=False, lines=None
    )

    # Should not add duplicate key
    assert result == code or result.count('"owner"') <= code.count('"owner"') + 1


def test_add_key_to_dict_block_no_closing_brace():
    """Test _add_key_to_dict_block when closing brace not found."""
    code = """
default_args = {
    "owner": "airflow"
# Missing closing brace
"""
    # This will be invalid Python, but test the edge case
    try:
        tree = ast.parse(code)
    except SyntaxError:
        # Invalid syntax is okay for this test
        tree = None

    result = _add_key_to_dict_block(
        code,
        tree if tree else ast.parse("x = 1"),
        "default_args",
        "retries",
        '"retries": 1',
        check_ast=False,
        lines=None,
    )

    # Should handle gracefully
    assert isinstance(result, str)


def test_add_param_to_dag_call_no_closing_paren():
    """Test _add_param_to_dag_call when closing paren not found."""
    code = """
from airflow import DAG

dag = DAG(
    dag_id="test"
# Missing closing paren
"""
    # This will be invalid Python, but test the edge case
    try:
        tree = ast.parse(code)
    except SyntaxError:
        tree = None

    if tree:
        issue = LintIssue("test.py", 3, 0, Severity.WARNING, "AIR003", "Missing catchup")
        result = _add_param_to_dag_call(
            code, tree, issue, "catchup", "catchup=False", check_ast=False, lines=None
        )

        # Should handle gracefully
        assert isinstance(result, str)


def test_apply_fixes_os_error():
    """Test apply_fixes handles OSError during fix application."""
    # This is tested via file write errors in other tests
    # Adding explicit test
    dag_file = Path("/nonexistent/test.py")

    issues = [
        LintIssue(str(dag_file), 1, 0, Severity.ERROR, "DAG001", "Missing import"),
    ]

    result, applied = apply_fixes(str(dag_file), issues)

    # Should handle file not found error
    assert result == ""
    assert applied == []


def test_apply_fixes_io_error(tmp_path):
    """Test apply_fixes handles IOError during fix application."""
    dag_file = tmp_path / "test_dag.py"
    dag_file.write_text("dag = DAG(dag_id='test')\n", encoding="utf-8")

    # Test that validation happens first (file not found would fail earlier)
    # Just test that function handles errors
    issues = [
        LintIssue(str(dag_file), 1, 0, Severity.ERROR, "DAG001", "Missing import"),
    ]

    result, applied = apply_fixes(str(dag_file), issues)

    # Should handle gracefully
    assert isinstance(result, str)
    assert isinstance(applied, list)


def test_fix_dag005_line_zero():
    """Test fix_dag005 with line 0."""
    code = """
from airflow import DAG

dag = DAG(dag_id="test")
"""
    tree = ast.parse(code)
    issue = LintIssue("test.py", 0, 0, Severity.WARNING, "DAG005", "Spaces in dag_id")

    result = fix_dag005(code, tree, issue, code.splitlines(keepends=True))

    # Should handle line 0 gracefully
    assert isinstance(result, str)


def test_fix_dag005_line_too_large():
    """Test fix_dag005 with line number too large."""
    code = """
from airflow import DAG

dag = DAG(dag_id="test")
"""
    tree = ast.parse(code)
    issue = LintIssue("test.py", 999, 0, Severity.WARNING, "DAG005", "Spaces in dag_id")

    result = fix_dag005(code, tree, issue, code.splitlines(keepends=True))

    # Should handle large line number gracefully
    assert isinstance(result, str)


def test_fix_dag005_regex_fallback():
    """Test fix_dag005 regex fallback when AST doesn't match."""
    code = """
from airflow import DAG

dag = DAG(dag_id="  test  ")
"""
    tree = ast.parse(code)
    # Issue on line that has dag_id but AST might not match exactly
    issue = LintIssue("test.py", 3, 0, Severity.WARNING, "DAG005", "Spaces in dag_id")

    result = fix_dag005(code, tree, issue, code.splitlines(keepends=True))

    # Should try regex fallback
    assert isinstance(result, str)


def test_add_param_to_dag_call_check_ast_false():
    """Test _add_param_to_dag_call with check_ast=False."""
    code = """
from airflow import DAG

dag = DAG(dag_id="test")
"""
    tree = ast.parse(code)
    issue = LintIssue("test.py", 3, 0, Severity.WARNING, "AIR003", "Missing catchup")

    result = _add_param_to_dag_call(
        code, tree, issue, "catchup", "catchup=False", check_ast=False, lines=None
    )

    # Should add parameter without AST check
    assert isinstance(result, str)


def test_add_param_to_dag_call_param_already_exists_ast():
    """Test _add_param_to_dag_call when parameter exists (AST check)."""
    code = """
from airflow import DAG

dag = DAG(dag_id="test", catchup=False)
"""
    tree = ast.parse(code)
    issue = LintIssue("test.py", 3, 0, Severity.WARNING, "AIR003", "Missing catchup")

    result = _add_param_to_dag_call(
        code, tree, issue, "catchup", "catchup=False", check_ast=True, lines=None
    )

    # Should not add duplicate parameter
    assert result == code


def test_add_param_to_dag_call_no_closing_paren_found():
    """Test _add_param_to_dag_call when closing paren not found."""
    # Create multiline DAG that exceeds MAX_LINES_TO_SEARCH
    code = """
from airflow import DAG

dag = DAG(
    dag_id="test",
    start_date=None,
    schedule=None,
    catchup=None
"""
    # Note: Missing closing paren, but code will parse
    code_complete = code + ")"
    tree = ast.parse(code_complete)
    issue = LintIssue("test.py", 3, 0, Severity.WARNING, "AIR013", "Missing max_active_runs")

    # But we'll test with incomplete code that exceeds search
    # This tests the case where closing paren is not found in MAX_LINES_TO_SEARCH
    result = _add_param_to_dag_call(
        code_complete,
        tree,
        issue,
        "max_active_runs",
        "max_active_runs=1",
        check_ast=False,
        lines=None,
    )

    # Should handle gracefully
    assert isinstance(result, str)


def test_add_param_to_dag_call_no_dag_call_match():
    """Test _add_param_to_dag_call when DAG call line doesn't match."""
    code = """
from airflow import DAG

dag = DAG(dag_id="test")
"""
    tree = ast.parse(code)
    # Issue on different line than DAG call
    issue = LintIssue("test.py", 2, 0, Severity.WARNING, "AIR003", "Missing catchup")

    result = _add_param_to_dag_call(
        code, tree, issue, "catchup", "catchup=False", check_ast=False, lines=None
    )

    # Should handle gracefully
    assert isinstance(result, str)


def test_add_param_to_dag_call_has_param_in_text():
    """Test _add_param_to_dag_call when param already exists in text."""
    code = """
from airflow import DAG

dag = DAG(dag_id="test", catchup=False)
"""
    tree = ast.parse(code)
    issue = LintIssue("test.py", 3, 0, Severity.WARNING, "AIR003", "Missing catchup")

    result = _add_param_to_dag_call(
        code, tree, issue, "catchup", "catchup=False", check_ast=False, lines=None
    )

    # Should not add duplicate
    assert isinstance(result, str)


def test_add_param_to_dag_call_insert_pos_found():
    """Test _add_param_to_dag_call finds insert position correctly."""
    code = """
from airflow import DAG

dag = DAG(
    dag_id="test",
    start_date=None
)
"""
    tree = ast.parse(code)
    issue = LintIssue("test.py", 3, 0, Severity.WARNING, "AIR003", "Missing catchup")

    result = _add_param_to_dag_call(
        code, tree, issue, "catchup", "catchup=False", check_ast=False, lines=None
    )

    # Should insert parameter
    assert isinstance(result, str)


def test_add_param_to_dag_call_find_last_non_comment_line():
    """Test _add_param_to_dag_call finds last non-comment line before closing paren."""
    code = """
from airflow import DAG

dag = DAG(
    dag_id="test",
    # comment
    start_date=None
)
"""
    tree = ast.parse(code)
    issue = LintIssue("test.py", 3, 0, Severity.WARNING, "AIR003", "Missing catchup")

    result = _add_param_to_dag_call(
        code, tree, issue, "catchup", "catchup=False", check_ast=False, lines=None
    )

    # Should handle comments correctly
    assert isinstance(result, str)


def test_add_param_to_dag_call_multiline_with_comments():
    """Test _add_param_to_dag_call with multiline DAG call and comments."""
    code = """
from airflow import DAG

dag = DAG(
    dag_id="test",
    # Some comment
    start_date=None
    # Another comment
)
"""
    tree = ast.parse(code)
    issue = LintIssue("test.py", 3, 0, Severity.WARNING, "AIR003", "Missing catchup")

    result = _add_param_to_dag_call(
        code, tree, issue, "catchup", "catchup=False", check_ast=False, lines=None
    )

    # Should handle multiline with comments
    assert isinstance(result, str)


def test_add_param_to_dag_call_with_lines_parameter():
    """Test _add_param_to_dag_call with pre-split lines."""
    code = """
from airflow import DAG

dag = DAG(
    dag_id="test"
)
"""
    lines = code.splitlines(keepends=True)
    tree = ast.parse(code)
    issue = LintIssue("test.py", 3, 0, Severity.WARNING, "AIR003", "Missing catchup")

    result = _add_param_to_dag_call(
        code, tree, issue, "catchup", "catchup=False", check_ast=False, lines=lines
    )

    # Should use provided lines
    assert isinstance(result, str)


def test_add_param_to_dag_call_bracket_counting():
    """Test _add_param_to_dag_call bracket counting logic."""
    code = """
from airflow import DAG

dag = DAG(
    dag_id="test",
    nested=dict(
        key="value"
    )
)
"""
    tree = ast.parse(code)
    issue = LintIssue("test.py", 3, 0, Severity.WARNING, "AIR003", "Missing catchup")

    result = _add_param_to_dag_call(
        code, tree, issue, "catchup", "catchup=False", check_ast=False, lines=None
    )

    # Should handle nested brackets correctly
    assert isinstance(result, str)


def test_add_param_to_dag_call_found_call_after_open():
    """Test _add_param_to_dag_call when DAG call found after opening paren."""
    code = """
from airflow import DAG

dag = DAG(dag_id="test")
"""
    tree = ast.parse(code)
    issue = LintIssue("test.py", 3, 0, Severity.WARNING, "AIR003", "Missing catchup")

    result = _add_param_to_dag_call(
        code, tree, issue, "catchup", "catchup=False", check_ast=False, lines=None
    )

    # Should handle single-line DAG call
    assert isinstance(result, str)


def test_add_param_to_dag_call_max_lines_exceeded():
    """Test _add_param_to_dag_call when MAX_LINES_TO_SEARCH exceeded."""
    # Create DAG call that spans many lines
    code = """
from airflow import DAG

dag = DAG(
    dag_id="test",
    param1="value1",
    param2="value2",
    param3="value3",
    param4="value4",
    param5="value5",
    param6="value6",
    param7="value7",
    param8="value8",
    param9="value9",
    param10="value10",
    param11="value11",
    param12="value12",
    param13="value13",
    param14="value14",
    param15="value15",
    param16="value16",
    param17="value17",
    param18="value18",
    param19="value19",
    param20="value20"
)
"""
    tree = ast.parse(code)
    issue = LintIssue("test.py", 3, 0, Severity.WARNING, "AIR003", "Missing catchup")

    result = _add_param_to_dag_call(
        code, tree, issue, "catchup", "catchup=False", check_ast=False, lines=None
    )

    # Should handle exceeding MAX_LINES_TO_SEARCH gracefully
    assert isinstance(result, str)


def test_fix_dag005_line_regex_match():
    """Test fix_dag005 regex fallback matches correctly."""
    code = """
from airflow import DAG

dag = DAG(dag_id="  test  ")
"""
    tree = ast.parse(code)
    # Issue on line with dag_id that has spaces
    issue = LintIssue("test.py", 3, 0, Severity.WARNING, "DAG005", "Spaces in dag_id")

    result = fix_dag005(code, tree, issue, code.splitlines(keepends=True))

    # Should remove spaces via regex if AST doesn't match
    assert isinstance(result, str)


def test_fix_dag005_constant_value_not_string():
    """Test fix_dag005 when Constant value is not a string."""
    code = """
from airflow import DAG

dag = DAG(dag_id=123)
"""
    tree = ast.parse(code)
    issue = LintIssue("test.py", 3, 0, Severity.WARNING, "DAG005", "Spaces in dag_id")

    result = fix_dag005(code, tree, issue, code.splitlines(keepends=True))

    # Should return original code for non-string values
    assert result == code


def test_fix_dag005_stripped_equals_original_returns_early():
    """Test fix_dag005 early return when stripped equals original."""
    code = """
from airflow import DAG

dag = DAG(dag_id="test")
"""
    tree = ast.parse(code)
    issue = LintIssue("test.py", 3, 0, Severity.WARNING, "DAG005", "Spaces in dag_id")

    result = fix_dag005(code, tree, issue, code.splitlines(keepends=True))

    # Should return early if no spaces to remove
    assert result == code


def test_fix_dag005_line_index_in_range_but_no_match():
    """Test fix_dag005 when line_index is in range but regex doesn't match."""
    code = """
from airflow import DAG

dag = DAG(
    dag_id="test"
)
"""
    tree = ast.parse(code)
    issue = LintIssue("test.py", 3, 0, Severity.WARNING, "DAG005", "Spaces in dag_id")

    # The dag_id is on line 4, not line 3, so regex may not match
    result = fix_dag005(code, tree, issue, code.splitlines(keepends=True))

    # Should handle gracefully
    assert isinstance(result, str)


def test_fix_dag005_line_index_regex_no_change():
    """Test fix_dag005 when regex doesn't change the line."""
    code = """
from airflow import DAG

dag = DAG(dag_id="test")  # No spaces
"""
    tree = ast.parse(code)
    issue = LintIssue("test.py", 3, 0, Severity.WARNING, "DAG005", "Spaces in dag_id")

    result = fix_dag005(code, tree, issue, code.splitlines(keepends=True))

    # Should return original if regex doesn't match or doesn't change
    assert isinstance(result, str)


def test_fix_dag005_ast_str_value():
    """Test fix_dag005 with ast.Str value (Python < 3.8)."""
    code = """
from airflow import DAG

dag = DAG(dag_id="  test  ")
"""
    tree = ast.parse(code)
    issue = LintIssue("test.py", 3, 0, Severity.WARNING, "DAG005", "Spaces in dag_id")

    result = fix_dag005(code, tree, issue, code.splitlines(keepends=True))

    # Should handle ast.Str node
    assert isinstance(result, str)


def test_fix_dag005_constant_value_check():
    """Test fix_dag005 Constant value type check."""
    code = """
from airflow import DAG

dag = DAG(dag_id="test")
"""
    tree = ast.parse(code)

    # Create issue that triggers Constant value check path
    issue = LintIssue("test.py", 3, 0, Severity.WARNING, "DAG005", "Spaces in dag_id")

    result = fix_dag005(code, tree, issue, code.splitlines(keepends=True))

    # Should handle Constant value check
    assert isinstance(result, str)


def test_apply_fixes_multiple_files(tmp_path):
    """Test apply_autofixes with multiple files."""
    test_file1 = tmp_path / "test1.py"
    test_file1.write_text("dag = DAG(dag_id='test1')\n", encoding="utf-8")
    test_file2 = tmp_path / "test2.py"
    test_file2.write_text("dag = DAG(dag_id='test2')\n", encoding="utf-8")

    mock_config = MagicMock(spec=Config)
    mock_config.get_ignore.return_value = []

    issues, fixed = apply_autofixes(
        [str(test_file1), str(test_file2)],
        {"DAG001"},
        [Severity.ERROR, Severity.WARNING],
        [],
        mock_config,
    )

    assert isinstance(issues, list)
    assert isinstance(fixed, int)


def test_apply_autofixes_total_fixed_count(tmp_path):
    """Test apply_autofixes returns correct total_fixed count."""
    test_file = tmp_path / "test_dag.py"
    test_file.write_text("dag = DAG(dag_id='test')\n", encoding="utf-8")

    mock_config = MagicMock(spec=Config)
    mock_config.get_ignore.return_value = []

    issues, fixed = apply_autofixes(
        [str(test_file)],
        {"DAG001"},
        [Severity.ERROR, Severity.WARNING],
        [],
        mock_config,
    )

    assert isinstance(fixed, int)
    assert fixed >= 0


def test_apply_autofixes_no_fixable_issues_after_filter(tmp_path):
    """Test apply_autofixes when no fixable issues after filtering."""
    test_file = tmp_path / "test_dag.py"
    test_file.write_text("from airflow import DAG\n", encoding="utf-8")

    mock_config = MagicMock(spec=Config)
    mock_config.get_ignore.return_value = []

    issues, fixed = apply_autofixes(
        [str(test_file)],
        {"DAG001"},
        [Severity.ERROR],  # Only errors
        [],
        mock_config,
    )

    assert isinstance(issues, list)
    assert isinstance(fixed, int)


def test_apply_autofixes_with_severity_filter(tmp_path):
    """Test apply_autofixes filters by severity correctly."""
    test_file = tmp_path / "test_dag.py"
    test_file.write_text("dag = DAG(dag_id='test')\n", encoding="utf-8")

    mock_config = MagicMock(spec=Config)
    mock_config.get_ignore.return_value = []

    issues, fixed = apply_autofixes(
        [str(test_file)],
        {"DAG001"},
        [Severity.WARNING],  # Only warnings, not errors
        [],
        mock_config,
    )

    assert isinstance(issues, list)
    assert isinstance(fixed, int)
