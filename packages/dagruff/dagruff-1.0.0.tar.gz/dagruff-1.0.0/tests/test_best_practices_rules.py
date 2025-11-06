"""Tests for dagruff.rules.best_practices_rules module."""

import ast

from dagruff.models import Severity
from dagruff.rules.ast_collector import ASTCollector
from dagruff.rules.best_practices_rules import check_all_best_practices_rules


def test_bp003_execution_timeout_missing():
    """Test BP003: Check for missing execution_timeout."""
    code = """
from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime

dag = DAG(dag_id="test", start_date=datetime(2024, 1, 1))

task = BashOperator(
    task_id="test_task",
    bash_command="echo hello"
)
"""
    tree = ast.parse(code)
    collector = ASTCollector(tree)
    collector.collect()

    issues = check_all_best_practices_rules(collector, "test.py")

    bp003_issues = [i for i in issues if i.rule_id == "BP003"]
    assert len(bp003_issues) > 0
    assert bp003_issues[0].severity == Severity.INFO


def test_bp003_execution_timeout_present():
    """Test BP003: execution_timeout is present."""
    code = """
from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime

dag = DAG(dag_id="test", start_date=datetime(2024, 1, 1))

task = BashOperator(
    task_id="test_task",
    bash_command="echo hello",
    execution_timeout=300
)
"""
    tree = ast.parse(code)
    collector = ASTCollector(tree)
    collector.collect()

    issues = check_all_best_practices_rules(collector, "test.py")

    bp003_issues = [i for i in issues if i.rule_id == "BP003"]
    assert len(bp003_issues) == 0


def test_bp005_docstring_missing():
    """Test BP005: Check for missing task docstring."""
    code = """
from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime

dag = DAG(dag_id="test", start_date=datetime(2024, 1, 1))

task = BashOperator(
    task_id="test_task",
    bash_command="echo hello"
)
"""
    tree = ast.parse(code)
    collector = ASTCollector(tree)
    collector.collect()

    issues = check_all_best_practices_rules(collector, "test.py")

    bp005_issues = [i for i in issues if i.rule_id == "BP005"]
    assert len(bp005_issues) > 0
    assert bp005_issues[0].severity == Severity.INFO


def test_bp005_docstring_present():
    """Test BP005: docstring is present."""
    code = """
from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime

dag = DAG(dag_id="test", start_date=datetime(2024, 1, 1))

task = BashOperator(
    task_id="test_task",
    bash_command="echo hello",
    doc_md="Task documentation"
)
"""
    tree = ast.parse(code)
    collector = ASTCollector(tree)
    collector.collect()

    issues = check_all_best_practices_rules(collector, "test.py")

    bp005_issues = [i for i in issues if i.rule_id == "BP005"]
    assert len(bp005_issues) == 0


def test_bp006_dagrun_timeout_missing():
    """Test BP006: Check for missing dagrun_timeout."""
    code = """
from airflow import DAG
from datetime import datetime

dag = DAG(dag_id="test", start_date=datetime(2024, 1, 1))
"""
    tree = ast.parse(code)
    collector = ASTCollector(tree)
    collector.collect()

    issues = check_all_best_practices_rules(collector, "test.py")

    bp006_issues = [i for i in issues if i.rule_id == "BP006"]
    assert len(bp006_issues) > 0
    assert bp006_issues[0].severity == Severity.INFO


def test_bp006_dagrun_timeout_present():
    """Test BP006: dagrun_timeout is present."""
    code = """
from airflow import DAG
from datetime import datetime, timedelta

dag = DAG(
    dag_id="test",
    start_date=datetime(2024, 1, 1),
    dagrun_timeout=timedelta(hours=2)
)
"""
    tree = ast.parse(code)
    collector = ASTCollector(tree)
    collector.collect()

    issues = check_all_best_practices_rules(collector, "test.py")

    bp006_issues = [i for i in issues if i.rule_id == "BP006"]
    assert len(bp006_issues) == 0


def test_bp002_datetime_today():
    """Test BP002: Check for datetime.today() in top-level code."""
    code = """
from airflow import DAG
from datetime import datetime

today = datetime.today()
dag = DAG(dag_id="test", start_date=datetime(2024, 1, 1))
"""
    tree = ast.parse(code)
    collector = ASTCollector(tree)
    collector.collect()

    issues = check_all_best_practices_rules(collector, "test.py")

    bp002_issues = [i for i in issues if i.rule_id == "BP002"]
    assert len(bp002_issues) > 0
    assert bp002_issues[0].severity == Severity.WARNING


def test_bp004_mixed_dependencies():
    """Test BP004: Check for mixing dependency methods."""
    code = """
from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime

dag = DAG(dag_id="test", start_date=datetime(2024, 1, 1))

task1 = BashOperator(task_id="task1", bash_command="echo 1", dag=dag)
task2 = BashOperator(task_id="task2", bash_command="echo 2", dag=dag)

task1 >> task2
task2.set_upstream(task1)
"""
    tree = ast.parse(code)
    collector = ASTCollector(tree)
    collector.collect()

    issues = check_all_best_practices_rules(collector, "test.py")

    bp004_issues = [i for i in issues if i.rule_id == "BP004"]
    assert len(bp004_issues) > 0
    assert bp004_issues[0].severity == Severity.WARNING
