# Linter Rules for Airflow DAG

Complete list of linting rules implemented in the Apache Airflow DAG linter.

---

## 📋 Quick Reference

### By Category

#### 🔴 DAG Structure (13 rules)

| ID | Level | Description |
|----|-------|-------------|
| DAG001 | ERROR | Missing DAG import |
| DAG002 | WARNING | DAG definition not found |
| DAG003 | ERROR | Missing dag_id |
| DAG004 | ERROR | Duplicate dag_id |
| DAG005 | WARNING | Spaces in dag_id |
| DAG006 | WARNING | Missing DAG description |
| DAG007 | WARNING | Missing schedule_interval |
| DAG011 | ERROR | Missing dag_md |
| AIR002 | ERROR | Missing start_date |
| AIR003 | WARNING | Issues with catchup |

#### ⚙️ Configuration and Resources (8 rules)

| ID | Level | Description |
|----|-------|-------------|
| DAG009 | WARNING | Missing owner in default_args |
| DAG010 | WARNING | Missing retries in default_args |
| DAG013 | ERROR | Missing start_date in default_args |
| AIR002 | ERROR | Missing start_date in DAG (if not in default_args) |
| AIR013 | INFO | Missing max_active_runs |
| AIR014 | INFO / WARNING | Missing max_active_tasks / using deprecated concurrency |
| BP003 | INFO | Missing execution_timeout |
| BP006 | INFO | Missing dagrun_timeout |

#### 📋 Tasks and Operators (9 rules)

| ID | Level | Description |
|----|-------|-------------|
| DAG008 | INFO | Task without dag parameter |
| DAG012 | ERROR | KubernetesPodOperator without resources |
| AF001 | ERROR | Using SubDagOperator |
| AF002 | WARNING | BashOperator security risks |
| AF003 | ERROR | Duplicate task_id |
| AF004 | WARNING | Deprecated operators |
| AIRFLINT004 | ERROR | Required operator parameters |
| BP005 | INFO | Missing task docstring |

#### 🔗 Dependencies and Relationships (3 rules)

| ID | Level | Description |
|----|-------|-------------|
| AIRFLINT001 | WARNING | Missing task dependencies |
| AIRFLINT002 | INFO | Using XCom |
| BP004 | WARNING | Mixing dependency methods |

#### 🎯 Best Practices - Top-level Code (3 rules, combined)

| ID | Level | Description |
|----|-------|-------------|
| BP001 | WARNING | Top-level code in DAG file (external systems) |
| BP002 | WARNING | Using datetime functions in top-level |
| AIRFLINT003 | INFO | Using Variables in top-level |

**Note:** All three checks are performed in the `_check_top_level_code()` method for optimization.

---

### By Source

| Source | Prefix | Count |
|--------|--------|-------|
| Custom rules | DAGxxx | 11 |
| Ruff AIR | AIRxxx | 4 |
| flake8-airflow | AFxxx | 4 |
| airflint | AIRFLINTxxx | 4 |
| Best Practices | BPxxx | 6 |

---

### By Severity Level

| Level | Count | Rules |
|-------|-------|-------|
| **ERROR** | **11** | DAG001, DAG003, DAG004, DAG012, DAG013, AIR002, AF001, AF003, AIRFLINT004 |
| **WARNING** | **12** | DAG002, DAG005, DAG006, DAG007, DAG009, DAG010, DAG011, AIR003, AF002, AF004, AIRFLINT001, BP001, BP002, BP004 |
| **INFO** | **8** | DAG008, AIR013, AIR014, AIRFLINT002, AIRFLINT003, BP003, BP005, BP006 |

---

## 🗺️ Rule Grouping by Topic

### 1. DAG Structure and Validation

- **Import and Definition**: DAG001, DAG002
- **Identifiers**: DAG003, DAG004, DAG005
- **DAG Parameters**: DAG006, DAG007, DAG011, AIR002, AIR003, AIR013, AIR014, BP006

### 2. Parameters and Configuration

