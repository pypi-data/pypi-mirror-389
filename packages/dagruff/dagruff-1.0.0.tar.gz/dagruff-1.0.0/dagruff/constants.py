"""Constants used across the dagruff package."""

# ============================================================================
# Autofix Constants
# ============================================================================

# Maximum number of lines to search when parsing dictionary or function blocks
MAX_LINES_TO_SEARCH = 50

# Set of rule IDs that can be automatically fixed
FIXABLE_RULE_IDS = {"DAG001", "DAG005", "DAG009", "DAG010", "AIR003", "AIR013", "AIR014"}

# ============================================================================
# Airflow-related Constants
# ============================================================================

# Airflow module and class names
AIRFLOW_MODULE_NAME = "airflow"
DAG_CLASS_NAME = "DAG"
DAG_IMPORT_STATEMENT = "from airflow import DAG\n"
DAG_CALL_PATTERN = "DAG("

# Airflow import patterns for DAG file detection
AIRFLOW_IMPORT_FROM_PATTERN = "from airflow import"
AIRFLOW_IMPORT_PATTERN = "import airflow"
AIRFLOW_DECORATORS_IMPORT_PATTERN = "from airflow.decorators import"

# ============================================================================
# Default Values for Autofix
# ============================================================================

DEFAULT_OWNER_VALUE = "airflow"
DEFAULT_RETRIES_VALUE = 1
DEFAULT_CATCHUP_VALUE = False
DEFAULT_MAX_ACTIVE_RUNS_VALUE = 1
DEFAULT_MAX_ACTIVE_TASKS_VALUE = 1

# ============================================================================
# Autofix String Templates
# ============================================================================

OWNER_KEY_VALUE_TEMPLATE = '"owner": "airflow",'
RETRIES_KEY_VALUE_TEMPLATE = '"retries": 1,'
CATCHUP_PARAM_VALUE_TEMPLATE = "catchup=False,"
MAX_ACTIVE_RUNS_PARAM_VALUE_TEMPLATE = "max_active_runs=1,"
MAX_ACTIVE_TASKS_PARAM_VALUE_TEMPLATE = "max_active_tasks=1,"
MAX_ACTIVE_TASKS_REPLACEMENT = "max_active_tasks="

# ============================================================================
# Python Syntax Constants
# ============================================================================

# Python keywords
IMPORT_KEYWORD = "import"
FROM_KEYWORD = "from"

# ============================================================================
# File Detection and Processing Constants
# ============================================================================

# Package name to exclude from DAG file detection
DAGRUFF_PACKAGE_NAME = "dagruff"

# Python file extension (for rglob pattern)
PYTHON_FILE_EXTENSION = "*.py"

# Standard ignore patterns (similar to .gitignore)
STANDARD_IGNORE_PATTERNS = [
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".venv",
    "venv",
    "ENV",
    "env",
    ".tox",
    ".hypothesis",
    ".idea",
    ".vscode",
    ".git",
    "*.egg-info",
    "build",
    "dist",
    ".coverage",
    "htmlcov",
]

# Config file exception
CONFIG_FILE_EXCEPTION = ".dagruff.toml"

# ============================================================================
# CLI Output Constants
# ============================================================================

# Top rules count for statistics
TOP_RULES_COUNT = 10

# Example message truncation length
EXAMPLE_MESSAGE_TRUNCATE_LENGTH = 70
