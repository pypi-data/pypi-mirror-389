# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.0.0] - 2024-11-06

### Added
- Initial release with 31 lint rules
- Auto-fix support for 7 rules
- CLI interface with JSON output
- Configuration via `pyproject.toml` or `.dagruff.toml`
- Support for AST-based checks without Airflow
- Optional DagBag validation with Airflow
- Basic DAG validation rules (13 rules)
- Ruff AIR rules integration (4 rules)
- flake8-airflow rules (4 rules)
- airflint AST rules (4 rules)
- Best practices rules (6 rules)
- Auto-fix functionality for common issues
- CLI tool `dagruff`
- Configuration file support
- Test suite

[Unreleased]: https://github.com/dkfancska/dagruff/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/dkfancska/dagruff/releases/tag/v1.0.0
