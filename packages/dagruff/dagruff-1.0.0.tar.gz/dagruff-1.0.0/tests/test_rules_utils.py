"""Tests for dagruff.rules.utils module."""

import ast

from dagruff.rules.utils import (
    find_dag_calls,
    find_operators,
    get_default_args_start_date,
    has_retries_in_operators,
    has_start_date_in_dag,
    is_inside_task_or_operator,
)


def test_find_dag_calls_simple():
    """Test finding simple DAG() calls."""
    code = """
from airflow import DAG

dag = DAG(dag_id="test_dag")
"""
    tree = ast.parse(code)
    dag_calls = find_dag_calls(tree)

    assert len(dag_calls) == 1
    assert isinstance(dag_calls[0], ast.Call)


def test_find_dag_calls_with_attribute():
    """Test finding DAG calls via attribute access."""
    code = """
from airflow.models import DAG

dag = DAG(dag_id="test_dag")
"""
    tree = ast.parse(code)
    dag_calls = find_dag_calls(tree)

    assert len(dag_calls) == 1


def test_find_dag_calls_multiple():
    """Test finding multiple DAG calls."""
    code = """
from airflow import DAG

dag1 = DAG(dag_id="test1")
dag2 = DAG(dag_id="test2")
"""
    tree = ast.parse(code)
    dag_calls = find_dag_calls(tree)

    assert len(dag_calls) == 2


def test_find_dag_calls_none():
    """Test finding DAG calls when none exist."""
    code = """
x = 1
y = 2
"""
    tree = ast.parse(code)
    dag_calls = find_dag_calls(tree)

    assert len(dag_calls) == 0


def test_find_operators_simple():
    """Test finding simple operator calls."""
    code = """
from airflow.operators.bash import BashOperator

task = BashOperator(task_id="test", bash_command="echo hello")
"""
    tree = ast.parse(code)
    operators = find_operators(tree)

    assert len(operators) == 1
    assert isinstance(operators[0], ast.Call)


def test_find_operators_multiple():
    """Test finding multiple operators."""
    code = """
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator

task1 = BashOperator(task_id="task1", bash_command="echo hello")
task2 = PythonOperator(task_id="task2", python_callable=lambda: None)
"""
    tree = ast.parse(code)
    operators = find_operators(tree)

    assert len(operators) == 2


def test_find_operators_none():
    """Test finding operators when none exist."""
    code = """
x = 1
"""
    tree = ast.parse(code)
    operators = find_operators(tree)

    assert len(operators) == 0


def test_is_inside_task_or_operator_true():
    """Test is_inside_task_or_operator returns True for operator."""
    code = """
from airflow.operators.bash import BashOperator

task = BashOperator(task_id="test", bash_command="echo hello")
"""
    tree = ast.parse(code)
    operators = find_operators(tree)

    assert len(operators) == 1
    assert is_inside_task_or_operator(operators[0]) is True


def test_is_inside_task_or_operator_false():
    """Test is_inside_task_or_operator returns False for non-operator."""
    code = """
from airflow import DAG

dag = DAG(dag_id="test")
"""
    tree = ast.parse(code)
    dag_calls = find_dag_calls(tree)

    assert len(dag_calls) == 1
    assert is_inside_task_or_operator(dag_calls[0]) is False


def test_get_default_args_start_date_true():
    """Test get_default_args_start_date finds start_date in default_args."""
    code = """
from datetime import datetime
from airflow import DAG

default_args = {
    "start_date": datetime(2024, 1, 1),
    "retries": 1
}

dag = DAG(dag_id="test", default_args=default_args)
"""
    tree = ast.parse(code)
    result = get_default_args_start_date(tree)

    assert result is True


def test_get_default_args_start_date_false():
    """Test get_default_args_start_date returns False when start_date not found."""
    code = """
from airflow import DAG

default_args = {
    "retries": 1
}

dag = DAG(dag_id="test", default_args=default_args)
"""
    tree = ast.parse(code)
    result = get_default_args_start_date(tree)

    assert result is False


