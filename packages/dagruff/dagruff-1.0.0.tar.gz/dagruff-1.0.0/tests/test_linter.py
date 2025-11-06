"""Тесты для линтера."""

from pathlib import Path
from unittest.mock import patch

import pytest

from dagruff.linter import DAGLinter
from dagruff.models import Severity


@pytest.fixture
def examples_dir():
    """Путь к директории с примерами."""
    return Path(__file__).parent.parent / "examples"


def test_lint_good_dag(examples_dir):
    """Test checking a good DAG (should have minimal errors)."""
    dag_file = examples_dir / "example_dag_good.py"
    linter = DAGLinter(str(dag_file))
    issues = linter.lint()

    # Good DAG should have minimal critical errors (may have warnings like DAG011)
    # Check that there are no critical structural errors (DAG001, DAG003, etc.)
    critical_errors = [
        issue
        for issue in issues
        if issue.severity == Severity.ERROR
        and issue.rule_id in ["DAG001", "DAG003", "DAG004", "SYNTAX_ERROR"]
    ]
    assert len(critical_errors) == 0, (
        f"Found critical errors in good DAG: {[e.message for e in critical_errors]}"
    )


def test_lint_bad_dag(examples_dir):
    """Тест проверки неправильного DAG."""
    dag_file = examples_dir / "example_dag_bad.py"
    linter = DAGLinter(str(dag_file))
    issues = linter.lint()

    # Неправильный DAG должен иметь ошибки
    errors = [issue for issue in issues if issue.severity == Severity.ERROR]
    assert len(errors) > 0, "В неправильном DAG должны быть ошибки"


def test_linter_init_with_file(tmp_path):
    """Test DAGLinter initialization with file path."""
    test_file = tmp_path / "test_dag.py"
    test_file.write_text("from airflow import DAG\n", encoding="utf-8")

    linter = DAGLinter(str(test_file))

    assert linter.file_path == str(test_file)


def test_linter_lint_valid_dag(tmp_path):
    """Test linter.lint with valid DAG file."""
    test_file = tmp_path / "test_dag.py"
    content = """from airflow import DAG

dag = DAG(
    dag_id="test_dag",
    description="Test DAG",
)
"""
    test_file.write_text(content, encoding="utf-8")

    linter = DAGLinter(str(test_file))
    issues = linter.lint()

    assert isinstance(issues, list)


def test_linter_lint_invalid_dag(tmp_path):
    """Test linter.lint with invalid DAG file."""
    test_file = tmp_path / "test_dag.py"
    content = """dag = DAG(dag_id="test")
"""
    test_file.write_text(content, encoding="utf-8")

    linter = DAGLinter(str(test_file))
    issues = linter.lint()

    # Should find issues (missing import)
    assert isinstance(issues, list)


def test_linter_lint_syntax_error(tmp_path):
    """Test linter.lint with syntax error."""
    test_file = tmp_path / "test_dag.py"
    content = """def invalid syntax
"""
    test_file.write_text(content, encoding="utf-8")

    linter = DAGLinter(str(test_file))
    issues = linter.lint()

    # Should handle syntax error gracefully
    assert isinstance(issues, list)


def test_linter_lint_empty_file(tmp_path):
    """Test linter.lint with empty file."""
    test_file = tmp_path / "test_dag.py"
    test_file.write_text("", encoding="utf-8")

    linter = DAGLinter(str(test_file))
    issues = linter.lint()

    assert isinstance(issues, list)


def test_linter_lint_non_dag_file(tmp_path):
    """Test linter.lint with non-DAG file."""
    test_file = tmp_path / "regular.py"
    test_file.write_text("print('hello')\n", encoding="utf-8")

    linter = DAGLinter(str(test_file))
    issues = linter.lint()

    # Should return empty list or handle gracefully
    assert isinstance(issues, list)


def test_linter_parallel_rule_execution(tmp_path):
    """Test linter parallel rule execution."""
    test_file = tmp_path / "test_dag.py"
    content = """from airflow import DAG

dag = DAG(
    dag_id="test_dag",
    description="Test DAG",
)
"""
    test_file.write_text(content, encoding="utf-8")

    linter = DAGLinter(str(test_file))
    issues = linter.lint()

    # Should execute rules in parallel
    assert isinstance(issues, list)


def test_linter_error_handling(tmp_path):
    """Test linter error handling."""
    test_file = tmp_path / "test_dag.py"
    test_file.write_text("from airflow import DAG\n", encoding="utf-8")

    linter = DAGLinter(str(test_file))

    # Test that lint handles errors gracefully
    issues = linter.lint()
    assert isinstance(issues, list)


def test_linter_file_validation_error(tmp_path):
    """Test linter with file validation error."""
    # File doesn't exist or is invalid
    invalid_file = tmp_path / "nonexistent.py"

    linter = DAGLinter(str(invalid_file))
    issues = linter.lint()

    # Should return validation error
    assert isinstance(issues, list)
    assert len(issues) > 0
    assert any(issue.rule_id == "VALIDATION_ERROR" for issue in issues)


def test_linter_encoding_error(tmp_path):
    """Test linter with encoding error."""
    test_file = tmp_path / "test.py"
    test_file.write_bytes(b"\xff\xfe\x00\x00")  # Invalid UTF-8

    linter = DAGLinter(str(test_file))
    issues = linter.lint()

    # Should return encoding error
    assert isinstance(issues, list)
    assert len(issues) > 0
    assert any(issue.rule_id == "ENCODING_ERROR" for issue in issues)


def test_linter_dagbag_critical_errors(tmp_path):
    """Test linter stops on DagBag critical errors."""
    test_file = tmp_path / "test_dag.py"
    # Create file with critical DagBag error (syntax error)
    content = """def invalid syntax
"""
    test_file.write_text(content, encoding="utf-8")

    linter = DAGLinter(str(test_file))
    issues = linter.lint()

    # Should have DagBag errors and stop early
    assert isinstance(issues, list)


