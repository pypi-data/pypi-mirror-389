"""Пример DAG файла с ошибками для демонстрации линтера."""

from datetime import datetime
# Отсутствует импорт DAG из airflow

# Импорт операторов есть, но DAG импортирован неправильно
from airflow.operators.bash import BashOperator

default_args = {
    "owner": "airflow",
"retries": 1,
    # Отсутствует start_date и retries
}

# DAG без dag_id - линтер должен найти эту ошибку
# НО: для демонстрации нужно использовать правильный импорт, 
# иначе будет синтаксическая ошибка, а не ошибка линтера
from airflow import DAG

dag = DAG(
    # dag_id отсутствует - ошибка DAG003
    description="Пример неправильного DAG",
    # Отсутствует schedule_interval - предупреждение DAG007
)

task1 = BashOperator(
    task_id="print_date",
    bash_command="date",
    # Отсутствует параметр dag - информация DAG008
)

