"""Main linter module for checking DAG files (optimized version with single AST traversal)."""

import ast
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional

from dagruff.cache import LinterCache
from dagruff.logger import get_logger
from dagruff.models import LintIssue, Severity
from dagruff.plugins import load_plugins
from dagruff.rules import (
    airflint_rules,
    best_practices_rules,
    dag_rules,
    ruff_air_rules,
)
from dagruff.rules.ast_collector import ASTCollector
from dagruff.rules.base import RuleChecker
from dagruff.rules.dagbag import check_dagbag_validation
from dagruff.validation import validate_encoding, validate_file_path

logger = get_logger(__name__)

# Global cache instance (singleton)
_global_cache: Optional[LinterCache] = None


def get_cache(enabled: bool = True) -> LinterCache:
    """Get global cache instance.

    Args:
        enabled: Whether caching is enabled

    Returns:
        Global cache instance
    """
    global _global_cache
    if _global_cache is None:
        _global_cache = LinterCache(enabled=enabled)
    return _global_cache


def set_cache(cache: Optional[LinterCache]) -> None:
    """Set global cache instance.

    Args:
        cache: Cache instance to use, or None to use default
    """
    global _global_cache
    _global_cache = cache


class DAGLinter:
    """Linter for checking Airflow DAG files with optimized AST traversal."""

    def __init__(self, file_path: str, cache: Optional[LinterCache] = None):
        """Initialize linter for specific file.

        Args:
            file_path: Path to file to lint
            cache: Optional cache instance, uses global cache if None
        """
        self.file_path = file_path
        self.issues: list[LintIssue] = []
        self.tree: Optional[ast.AST] = None
        self.source_code: str = ""
        self.collector: Optional[ASTCollector] = None
        self.cache = cache if cache is not None else get_cache()

    def lint(self) -> list[LintIssue]:
        """Run file check with caching and validation.

        Performs linting of the file with the following steps:
        1. Check cache for previously computed results
        2. Validate file path and encoding
        3. Parse file into AST
        4. Check DAG validity via DagBag
        5. Collect AST data using ASTCollector
        6. Run all rule checks in parallel
        7. Cache results for future use

        Returns:
            List of found lint issues
        """
        try:
            logger.debug(f"Starting file check: {self.file_path}")

            # Check cache first
            cached_issues = self.cache.get(self.file_path)
            if cached_issues is not None:
                logger.debug(f"Using cached results for {self.file_path}")
                self.issues = cached_issues
                return self.issues

            # Validate file path before processing
            is_valid, error_msg = validate_file_path(self.file_path)
            if not is_valid:
                logger.error(f"File validation failed: {error_msg}")
                self.issues.append(
                    LintIssue(
                        file_path=self.file_path,
                        line=0,
                        column=0,
                        severity=Severity.ERROR,
                        rule_id="VALIDATION_ERROR",
                        message=error_msg or "File validation failed",
                    )
                )
                # Don't cache validation errors
                return self.issues

            # Validate encoding
            is_valid_encoding, encoding_error = validate_encoding(self.file_path)
            if not is_valid_encoding:
                logger.error(f"Encoding validation failed: {encoding_error}")
                self.issues.append(
                    LintIssue(
                        file_path=self.file_path,
                        line=0,
                        column=0,
                        severity=Severity.ERROR,
                        rule_id="ENCODING_ERROR",
                        message=encoding_error or "Cannot read file with UTF-8 encoding",
                    )
                )
                return self.issues

            # Read file with validated path and encoding
            with open(self.file_path, encoding="utf-8") as f:
                self.source_code = f.read()

            logger.debug(f"File size: {len(self.source_code)} characters")
            self.tree = ast.parse(self.source_code, filename=self.file_path)

            # OPTIMIZATION: Single AST traversal to collect all data
            # Always create collector after AST parsing, even if DagBag has errors
            logger.debug("Collecting data from AST (single traversal)")
            self.collector = ASTCollector(self.tree)
            self.collector.collect()

            # Check DAG validity via DagBag (first check)
            logger.debug("Checking via DagBag")
            dagbag_issues = check_dagbag_validation(self.file_path)
            self.issues.extend(dagbag_issues)

            # If there are critical DagBag errors, don't continue with other checks
            has_critical_dagbag_errors = any(
                issue.severity == Severity.ERROR and issue.rule_id.startswith("DAGBAG")
                for issue in dagbag_issues
            )

            if has_critical_dagbag_errors:
                logger.warning(
                    f"Critical DagBag errors detected in {self.file_path}, skipping other checks"
                )

            if not has_critical_dagbag_errors:
                logger.debug("Applying check rules")
                self._check_rules()

            logger.info(f"Check completed: found {len(self.issues)} issues in {self.file_path}")

            # Cache results
            self.cache.set(self.file_path, self.issues)
        except SyntaxError as e:
            logger.error(
                f"Syntax error in {self.file_path}: {e.msg} (line {e.lineno})", exc_info=True
            )
            self.issues.append(
                LintIssue(
                    file_path=self.file_path,
                    line=e.lineno or 0,
                    column=e.offset or 0,
                    severity=Severity.ERROR,
                    rule_id="SYNTAX_ERROR",
                    message=f"Syntax error: {e.msg}",
                )
            )
        except FileNotFoundError as e:
            logger.error(f"File not found: {self.file_path}", exc_info=True)
            self.issues.append(
                LintIssue(
                    file_path=self.file_path,
                    line=0,
                    column=0,
                    severity=Severity.ERROR,
                    rule_id="FILE_NOT_FOUND",
                    message=f"File not found: {str(e)}",
                )
            )
        except PermissionError as e:
            logger.error(f"No access to file: {self.file_path}", exc_info=True)
            self.issues.append(
                LintIssue(
                    file_path=self.file_path,
                    line=0,
                    column=0,
                    severity=Severity.ERROR,
                    rule_id="PERMISSION_ERROR",
                    message=f"No access to file: {str(e)}",
                )
            )
        except (OSError, UnicodeDecodeError, ValueError) as e:
            # Specific file and data handling errors
            logger.exception(f"Error processing file {self.file_path}: {e}")
            self.issues.append(
                LintIssue(
                    file_path=self.file_path,
                    line=0,
                    column=0,
                    severity=Severity.ERROR,
                    rule_id="PARSE_ERROR",
                    message=f"File processing error: {str(e)}",
                )
            )
        except (KeyboardInterrupt, SystemExit):
            # System exceptions should not be caught
            raise
        except Exception as e:
            # Last catch-all only for unexpected AST parsing errors
            logger.exception(f"Unexpected error parsing AST file {self.file_path}: {e}")
            self.issues.append(
                LintIssue(
                    file_path=self.file_path,
                    line=0,
                    column=0,
                    severity=Severity.ERROR,
                    rule_id="PARSE_ERROR",
                    message=f"Unexpected parsing error: {str(e)}",
                )
            )

        return self.issues

    def _check_rules(self):
        """Apply all check rules using collected data with parallel execution.

        Loads built-in rules and plugins, then executes them in parallel using
        ThreadPoolExecutor for better performance. Each rule check runs independently
        and errors are handled gracefully without stopping other rules.
        """
        if not self.tree or not self.collector:
            logger.warning(f"AST tree or collector missing for {self.file_path}")
            return

        try:
            # Define built-in rule check functions (all follow RuleChecker protocol)
            rule_checks: list[tuple[str, RuleChecker]] = [
                ("DAG rules", dag_rules.check_all_dag_rules),
                ("Ruff AIR rules", ruff_air_rules.check_all_ruff_air_rules),
                ("airflint rules", airflint_rules.check_all_airflint_rules),
                ("Best Practices rules", best_practices_rules.check_all_best_practices_rules),
            ]

            # Load and add plugin rules
            plugin_rules = load_plugins()
            rule_checks.extend(plugin_rules)

            # Execute rules in parallel using ThreadPoolExecutor
            logger.debug("Checking rules in parallel")
            with ThreadPoolExecutor(max_workers=len(rule_checks)) as executor:
                # Submit all rule checks
                future_to_rule = {
                    executor.submit(check_func, self.collector, self.file_path): rule_name
                    for rule_name, check_func in rule_checks
                }

                # Collect results as they complete
                for future in as_completed(future_to_rule):
                    rule_name = future_to_rule[future]
                    try:
                        logger.debug(f"Checking {rule_name}")
                        issues = future.result()
                        self.issues.extend(issues)
                        logger.debug(f"Completed {rule_name}: found {len(issues)} issues")
                    except (AttributeError, TypeError, KeyError, IndexError) as e:
                        # AST data access errors
                        logger.exception(
                            f"AST data access error when applying {rule_name} for {self.file_path}: {e}"
                        )
                        # Don't add issue to avoid duplicating errors
                    except Exception as e:
                        # Unexpected rule errors
                        logger.exception(
                            f"Unexpected error applying {rule_name} for {self.file_path}: {e}"
                        )
                        # Don't add issue to avoid duplicating errors
        except (KeyboardInterrupt, SystemExit):
            # System exceptions should not be caught
            raise
        except Exception as e:
            # Last catch-all only for unexpected executor errors
            logger.exception(
                f"Unexpected error in parallel rule execution for {self.file_path}: {e}"
            )
            # Don't add issue to avoid duplicating errors