- **default_args**: DAG009 (owner), DAG010 (retries), DAG013 (start_date)
- **start_date**: AIR002 (in DAG, if not in default_args), DAG013 (in default_args)
- **Timeouts**: BP003, BP006

### 3. Tasks and Operators

- **Task Definition**: DAG008, AIRFLINT004
- **Specific Operators**: AF001, AF002, AF004, DAG012
- **Task Identifiers**: AF003
- **Documentation**: BP005

### 4. Dependencies and Relationships

- **Task Dependencies**: AIRFLINT001, BP004
- **XCom and Variables**: AIRFLINT002, AIRFLINT003

### 5. Best Practices

- **Top-level Code**: BP001, BP002, AIRFLINT003 (combined)

---

## 📖 Detailed Rule Descriptions

### Basic DAG Rules

#### DAG001 - Missing DAG Import
**Level:** ERROR  
**Source:** Custom rule

**Description:** DAG file must contain DAG import from airflow module.

**Violation Example:**
```python
# Missing DAG import
default_args = {"owner": "airflow"}
```

**Fix Example:**
```python
from airflow import DAG
# or
from airflow.models import DAG
```

---

#### DAG002 - DAG Definition Not Found
**Level:** WARNING  
**Source:** Custom rule

**Description:** DAG definition via DAG() constructor not found in file.

**Violation Example:**
```python
from airflow import DAG
# DAG not defined
```

---

#### DAG003 - Missing dag_id
**Level:** ERROR  
**Source:** Custom rule

**Description:** DAG must have required `dag_id` parameter.

**Violation Example:**
```python
dag = DAG(
    description="My DAG",
    # dag_id missing
)
```

**Fix Example:**
```python
dag = DAG(dag_id="my_dag")
```

---

#### DAG004 - Duplicate dag_id
**Level:** ERROR  
**Source:** Custom rule

**Description:** Multiple DAGs with the same `dag_id` should not exist in one file.

**Violation Example:**
```python
dag1 = DAG(dag_id="my_dag")
dag2 = DAG(dag_id="my_dag")  # Duplicate!
```

---

#### DAG005 - Spaces in dag_id
**Level:** WARNING  
**Source:** Custom rule

**Description:** `dag_id` should not contain leading or trailing spaces.

**Violation Example:**
```python
dag = DAG(dag_id=" my_dag ")  # Extra spaces
```

---

#### DAG006 - Missing DAG Description
**Level:** WARNING  
**Source:** Custom rule

**Description:** It's recommended to add DAG description via `description` parameter.

**Violation Example:**
```python
dag = DAG(dag_id="my_dag")  # No description
```

**Fix Example:**
```python
dag = DAG(
    dag_id="my_dag",
    description="My DAG description"
)
```

---

#### DAG007 - Missing schedule_interval
**Level:** WARNING  
**Source:** Custom rule

**Description:** It's recommended to explicitly specify `schedule_interval` or `schedule` for DAG.

**Violation Example:**
```python
dag = DAG(dag_id="my_dag")  # No schedule
```

**Fix Example:**
```python
dag = DAG(
    dag_id="my_dag",
    schedule_interval="@daily"
)
```

---

#### DAG009 - Missing owner in default_args
**Level:** WARNING  
**Source:** Custom rule

**Description:** It's recommended to include `owner` parameter in `default_args` to specify DAG owner.

**Note:** `start_date` is checked separately in rule **AIR002** as a required parameter (ERROR).

**Violation Example:**
```python
default_args = {
    "retries": 1,
    # Missing owner
}
```

**Fix Example:**
```python
default_args = {
    "owner": "airflow",
    "retries": 1,
    # start_date is checked in AIR002
}
```

---

#### DAG010 - Missing retries in default_args
**Level:** WARNING  
**Source:** Custom rule

**Description:** It's recommended to include `retries` parameter in `default_args` to specify number of retry attempts on task failure.

**Violation Example:**
```python
default_args = {
    "owner": "airflow",
    # Missing retries
}
```

