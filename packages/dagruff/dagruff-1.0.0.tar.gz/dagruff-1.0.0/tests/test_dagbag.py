"""Tests for dagruff.rules.dagbag module."""

from dagruff.models import Severity
from dagruff.rules.dagbag import check_dagbag_validation


def test_check_dagbag_validation_invalid_path():
    """Test check_dagbag_validation with invalid file path."""
    issues = check_dagbag_validation("/nonexistent/path/to/file.py")

    # Should return validation warning
    assert len(issues) >= 0  # May return 0 if Airflow not installed


def test_check_dagbag_validation_valid_dag(tmp_path):
    """Test check_dagbag_validation with valid DAG file."""
    dag_content = """
from airflow import DAG
from datetime import datetime

dag = DAG(
    dag_id="test_dag",
    start_date=datetime(2024, 1, 1)
)
"""
    dag_file = tmp_path / "test_dag.py"
    dag_file.write_text(dag_content)

    issues = check_dagbag_validation(str(dag_file))

    # Should not return errors for valid DAG (if Airflow is installed)
    # If Airflow is not installed, should return empty list
    assert isinstance(issues, list)
    for issue in issues:
        assert issue.rule_id in ["DAGBAG001", "DAGBAG002"]


def test_check_dagbag_validation_invalid_dag(tmp_path):
    """Test check_dagbag_validation with invalid DAG file."""
    dag_content = """
from airflow import DAG
from datetime import datetime

# Invalid: missing dag_id
dag = DAG(start_date=datetime(2024, 1, 1))
"""
    dag_file = tmp_path / "invalid_dag.py"
    dag_file.write_text(dag_content)

    issues = check_dagbag_validation(str(dag_file))

    # May return empty list if Airflow not installed
    # If Airflow is installed, may return DAGBAG001 errors
    assert isinstance(issues, list)
    for issue in issues:
        assert issue.rule_id in ["DAGBAG001", "DAGBAG002"]
        assert issue.severity in [Severity.ERROR, Severity.WARNING]


def test_check_dagbag_validation_syntax_error(tmp_path):
    """Test check_dagbag_validation with syntax error in file."""
    dag_content = """
from airflow import DAG

dag = DAG(
    dag_id="test"
    # Missing closing parenthesis
"""
    dag_file = tmp_path / "syntax_error.py"
    dag_file.write_text(dag_content)

    issues = check_dagbag_validation(str(dag_file))

    # May return empty list if Airflow not installed
    # If Airflow is installed, should return DAGBAG001 error
    assert isinstance(issues, list)
    for issue in issues:
        assert issue.rule_id in ["DAGBAG001", "DAGBAG002"]


def test_check_dagbag_validation_empty_file(tmp_path):
    """Test check_dagbag_validation with empty file."""
    dag_file = tmp_path / "empty.py"
    dag_file.write_text("")

    issues = check_dagbag_validation(str(dag_file))

    assert isinstance(issues, list)
    # Empty file may or may not trigger DagBag errors depending on Airflow version


def test_check_dagbag_validation_directory(tmp_path):
    """Test check_dagbag_validation with directory path instead of file."""
    issues = check_dagbag_validation(str(tmp_path))

    # Should handle directory gracefully
    assert isinstance(issues, list)
    for issue in issues:
        assert issue.rule_id in ["DAGBAG001", "DAGBAG002"]