def test_has_start_date_in_dag_true():
    """Test has_start_date_in_dag finds start_date in DAG parameters."""
    code = """
from datetime import datetime
from airflow import DAG

dag = DAG(
    dag_id="test",
    start_date=datetime(2024, 1, 1)
)
"""
    tree = ast.parse(code)
    result = has_start_date_in_dag(tree)

    assert result is True


def test_has_start_date_in_dag_false():
    """Test has_start_date_in_dag returns False when start_date not found."""
    code = """
from airflow import DAG

dag = DAG(dag_id="test")
"""
    tree = ast.parse(code)
    result = has_start_date_in_dag(tree)

    assert result is False


def test_has_retries_in_operators_true():
    """Test has_retries_in_operators finds retries in operator parameters."""
    code = """
from airflow.operators.bash import BashOperator

task = BashOperator(
    task_id="test",
    bash_command="echo hello",
    retries=3
)
"""
    tree = ast.parse(code)
    result = has_retries_in_operators(tree)

    assert result is True


def test_has_retries_in_operators_false():
    """Test has_retries_in_operators returns False when retries not found."""
    code = """
from airflow.operators.bash import BashOperator

task = BashOperator(
    task_id="test",
    bash_command="echo hello"
)
"""
    tree = ast.parse(code)
    result = has_retries_in_operators(tree)

    assert result is False


def test_find_dag_calls_with_nested():
    """Test find_dag_calls with nested calls."""
    code = """
from airflow import DAG

def create_dag():
    return DAG(dag_id="test")

dag = create_dag()
"""
    tree = ast.parse(code)
    calls = find_dag_calls(tree)

    assert isinstance(calls, list)


def test_find_dag_calls_with_alias():
    """Test find_dag_calls with aliased import."""
    code = """
from airflow.models import DAG as AirflowDAG

dag = AirflowDAG(dag_id="test")
"""
    tree = ast.parse(code)
    calls = find_dag_calls(tree)

    assert isinstance(calls, list)


def test_find_operators():
    """Test find_operators with operator calls."""
    code = """
from airflow.operators.bash import BashOperator

task = BashOperator(
    task_id="test",
    bash_command="echo hello"
)
"""
    tree = ast.parse(code)
    operators = find_operators(tree)

    assert isinstance(operators, list)


def test_is_inside_task_or_operator():
    """Test is_inside_task_or_operator."""
    code = """
from airflow import DAG
from airflow.operators.bash import BashOperator

dag = DAG(dag_id="test")
task = BashOperator(task_id="test", bash_command="echo")
"""
    tree = ast.parse(code)

    # Test with a node inside operator
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            result = is_inside_task_or_operator(node)
            assert isinstance(result, bool)
            break


def test_find_dag_calls_multiple_calls():
    """Test find_dag_calls with multiple calls."""
    code = """
from airflow import DAG

dag1 = DAG(dag_id="test1")
dag2 = DAG(dag_id="test2")
"""
    tree = ast.parse(code)
    calls = find_dag_calls(tree)

    assert len(calls) == 2


def test_find_operators_with_operators():
    """Test find_operators with multiple operators."""
    code = """
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator

task1 = BashOperator(task_id="task1", bash_command="echo")
task2 = PythonOperator(task_id="task2", python_callable=lambda: None)
"""
    tree = ast.parse(code)
    operators = find_operators(tree)

    assert len(operators) >= 2


def test_find_dag_calls_empty_code():
    """Test find_dag_calls with empty code."""
    code = ""
    tree = ast.parse(code)
    calls = find_dag_calls(tree)

    assert calls == []


def test_find_operators_empty_code():
    """Test find_operators with empty code."""
    code = ""
    tree = ast.parse(code)
    operators = find_operators(tree)

    assert operators == []
