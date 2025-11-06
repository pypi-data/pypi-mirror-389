# Pre-commit Hooks Setup

This project uses pre-commit hooks to ensure code quality and run tests before committing.

## Installation

### Option 1: Pre-commit Framework (Recommended)

1. Install pre-commit:
   ```bash
   pip install pre-commit
   ```

2. Install the hooks:
   ```bash
   pre-commit install
   ```

3. (Optional) Install hooks for all repos:
   ```bash
   pre-commit install --install-hooks
   ```

### Option 2: Git Hook Script (Simple)

The project includes a simple git hook script at `.git/hooks/pre-commit`.

To use it:
```bash
chmod +x .git/hooks/pre-commit
```

**Note:** This hook must be installed manually in each clone. For team use, prefer the pre-commit framework.

## What It Does

The pre-commit hooks will:

1. **Run tests** - Execute `pytest tests/` to ensure all tests pass
2. **Format code** - Run `ruff format` to format Python code
3. **Lint code** - Run `ruff check` to catch code quality issues
4. **Check files** - Verify YAML, JSON files and check for merge conflicts
5. **Prevent large files** - Block commits with files larger than 1MB

## Bypassing Hooks (Not Recommended)

If you need to bypass the hooks (e.g., for WIP commits):

```bash
git commit --no-verify -m "WIP: work in progress"
```

**Warning:** Only bypass hooks if absolutely necessary. Running tests before committing helps catch issues early.

## Manual Execution

Run hooks manually on all files:

```bash
pre-commit run --all-files
```

Run hooks on staged files only:

```bash
pre-commit run
```

## Configuration

Hook configuration is in `.pre-commit-config.yaml`. To modify hooks:

1. Edit `.pre-commit-config.yaml`
2. Update hooks: `pre-commit install`
3. Test: `pre-commit run --all-files`

