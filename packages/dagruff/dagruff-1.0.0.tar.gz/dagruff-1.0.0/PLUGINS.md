# Plugin System for DagRuff

DagRuff supports a plugin architecture that allows you to add custom linting rules without modifying the main codebase.

## Overview

The plugin system uses Python's entry points mechanism to discover and load custom rule checkers at runtime. All plugins must implement the `RuleChecker` protocol defined in `dagruff.rules.base`.

## Creating a Plugin

### Step 1: Create Your Rule Checker Function

Your plugin should provide a function that follows the `RuleChecker` protocol:

```python
# my_plugin/__init__.py
from typing import List
from dagruff.rules.ast_collector import ASTCollector
from dagruff.models import LintIssue, Severity

def check_all_custom_rules(collector: ASTCollector, file_path: str) -> List[LintIssue]:
    """Apply custom rules using collected AST data.
    
    This function implements the RuleChecker protocol.
    
    Args:
        collector: ASTCollector with collected AST data
        file_path: Path to the file being checked
        
    Returns:
        List of found issues
    """
    issues: List[LintIssue] = []
    
    # Your custom rule logic here
    # Example: Check for specific patterns in DAG calls
    for dag_call in collector.dag_calls:
        # Check something custom
        if some_condition:
            issues.append(
                LintIssue(
                    file_path=file_path,
                    line=dag_call.lineno,
                    column=dag_call.col_offset,
                    severity=Severity.WARNING,
                    rule_id="CUSTOM001",
                    message="Custom rule violation",
                )
            )
    
    return issues
```

### Step 2: Register Your Plugin

In your package's `pyproject.toml`, add an entry point:

```toml
[project.entry-points."dagruff.rules"]
my_custom_rule = "my_plugin:check_all_custom_rules"
```

Or if you're using `setup.py`:

```python
setup(
    ...
    entry_points={
        "dagruff.rules": [
            "my_custom_rule = my_plugin:check_all_custom_rules",
        ],
    },
)
```

### Step 3: Install Your Plugin

Install your plugin package:

```bash
pip install my-plugin
# or
uv pip install my-plugin
```

DagRuff will automatically discover and load your plugin when it runs.

## Plugin Requirements

1. **Function Signature**: Must match `(collector: ASTCollector, file_path: str) -> List[LintIssue]`
2. **Return Type**: Must return a list of `LintIssue` objects
3. **Protocol Compliance**: Function must implement the `RuleChecker` protocol

## Example Plugin Package Structure

```
my-dagruff-plugin/
├── pyproject.toml
├── README.md
└── my_plugin/
    ├── __init__.py
    └── rules.py
```

## Using ASTCollector

The `ASTCollector` provides access to pre-collected AST data:

- `collector.dag_calls` - List of DAG call nodes
- `collector.operators` - List of operator call nodes
- `collector.has_dag_import()` - Check if DAG is imported
- `collector.has_default_args_key(key)` - Check if key exists in default_args
- `collector.task_assignments` - Task assignments
- And more...

See `dagruff/rules/ast_collector.py` for the full API.

## Plugin Loading

Plugins are loaded automatically when DagRuff starts. If a plugin fails to load (e.g., import error, protocol mismatch), it will be skipped with a warning, and DagRuff will continue with other plugins and built-in rules.

## Best Practices

1. **Use Rule IDs**: Follow a consistent naming scheme for your rule IDs (e.g., `CUSTOM001`, `CUSTOM002`)
2. **Documentation**: Document what each rule checks
3. **Error Handling**: Handle edge cases gracefully
4. **Testing**: Write tests for your plugin rules
5. **Performance**: Keep plugin rules efficient, as they run in parallel with other rules

## Troubleshooting

If your plugin is not loading:

1. **Check Installation**: Ensure your plugin package is installed
2. **Verify Entry Point**: Check that the entry point is correctly registered in `pyproject.toml`
3. **Check Logs**: Enable debug logging to see plugin loading messages:
   ```bash
   dagruff --log-level DEBUG path/to/dags/
   ```
4. **Protocol Compliance**: Ensure your function matches the `RuleChecker` protocol signature

## Examples

See the built-in rules in `dagruff/rules/` for examples of how to implement rule checkers:
- `dag_rules.py` - DAG-specific rules
- `ruff_air_rules.py` - Ruff AIR rules
- `best_practices_rules.py` - Best practices rules