**Fix Example:**
```python
default_args = {
    "owner": "airflow",
    "retries": 1,
}
```

---

#### DAG013 - Missing start_date in default_args
**Level:** ERROR  
**Source:** Custom rule

**Description:** If `default_args` is defined in file, it must contain `start_date` parameter. This allows centralized management of start date for all DAG tasks.

**Note:** 
- Rule only triggers if `default_args` is defined in file
- If `start_date` is specified directly in DAG (not in `default_args`), this rule doesn't trigger
- Rule AIR002 checks for `start_date` in DAG itself, if it's missing in `default_args` or `default_args` is not defined

**Violation Example:**
```python
default_args = {
    "owner": "airflow",
    "retries": 1,
    # Missing start_date
}
```

**Fix Example:**
```python
from datetime import datetime

default_args = {
    "owner": "airflow",
    "retries": 1,
    "start_date": datetime(2024, 1, 1),
}
```

---

#### DAG011 - Missing dag_md
**Level:** WARNING  
**Source:** Custom rule

**Description:** It's recommended to specify `dag_md` parameter in DAG for metadata.

**Violation Example:**
```python
dag = DAG(
    dag_id="my_dag",
    # Missing dag_md
)
```

**Fix Example:**
```python
dag = DAG(
    dag_id="my_dag",
    dag_md={"owner": "team", "description": "My DAG"}
)
```

---

#### DAG012 - KubernetesPodOperator Without Resources
**Level:** ERROR  
**Source:** Custom rule

**Description:** `KubernetesPodOperator` must have required `container_resources` and `executor_resources` parameters for proper resource management in Kubernetes.

**Violation Example:**
```python
from airflow.providers.cncf.kubernetes.operators.kubernetes_pod import KubernetesPodOperator

task = KubernetesPodOperator(
    task_id="my_task",
    name="my-pod",
    # Missing container_resources and executor_resources
)
```

**Fix Example:**
```python
from airflow.providers.cncf.kubernetes.operators.kubernetes_pod import KubernetesPodOperator
from kubernetes.client import models as k8s

task = KubernetesPodOperator(
    task_id="my_task",
    name="my-pod",
    container_resources=k8s.V1ResourceRequirements(
        requests={"memory": "512Mi", "cpu": "500m"},
        limits={"memory": "1Gi", "cpu": "1000m"}
    ),
    executor_resources=k8s.V1ResourceRequirements(
        requests={"memory": "256Mi", "cpu": "250m"},
        limits={"memory": "512Mi", "cpu": "500m"}
    )
)
```

---

### Rules from Ruff AIR Series

#### AIR002 - Missing start_date in DAG
**Level:** ERROR  
**Source:** Ruff AIR rules

**Description:** DAG must have `start_date` parameter. Check is performed in DAG itself, if `start_date` is missing in `default_args`. If `start_date` exists in `default_args`, rule AIR002 doesn't trigger (but DAG013 triggers if `default_args` is defined but doesn't contain `start_date`).

**Violation Example:**
```python
dag = DAG(dag_id="my_dag")  # No start_date in DAG or default_args
```

**Fix Example:**
```python
dag = DAG(
    dag_id="my_dag",
    start_date=datetime(2024, 1, 1)
)
# or via default_args (checked by DAG013 rule)
default_args = {
    "start_date": datetime(2024, 1, 1)
}
```

---

#### AIR003 - Issues with catchup
**Level:** WARNING  
**Source:** Ruff AIR rules

**Description:** 
- It's recommended to explicitly specify `catchup=False` to prevent execution of missed tasks
- If `catchup=True`, warning is issued about potential execution of large number of missed tasks

**Violation Example:**
```python
dag = DAG(dag_id="my_dag")  # catchup not specified
# or
dag = DAG(dag_id="my_dag", catchup=True)  # Dangerous!
```

**Fix Example:**
```python
dag = DAG(
    dag_id="my_dag",
    catchup=False  # Explicitly specify
)
```

---