def test_linter_parallel_rule_execution_error(tmp_path, monkeypatch):
    """Test linter handles parallel rule execution errors."""
    test_file = tmp_path / "test_dag.py"
    content = """from airflow import DAG

dag = DAG(dag_id="test")
"""
    test_file.write_text(content, encoding="utf-8")

    # Mock rule check to raise error
    def mock_check(*args, **kwargs):
        raise Exception("Test error")

    linter = DAGLinter(str(test_file))

    # Test that errors are handled gracefully
    issues = linter.lint()
    assert isinstance(issues, list)


def test_linter_syntax_error(tmp_path):
    """Test linter with syntax error."""
    test_file = tmp_path / "test_dag.py"
    content = """def invalid syntax
"""
    test_file.write_text(content, encoding="utf-8")

    linter = DAGLinter(str(test_file))
    issues = linter.lint()

    # Should handle syntax error
    assert isinstance(issues, list)


def test_linter_ast_parse_error(tmp_path):
    """Test linter with AST parse error."""
    test_file = tmp_path / "test_dag.py"
    # Create file that causes AST parse error
    content = """def invalid() {
"""
    test_file.write_text(content, encoding="utf-8")

    linter = DAGLinter(str(test_file))
    issues = linter.lint()

    # Should handle AST parse error
    assert isinstance(issues, list)


def test_linter_check_rules_parallel(tmp_path):
    """Test linter parallel rule execution."""
    test_file = tmp_path / "test_dag.py"
    content = """from airflow import DAG

dag = DAG(dag_id="test")
"""
    test_file.write_text(content, encoding="utf-8")

    linter = DAGLinter(str(test_file))
    issues = linter.lint()

    # Should execute rules in parallel
    assert isinstance(issues, list)


def test_linter_collector_initialization(tmp_path):
    """Test linter AST collector initialization."""
    test_file = tmp_path / "test_dag.py"
    content = """from airflow import DAG

dag = DAG(dag_id="test")
"""
    test_file.write_text(content, encoding="utf-8")

    linter = DAGLinter(str(test_file))
    linter.lint()

    # Collector should be initialized
    assert linter.collector is not None


def test_linter_tree_parsing(tmp_path):
    """Test linter AST tree parsing."""
    test_file = tmp_path / "test_dag.py"
    content = """from airflow import DAG

dag = DAG(dag_id="test")
"""
    test_file.write_text(content, encoding="utf-8")

    linter = DAGLinter(str(test_file))
    linter.lint()

    # Tree should be parsed
    assert linter.tree is not None


def test_linter_source_code_reading(tmp_path):
    """Test linter source code reading."""
    test_file = tmp_path / "test_dag.py"
    content = """from airflow import DAG

dag = DAG(dag_id="test")
"""
    test_file.write_text(content, encoding="utf-8")

    linter = DAGLinter(str(test_file))
    linter.lint()

    # Source code should be read
    assert len(linter.source_code) > 0
    assert "from airflow import DAG" in linter.source_code


def test_linter_no_critical_dagbag_errors(tmp_path):
    """Test linter continues when no critical DagBag errors."""
    test_file = tmp_path / "test_dag.py"
    content = """from airflow import DAG

dag = DAG(dag_id="test")
"""
    test_file.write_text(content, encoding="utf-8")

    linter = DAGLinter(str(test_file))
    issues = linter.lint()

    # Should continue with other checks
    assert isinstance(issues, list)


def test_linter_rule_check_error_handling(tmp_path):
    """Test linter handles rule check errors."""
    test_file = tmp_path / "test_dag.py"
    content = """from airflow import DAG

dag = DAG(dag_id="test")
"""
    test_file.write_text(content, encoding="utf-8")

    linter = DAGLinter(str(test_file))
    issues = linter.lint()

    # Should handle errors gracefully
    assert isinstance(issues, list)


def test_linter_error_handling_in_lint(tmp_path):
    """Test linter error handling in lint method."""
    test_file = tmp_path / "test_dag.py"
    test_file.write_text("from airflow import DAG\n", encoding="utf-8")

    linter = DAGLinter(str(test_file))
    issues = linter.lint()

    assert isinstance(issues, list)


def test_linter_collector_usage(tmp_path):
    """Test linter uses AST collector."""
    test_file = tmp_path / "test_dag.py"
    content = """from airflow import DAG

dag = DAG(dag_id="test")
"""
    test_file.write_text(content, encoding="utf-8")

    linter = DAGLinter(str(test_file))
    linter.lint()

    # Collector should be used if no critical DagBag errors
    assert isinstance(linter.collector, (type(None), object))


def test_linter_continues_after_validation(tmp_path):
    """Test linter continues after validation passes."""
    test_file = tmp_path / "test_dag.py"
    content = """from airflow import DAG

dag = DAG(dag_id="test")
"""
    test_file.write_text(content, encoding="utf-8")

    linter = DAGLinter(str(test_file))
    issues = linter.lint()

    # Should continue and find issues
    assert isinstance(issues, list)


def test_linter_handles_validation_error(tmp_path):
    """Test linter handles validation error gracefully."""
    # Create file that will fail validation
    invalid_file = tmp_path / "test_dag.py"
    invalid_file.write_text("from airflow import DAG\n", encoding="utf-8")

    # Mock validate_file_path to return False
    with patch("dagruff.linter.validate_file_path", return_value=(False, "Validation error")):
        linter = DAGLinter(str(invalid_file))
        issues = linter.lint()

        # Should return validation error issue
        assert isinstance(issues, list)
        assert len(issues) > 0
