# Contributing

Contributions are welcome and highly appreciated! To get started, check out the guidelines below.

## Getting Started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/dkfancska/dagruff.git`
3. Create a virtual environment: `python -m venv venv`
4. Activate it: `source venv/bin/activate` (or `venv\Scripts\activate` on Windows)
5. Install in development mode: `pip install -e ".[airflow,dev]"` (or use `uv pip install -e ".[airflow,dev]"`)

## Development Workflow

1. Create a branch for your feature: `git checkout -b feature/amazing-feature`
2. Make your changes
3. Ensure tests pass: `pytest tests/`
4. Format code: `ruff format dagruff tests/`
5. Lint code: `ruff check dagruff tests/`
6. Commit your changes: `git commit -m 'Add amazing feature'`
7. Push to your fork: `git push origin feature/amazing-feature`
8. Open a Pull Request

## Code Standards

- **Formatting**: Use `ruff format` for code formatting (replaces `black`)
- **Linting**: Use `ruff check` for code quality checks
- **Type hints**: Prefer type hints for function signatures
- **Docstrings**: Add docstrings for public functions and classes
- **Tests**: Write tests for all new functionality

## Running Tests

```bash
# Run all tests
pytest tests/

# Run tests with coverage
pytest --cov=dagruff tests/

# Run specific test file
pytest tests/test_linter.py

# Run specific test
pytest tests/test_linter.py::TestDAGLinter::test_dag_import
```

## Adding New Lint Rules

To add a new lint rule:

1. **Create the rule class** in the appropriate file:
   - `dagruff/rules/dag_rules.py` for DAG-specific rules
   - `dagruff/rules/best_practices_rules.py` for best practice rules
   - `dagruff/rules/ruff_air_rules.py` for AIR series rules
   - Or create a new file if needed

2. **Create a rule checking function** following the `RuleChecker` protocol:
   ```python
   from dagruff.rules.ast_collector import ASTCollector
   from dagruff.models import LintIssue, Severity

   def check_all_my_rules(collector: ASTCollector, file_path: str) -> list[LintIssue]:
       """Apply my custom rules using collected AST data.

       This function implements the RuleChecker protocol.

       Args:
           collector: ASTCollector with collected AST data
           file_path: Path to the file being checked

       Returns:
           List of found issues
       """
       issues: list[LintIssue] = []

       # Your rule logic here
       # Example: Check for specific patterns
       if some_condition:
           issues.append(
               LintIssue(
                   file_path=file_path,
                   line=1,
                   column=0,
                   severity=Severity.WARNING,
                   rule_id="DAG999",
                   message="Description of the issue",
               )
           )

       return issues
   ```

3. **Add the rule function** to the appropriate rules module (e.g., `dagruff/rules/dag_rules.py`)

4. **Add tests** in `tests/test_linter.py`:
   ```python
   def test_my_new_rule(self):
       # Test code here
   ```

5. **Update documentation**:
   - Add rule description to `RULES.md`
   - Update rule count in `README.md` if needed

6. **Update autofix** (if applicable):
   - Add autofix logic in `dagruff/autofix.py`
   - Add tests for autofix functionality

## Project Structure

```
dagruff/
├── dagruff/                   # Main package
│   ├── __init__.py            # Package initialization
│   ├── cli/                   # CLI package
│   │   ├── __init__.py        # Main entry point
│   │   ├── runner.py          # CLI orchestrator
│   │   ├── linter.py          # Linting functions
│   │   ├── commands/          # Command pattern
│   │   │   ├── base.py        # BaseCommand
│   │   │   ├── check.py       # CheckCommand
│   │   │   └── fix.py         # FixCommand
│   │   ├── formatters/        # Output formatters
│   │   │   ├── human.py       # Human-readable format
│   │   │   └── json.py        # JSON format
│   │   └── utils/             # CLI utilities
│   │       ├── args.py        # Argument parsing
│   │       ├── files.py       # File utilities
│   │       ├── config_handler.py
│   │       └── autofix_handler.py
│   ├── config.py              # Configuration handling
│   ├── linter.py              # Main linter logic
│   ├── cache.py               # Caching implementation
│   ├── models.py              # Data models (LintIssue, Severity, etc.)
│   ├── autofix.py             # Auto-fix implementation
│   ├── validation.py          # Input validation
│   ├── logger.py              # Logging setup
│   ├── constants.py           # Constants
│   ├── plugins.py             # Plugin system
│   └── rules/                 # Lint rules
│       ├── __init__.py        # Rule registration
│       ├── base.py            # Rule protocols (RuleChecker, Linter, Autofixer)
│       ├── ast_collector.py   # AST data collector
│       ├── dag_rules.py       # DAG-specific rules
│       ├── ruff_air_rules.py  # Ruff AIR rules
│       ├── best_practices_rules.py
│       ├── airflint_rules.py
│       ├── dagbag.py          # DagBag validation
│       └── utils.py           # Rule utilities
├── tests/                     # Test suite (296+ tests)
│   ├── test_linter.py
│   ├── test_config.py
│   ├── test_autofix.py
│   ├── test_cache.py
│   ├── test_cli.py
│   ├── test_dag_rules.py
│   ├── test_best_practices_rules.py
│   ├── test_dagbag.py
│   ├── test_rules_utils.py
│   ├── test_validation.py
│   └── test_base_rule.py
├── examples/                  # Example DAG files
├── pyproject.toml             # Project configuration
├── README.md                  # Main documentation
└── RULES.md                   # Rule descriptions
```

## Commit Messages

We prefer clear, descriptive commit messages:

- Use present tense ("Add feature" not "Added feature")
- Use imperative mood ("Fix bug" not "Fixes bug")
- Reference issues when applicable: "Fix #123"

Examples:
- `Add DAG010 rule for retries validation`
- `Fix autofix for AIR003 rule`
- `Update documentation for new rules`

## Pull Requests

When submitting a PR:

- Ensure all tests pass
- Ensure code is formatted and linted
- Update documentation if needed
- Add tests for new functionality
- Keep PRs focused on a single feature or fix

## Questions?

Feel free to:
- Open an issue for bugs or feature requests
- Ask questions in discussions
- Check existing issues before creating new ones

Thank you for contributing to DagRuff! 🎉