#### AIR013 - Missing max_active_runs
**Level:** INFO  
**Source:** Ruff AIR rules

**Description:** It's recommended to specify `max_active_runs` to limit parallel DAG runs.

**Violation Example:**
```python
dag = DAG(dag_id="my_dag")  # No limit
```

**Fix Example:**
```python
dag = DAG(
    dag_id="my_dag",
    max_active_runs=1
)
```

---

#### AIR014 - Missing max_active_tasks / concurrency
**Level:** INFO / WARNING  
**Source:** Ruff AIR rules (updated for Airflow 2+)

**Description:** 
- For Airflow 2+ it's recommended to use `max_active_tasks` to limit parallel tasks in DAG
- If deprecated `concurrency` parameter is used, warning is issued
- `concurrency` parameter is considered deprecated in Airflow 2+ and replaced with `max_active_tasks`

**Violation Example:**
```python
dag = DAG(dag_id="my_dag")  # No limit
```

**Violation Example (deprecated parameter):**
```python
dag = DAG(
    dag_id="my_dag",
    concurrency=5  # Deprecated parameter for Airflow 2+
)
```

**Fix Example:**
```python
dag = DAG(
    dag_id="my_dag",
    max_active_tasks=5  # Recommended for Airflow 2+
)
```

---

### Rules from flake8-airflow

#### AF001 - Using SubDagOperator
**Level:** ERROR  
**Source:** flake8-airflow (AA101)

**Description:** `SubDagOperator` is deprecated since Airflow 2.0 and not recommended for use. Use `TaskGroup` instead.

**Violation Example:**
```python
from airflow.operators.subdag import SubDagOperator

subdag = SubDagOperator(
    task_id="subdag",
    subdag=create_subdag(),
)
```

**Fix Example:**
```python
from airflow.utils.task_group import TaskGroup

with TaskGroup("my_group") as tg:
    task1 = BashOperator(task_id="task1", bash_command="echo 1")
    task2 = BashOperator(task_id="task2", bash_command="echo 2")
```

---

#### AF002 - BashOperator Security Risks
**Level:** WARNING  
**Source:** flake8-airflow (AA102)

**Description:** `BashOperator` doesn't escape strings in `bash_command`, which can pose potential security risk when using user input.

**Violation Example:**
```python
task = BashOperator(
    task_id="task",
    bash_command="echo $USER && rm -rf /tmp/*"  # Dangerous constructs
)
```

**Recommendation:** Be careful with user input. Consider using alternative operators.

---

#### AF003 - Duplicate task_id
**Level:** ERROR  
**Source:** flake8-airflow

**Description:** All tasks in DAG must have unique `task_id`.

**Violation Example:**
```python
task1 = BashOperator(task_id="print_date", bash_command="date")
task2 = BashOperator(task_id="print_date", bash_command="date")  # Duplicate!
```

**Fix Example:**
```python
task1 = BashOperator(task_id="print_date_1", bash_command="date")
task2 = BashOperator(task_id="print_date_2", bash_command="date")
```

---

#### AF004 - Deprecated Operators
**Level:** WARNING  
**Source:** flake8-airflow

**Description:** Check for usage of deprecated operators that have been replaced with new versions.

**Deprecated Operator Examples:**
- `DataProcPySparkOperator` → `DataProcPySparkJobOperator`
- `DataProcSparkOperator` → `DataProcSparkJobOperator`
- `DataProcHadoopOperator` → `DataProcHadoopJobOperator`

**Violation Example:**
```python
from airflow.providers.google.cloud.operators.dataproc import DataProcPySparkOperator

task = DataProcPySparkOperator(...)
```

**Fix Example:**
```python
from airflow.providers.google.cloud.operators.dataproc import DataProcPySparkJobOperator

task = DataProcPySparkJobOperator(...)
```

---

### Rules from airflint (AST Linter)

#### AIRFLINT001 - Missing Task Dependencies
**Level:** WARNING  
**Source:** airflint (AST linter)

