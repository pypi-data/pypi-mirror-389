"""Tests for dagruff.rules.base module."""

import ast

from dagruff.models import LintIssue, Severity
from dagruff.rules.ast_collector import ASTCollector
from dagruff.rules.base import RuleChecker


def test_rule_checker_protocol():
    """Test RuleChecker protocol compliance."""

    def check_test_rule(collector: ASTCollector, file_path: str) -> list[LintIssue]:
        """Test rule checker function."""
        issues = []
        if not collector.has_dag_import():
            issues.append(
                LintIssue(
                    file_path=file_path,
                    line=1,
                    column=0,
                    severity=Severity.INFO,
                    rule_id="TEST001",
                    message="Test issue found",
                )
            )
        return issues

    # Check that function follows RuleChecker protocol
    assert isinstance(check_test_rule, RuleChecker)

    # Test that function can be called with correct parameters

    code = "x = 1"
    tree = ast.parse(code)
    collector = ASTCollector(tree)
    collector.collect()

    issues = check_test_rule(collector, "test.py")

    assert isinstance(issues, list)
    assert len(issues) == 1
    assert issues[0].rule_id == "TEST001"


def test_rule_checker_protocol_no_issues():
    """Test RuleChecker protocol with no issues."""

    def check_test_rule(collector: ASTCollector, file_path: str) -> list[LintIssue]:
        """Test rule checker function that returns no issues."""
        return []

    assert isinstance(check_test_rule, RuleChecker)

    code = "from airflow import DAG"
    tree = ast.parse(code)
    collector = ASTCollector(tree)
    collector.collect()

    issues = check_test_rule(collector, "test.py")

    assert isinstance(issues, list)
    assert len(issues) == 0


def test_rule_checker_protocol_multiple_issues():
    """Test RuleChecker protocol with multiple issues."""

    def check_test_rule(collector: ASTCollector, file_path: str) -> list[LintIssue]:
        """Test rule checker function that returns multiple issues."""
        issues = []
        issues.append(
            LintIssue(
                file_path=file_path,
                line=1,
                column=0,
                severity=Severity.WARNING,
                rule_id="TEST001",
                message="Test issue 1",
            )
        )
        issues.append(
            LintIssue(
                file_path=file_path,
                line=2,
                column=0,
                severity=Severity.ERROR,
                rule_id="TEST002",
                message="Test issue 2",
            )
        )
        return issues

    assert isinstance(check_test_rule, RuleChecker)

    code = "x = 1"
    tree = ast.parse(code)
    collector = ASTCollector(tree)
    collector.collect()

    issues = check_test_rule(collector, "test.py")

    assert isinstance(issues, list)
    assert len(issues) == 2
    assert issues[0].rule_id == "TEST001"
    assert issues[1].rule_id == "TEST002"
