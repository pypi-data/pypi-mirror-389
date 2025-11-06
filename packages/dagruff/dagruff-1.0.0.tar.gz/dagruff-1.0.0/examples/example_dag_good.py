"""Пример правильного DAG файла."""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.bash import BashOperator

default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
    "start_date": datetime(2024, 1, 1),
}

dag = DAG(
    dag_id="example_good_dag",
    default_args=default_args,
    description="Пример правильного DAG",
    schedule_interval=timedelta(days=1),
    catchup=False,
    tags=["example"],
)

task1 = BashOperator(
    task_id="print_date",
    bash_command="date",
    dag=dag,
)

task2 = BashOperator(
    task_id="sleep",
    bash_command="sleep 5",
    dag=dag,
)

task1 >> task2