**Description:** If multiple tasks are defined in DAG but no explicit dependencies between them, warning is issued.

**Violation Example:**
```python
task1 = BashOperator(task_id="task1", bash_command="echo 1")
task2 = BashOperator(task_id="task2", bash_command="echo 2")
# No dependencies between tasks
```

**Fix Example:**
```python
task1 = BashOperator(task_id="task1", bash_command="echo 1")
task2 = BashOperator(task_id="task2", bash_command="echo 2")

task1 >> task2  # Set dependency
```

---

#### AIRFLINT002 - Using XCom
**Level:** INFO  
**Source:** airflint (AST linter)

**Description:** Check for correct XCom usage in `PythonOperator`. In modern Airflow versions, using `provide_context` is not required, `op_kwargs` is used instead.

**Correct Usage Example:**
```python
def pull_data(**context):
    value = context['ti'].xcom_pull(task_ids='previous_task')
    return value

task = PythonOperator(
    task_id="task",
    python_callable=pull_data,
    # provide_context not required in new versions
)
```

---

#### AIRFLINT003 - Using Variables in Top-level Code
**Level:** INFO  
**Source:** airflint (AST linter)

**Description:** Check for `Variable.get()` usage at module level. Airflow Variables should not be loaded at module level, as this executes on every DAG file parsing.

**Note:** This check is combined with BP001 in `_check_top_level_code()` method, but retains its rule_id (AIRFLINT003) for backward compatibility.

**Incorrect Usage Example:**
```python
from airflow.models import Variable

# ❌ Incorrect - at module level
MY_VAR = Variable.get("my_key")
```

**Correct Usage Example:**
```python
def my_function(**context):
    # ✅ Correct - inside function or task
    my_var = Variable.get("my_key")
    return my_var

task = PythonOperator(
    task_id="task",
    python_callable=my_function
)
```

---

#### AIRFLINT004 - Required Operator Parameters
**Level:** ERROR  
**Source:** airflint (AST linter)

**Description:** Check for presence of required parameters for various operators.

**Required Parameters:**
- `BashOperator`: `bash_command`
- `PythonOperator`: `python_callable`
- `EmailOperator`: `to`

**Violation Example:**
```python
task = BashOperator(task_id="task")  # Missing bash_command
```

**Fix Example:**
```python
task = BashOperator(
    task_id="task",
    bash_command="echo hello"
)
```

---

### Best Practices from Astronomer and Official Documentation

#### BP001 - Top-level Code in DAG File
**Level:** WARNING  
**Source:** [Astronomer Best Practices](https://www.astronomer.io/docs/learn/dag-best-practices)

**Description:** Checks three aspects of top-level code:
1. External system calls (databases, APIs) at module level
2. Using datetime functions (`datetime.today()`, `datetime.now()`) in top-level code
3. Using `Variable.get()` at module level

Code executing during DAG parsing (top-level code) can cause performance issues and violate idempotency.

**Violation Example:**
```python
from airflow.providers.postgres.hooks.postgres import PostgresHook
from datetime import datetime
from airflow.models import Variable

# ❌ Incorrect - executes on every DAG parsing
hook = PostgresHook("database_conn")
results = hook.get_records("SELECT * FROM grocery_list;")

today = datetime.today()  # Violates idempotency

MY_VAR = Variable.get("my_key")  # Executes on parsing

@dag(...)
def my_dag():
    task = PythonOperator(...)
```

**Fix Example:**
```python
@dag(...)
def my_dag():
    @task
    def get_list_of_results():
        # ✅ Correct - executes only when task runs
        hook = PostgresHook("database_conn")
        results = hook.get_records("SELECT * FROM grocery_list;")
        return results
    
    @task
    def process_data(**context):
        # ✅ Use Airflow macros instead of datetime.today()
        execution_date = context['ds']
        my_var = Variable.get("my_key")  # Inside task
        return execution_date
```

**Note:** This is a combined rule that includes checks for BP001 (external systems), BP002 (datetime functions), and AIRFLINT003 (Variables). Each check has its own rule_id, but all are executed in one `_check_top_level_code()` method.

---

#### BP003 - Missing execution_timeout
**Level:** INFO  
**Source:** Best Practices

**Description:** It's recommended to specify `execution_timeout` for tasks to prevent infinite task execution and ensure timely completion.

**Violation Example:**
```python
task = PythonOperator(
    task_id="long_running_task",
    python_callable=my_function
    # Missing execution_timeout
)
```

**Fix Example:**
```python
from datetime import timedelta

task = PythonOperator(
    task_id="long_running_task",
    python_callable=my_function,
    execution_timeout=timedelta(hours=2)
)
```

---

#### BP004 - Mixing Dependency Methods
**Level:** WARNING  
**Source:** [Astronomer Best Practices](https://www.astronomer.io/docs/learn/dag-best-practices)

**Description:** It's recommended to use one consistent method for setting task dependencies (`>>`/`<<` or `set_upstream`/`set_downstream`) for better code readability.

**Violation Example:**
```python
task_1.set_downstream(task_2)
task_3.set_upstream(task_2)
task_3 >> task_4  # Mixing methods
```

**Fix Example:**
```python
# ✅ Use one method
task_1 >> task_2 >> [task_3, task_4]
```

---

#### BP005 - Missing Task Docstring
**Level:** INFO  
**Source:** Best Practices

**Description:** It's recommended to add docstring (`doc_md`) for tasks for better documentation and understanding of their purpose.

**Violation Example:**
```python
task = BashOperator(
    task_id="process_data",
    bash_command="python process.py"
    # Missing doc_md
)
```

**Fix Example:**
```python
task = BashOperator(
    task_id="process_data",
    bash_command="python process.py",
    doc_md="""
    ## Process Data Task
    
    This task processes the incoming data files.
    """
)
```

---

#### BP006 - Missing dagrun_timeout
**Level:** INFO  
**Source:** Best Practices

**Description:** It's recommended to specify `dagrun_timeout` for DAG to set maximum DAG Run execution time and prevent stuck runs.

**Violation Example:**
```python
dag = DAG(
    dag_id="my_dag",
    # Missing dagrun_timeout
)
```

**Fix Example:**
```python
from datetime import timedelta

dag = DAG(
    dag_id="my_dag",
    dagrun_timeout=timedelta(hours=4)
)
```

---

## 📊 Final Statistics

- **Total Rules**: **31**
  - Basic DAG structure checks: 13 rules
  - Rules from Ruff AIR series: 4 rules
  - Rules from flake8-airflow: 4 rules
  - Rules from airflint AST linter: 4 rules
  - Best practices: 6 rules

- **By Severity Level**:
  - **ERROR**: 11 rules
  - **WARNING**: 12 rules
  - **INFO**: 8 rules

- **Optimization**: Some checks are combined into single methods for better performance:
  - `_check_top_level_code()` performs checks for BP001, BP002, and AIRFLINT003
  - `check_default_args_owner()` checks only owner (DAG009)
  - `check_default_args_retries()` checks only retries (DAG010)
  - `check_default_args_start_date()` checks only start_date in default_args (DAG013)

---

## 🔍 Notes

1. **default_args Rule Separation**: All `default_args` parameter checks are separated into individual rules:
   - DAG009 - checks `owner` in `default_args`
   - DAG010 - checks `retries` in `default_args`
   - DAG013 - checks `start_date` in `default_args` (if `default_args` is defined)
   
   This allows ignoring each rule independently and using different defaults for autofix.

2. **Combined Checks**: Rules BP001, BP002, and AIRFLINT003 are combined into one `_check_top_level_code()` method, but retain their rule_id for backward compatibility.

3. **Avoiding Duplication**: 
   - `start_date` is checked only in AIR002 (ERROR)
   - `dag_id` is checked only in DAG003 (ERROR)

All rules are aimed at ensuring quality, security, and compliance with best practices when developing DAGs in Apache Airflow.
