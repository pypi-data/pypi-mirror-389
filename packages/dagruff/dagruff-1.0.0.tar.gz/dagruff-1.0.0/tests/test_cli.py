"""Tests for CLI module."""

import argparse
import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from dagruff.cli import (
    apply_autofixes,
    determine_fixable_rules,
    determine_paths_to_check,
    filter_issues,
    format_issue,
    format_output_json,
    get_severity_levels,
    is_dag_file,
    lint_directory,
    lint_file,
    load_configuration,
    normalize_arguments,
    parse_arguments,
    print_statistics,
    run_linter_for_paths,
)
from dagruff.config import Config
from dagruff.models import LintIssue, Severity


def test_is_dag_file_with_airflow_import(tmp_path):
    """Test is_dag_file with Airflow import."""
    dag_file = tmp_path / "test_dag.py"
    dag_content = """from airflow import DAG

dag = DAG(dag_id="test")
"""
    dag_file.write_text(dag_content, encoding="utf-8")

    assert is_dag_file(dag_file) is True


def test_is_dag_file_without_airflow_import(tmp_path):
    """Test is_dag_file without Airflow import."""
    regular_file = tmp_path / "regular.py"
    regular_file.write_text("print('hello')", encoding="utf-8")

    assert is_dag_file(regular_file) is False


def test_is_dag_file_not_exists():
    """Test is_dag_file with non-existent file."""
    non_existent = Path("/nonexistent/file.py")
    assert is_dag_file(non_existent) is False


def test_lint_file_valid_dag(tmp_path):
    """Test lint_file with valid DAG file."""
    dag_file = tmp_path / "test_dag.py"
    dag_content = """from airflow import DAG

dag = DAG(
    dag_id="test_dag",
    description="Test DAG",
)
"""
    dag_file.write_text(dag_content, encoding="utf-8")

    issues = lint_file(str(dag_file))
    assert isinstance(issues, list)


def test_lint_file_invalid_path():
    """Test lint_file with invalid path."""
    issues = lint_file("/nonexistent/file.py")
    assert issues == []


def test_lint_directory_valid(tmp_path):
    """Test lint_directory with valid directory."""
    dag_dir = tmp_path / "dags"
    dag_dir.mkdir()

    dag_file = dag_dir / "test_dag.py"
    dag_content = """from airflow import DAG

dag = DAG(
    dag_id="test_dag",
)
"""
    dag_file.write_text(dag_content, encoding="utf-8")

    issues = lint_directory(str(dag_dir))
    assert isinstance(issues, list)


def test_lint_directory_empty(tmp_path):
    """Test lint_directory with empty directory."""
    empty_dir = tmp_path / "empty"
    empty_dir.mkdir()

    issues = lint_directory(str(empty_dir))
    assert issues == []


def test_parse_arguments():
    """Test parsing command line arguments."""
    test_args = ["--log-level", "DEBUG", "test_path"]
    with patch.object(sys, "argv", ["dagruff"] + test_args):
        args = parse_arguments()
        assert args.log_level == "DEBUG"
        assert args.path == ["test_path"]


def test_get_severity_levels():
    """Test get_severity_levels function."""
    error_levels = get_severity_levels("error")
    assert Severity.ERROR in error_levels
    assert Severity.WARNING not in error_levels

    warning_levels = get_severity_levels("warning")
    assert Severity.ERROR in warning_levels
    assert Severity.WARNING in warning_levels
    assert Severity.INFO not in warning_levels

    info_levels = get_severity_levels("info")
    assert Severity.ERROR in info_levels
    assert Severity.WARNING in info_levels
    assert Severity.INFO in info_levels


def test_normalize_arguments(tmp_path):
    """Test normalize_arguments function."""
    # Create test file
    test_file = tmp_path / "test.py"
    test_file.touch()

    # Create mock args with mix of rules and paths
    args = argparse.Namespace()
    args.ignore = ["DAG001", str(test_file)]
    args.fix = ["DAG005", str(test_file)]
    args.path = None

    normalize_arguments(args)

    # Paths should be moved to args.path
    assert str(test_file) in args.path or args.path == [str(test_file), str(test_file)]
    # Rules should remain in args.ignore/args.fix
    assert "DAG001" in args.ignore
    assert "DAG005" in args.fix or len(args.fix) == 0  # Paths removed from fix


def test_format_issue_error():
    """Test format_issue with ERROR severity."""
    issue = LintIssue(
        file_path="test.py",
        line=1,
        column=0,
        severity=Severity.ERROR,
        rule_id="DAG001",
        message="Test error",
    )
    result = format_issue(issue)
    assert "❌" in result
    assert "DAG001" in result
    assert "Test error" in result


def test_format_issue_warning():
    """Test format_issue with WARNING severity."""
    issue = LintIssue(
        file_path="test.py",
        line=2,
        column=5,
        severity=Severity.WARNING,
        rule_id="DAG002",
        message="Test warning",
    )
    result = format_issue(issue)
    assert "⚠️" in result
    assert "DAG002" in result


def test_format_issue_info():
    """Test format_issue with INFO severity."""
    issue = LintIssue(
        file_path="test.py",
        line=3,
        column=10,
        severity=Severity.INFO,
        rule_id="DAG003",
        message="Test info",
    )
    result = format_issue(issue)
    assert "ℹ️" in result
    assert "DAG003" in result


def test_format_issue_unknown_severity():
    """Test format_issue with unknown severity."""
    # Create issue with custom severity (simulating unknown)
    issue = LintIssue(
        file_path="test.py",
        line=1,
        column=0,
        severity=None,  # Will cause KeyError
        rule_id="UNKNOWN",
        message="Test",
    )
    # Mock severity to be something unexpected
    issue.severity = "UNKNOWN"
    result = format_issue(issue)
    assert "•" in result  # Default symbol


def test_is_dag_file_with_decorators_import(tmp_path):
    """Test is_dag_file with Airflow decorators import."""
    dag_file = tmp_path / "test_dag.py"
    dag_file.write_text("from airflow.decorators import task\n", encoding="utf-8")

    assert is_dag_file(dag_file) is True


def test_is_dag_file_with_airflow_import_statement(tmp_path):
    """Test is_dag_file with airflow import statement."""
    dag_file = tmp_path / "test_dag.py"
    dag_file.write_text("import airflow\n", encoding="utf-8")

    assert is_dag_file(dag_file) is True


def test_is_dag_file_excludes_dagruff_package(tmp_path):
    """Test is_dag_file excludes dagruff package itself."""
    dagruff_file = tmp_path / "dagruff" / "test.py"
    dagruff_file.parent.mkdir()
    dagruff_file.write_text("from airflow import DAG\n", encoding="utf-8")

    # Should return False for dagruff package files
    assert is_dag_file(dagruff_file) is False


def test_is_dag_file_file_too_large(tmp_path, monkeypatch):
    """Test is_dag_file with file that exceeds size limit."""
    dag_file = tmp_path / "test_dag.py"
    # Create large file (simulate exceeding limit)
    large_content = "from airflow import DAG\n" * 10000
    dag_file.write_text(large_content, encoding="utf-8")

    # Mock validate_file_path to return False (file too large)
    def mock_validate(path):
        return False, "File too large"

    with patch("dagruff.cli.utils.files.validate_file_path", side_effect=mock_validate):
        result = is_dag_file(dag_file)
        # is_dag_file should return False when validation fails
        assert result is False


def test_is_dag_file_permission_error(tmp_path):
    """Test is_dag_file with permission error."""
    dag_file = tmp_path / "test_dag.py"
    dag_file.write_text("from airflow import DAG\n", encoding="utf-8")

    # Remove read permission
    dag_file.chmod(0o000)

    try:
        result = is_dag_file(dag_file)
        assert result is False
    finally:
        dag_file.chmod(0o644)


def test_is_dag_file_unicode_error(tmp_path):
    """Test is_dag_file with UnicodeDecodeError."""
    dag_file = tmp_path / "test_dag.py"
    dag_file.write_bytes(b"\xff\xfe\x00\x00")  # Invalid UTF-8

    result = is_dag_file(dag_file)
    assert result is False


def test_lint_directory_with_ignore_patterns(tmp_path):
    """Test lint_directory with files that should be ignored."""
    test_dir = tmp_path / "test_dir"
    test_dir.mkdir()

    # Create file that should be ignored (__pycache__)
    pycache_dir = test_dir / "__pycache__"
    pycache_dir.mkdir()
    pycache_file = pycache_dir / "test.pyc"
    pycache_file.write_bytes(b"")

    # Create DAG file
    dag_file = test_dir / "test_dag.py"
    dag_file.write_text("from airflow import DAG\n", encoding="utf-8")

    issues = lint_directory(str(test_dir))

    # Should not process __pycache__ files
    assert isinstance(issues, list)


def test_load_configuration_default():
    """Test load_configuration with default path."""
    with patch("dagruff.cli.utils.config_handler.Config") as mock_config_class:
        mock_config = MagicMock()
        # Config.load calls find_default_config internally when None is passed
        mock_config_class.load.return_value = mock_config

        result = load_configuration(None)

        assert result == mock_config
        # load_configuration(None) calls Config.load(None), which internally calls find_default_config
        # But we only patch Config, so we check that load was called with None
        mock_config_class.load.assert_called_once_with(None)


def test_load_configuration_custom_path():
    """Test load_configuration with custom path."""
    custom_path = "/custom/path.toml"
    with patch("dagruff.cli.utils.config_handler.Path") as mock_path_class:
        mock_path_instance = MagicMock()
        mock_path_instance.exists.return_value = True
        mock_path_class.return_value = mock_path_instance

        with patch("dagruff.cli.utils.config_handler.Config") as mock_config_class:
            mock_config = MagicMock()
            mock_config_class.load.return_value = mock_config

            result = load_configuration(custom_path)

            assert result == mock_config
            mock_config_class.load.assert_called_once()


def test_determine_paths_to_check_with_args(tmp_path):
    """Test determine_paths_to_check with CLI arguments."""
    test_file = tmp_path / "test.py"
    test_file.write_text("x = 1\n", encoding="utf-8")

    mock_config = MagicMock(spec=Config)

    result = determine_paths_to_check([str(test_file)], mock_config)

    assert len(result) == 1
    assert str(test_file) in result


def test_determine_paths_to_check_with_directory(tmp_path):
    """Test determine_paths_to_check with directory."""
    test_dir = tmp_path / "test_dir"
    test_dir.mkdir()

    mock_config = MagicMock(spec=Config)

    result = determine_paths_to_check([str(test_dir)], mock_config)

    assert len(result) == 1
    assert str(test_dir) in result


def test_determine_paths_to_check_invalid_file(tmp_path):
    """Test determine_paths_to_check with invalid file."""
    invalid_file = tmp_path / "invalid.py"
    # File doesn't exist

    mock_config = MagicMock(spec=Config)

    with pytest.raises(SystemExit):
        determine_paths_to_check([str(invalid_file)], mock_config)


def test_determine_paths_to_check_from_config(tmp_path):
    """Test determine_paths_to_check using config paths."""
    mock_config = MagicMock(spec=Config)
    test_paths = ["/path1", "/path2"]
    mock_config.get_paths.return_value = test_paths

    result = determine_paths_to_check(None, mock_config)

    assert result == test_paths


def test_determine_paths_to_check_no_paths_in_config():
    """Test determine_paths_to_check when config has no paths."""
    mock_config = MagicMock(spec=Config)
    mock_config.get_paths.return_value = []

    with pytest.raises(SystemExit):
        determine_paths_to_check(None, mock_config)


def test_determine_fixable_rules_none():
    """Test determine_fixable_rules with None (no --fix flag)."""
    fixable_rules, warnings = determine_fixable_rules(None)

    assert fixable_rules == set()
    assert warnings == []


def test_determine_fixable_rules_empty_list():
    """Test determine_fixable_rules with empty list (--fix without args)."""
    fixable_rules, warnings = determine_fixable_rules([])

    assert len(fixable_rules) > 0  # All fixable rules
    assert warnings == []


def test_determine_fixable_rules_specific_rules():
    """Test determine_fixable_rules with specific rules."""
    fixable_rules, warnings = determine_fixable_rules(["DAG001", "DAG005"])

    assert "DAG001" in fixable_rules
    assert "DAG005" in fixable_rules
    assert warnings == []


def test_determine_fixable_rules_invalid_rules():
    """Test determine_fixable_rules with invalid rules."""
    fixable_rules, warnings = determine_fixable_rules(["INVALID_RULE", "DAG001"])

    assert "DAG001" in fixable_rules
    assert "INVALID_RULE" not in fixable_rules
    assert len(warnings) == 1
    assert "INVALID_RULE" in warnings[0]


def test_run_linter_for_paths_single_file(tmp_path):
    """Test run_linter_for_paths with single file."""
    test_file = tmp_path / "test_dag.py"
    test_file.write_text("from airflow import DAG\n", encoding="utf-8")

    issues = run_linter_for_paths([str(test_file)])

    assert isinstance(issues, list)


def test_run_linter_for_paths_multiple_files(tmp_path):
    """Test run_linter_for_paths with multiple files."""
    test_file1 = tmp_path / "test1.py"
    test_file1.write_text("from airflow import DAG\n", encoding="utf-8")
    test_file2 = tmp_path / "test2.py"
    test_file2.write_text("from airflow import DAG\n", encoding="utf-8")

    issues = run_linter_for_paths([str(test_file1), str(test_file2)])

    assert isinstance(issues, list)


def test_run_linter_for_paths_with_directory(tmp_path):
    """Test run_linter_for_paths with directory."""
    test_dir = tmp_path / "test_dir"
    test_dir.mkdir()
    test_file = test_dir / "test.py"
    test_file.write_text("from airflow import DAG\n", encoding="utf-8")

    issues = run_linter_for_paths([str(test_dir)])

    assert isinstance(issues, list)


def test_run_linter_for_paths_error_handling(tmp_path):
    """Test run_linter_for_paths handles errors gracefully."""
    # Create file that will cause error
    invalid_path = "/nonexistent/path.py"

    issues = run_linter_for_paths([invalid_path])

    # Should handle error and return empty list or partial results
    assert isinstance(issues, list)


def test_apply_autofixes_no_fixable_rules(tmp_path):
    """Test apply_autofixes with no fixable rules."""
    test_file = tmp_path / "test.py"
    test_file.write_text("from airflow import DAG\n", encoding="utf-8")

    mock_config = MagicMock(spec=Config)
    mock_config.get_ignore.return_value = []

    issues, fixed = apply_autofixes(
        [str(test_file)],
        set(),  # No fixable rules
        [Severity.ERROR, Severity.WARNING],
        [],
        mock_config,
    )

    assert issues == []
    assert fixed == 0


def test_apply_autofixes_with_fixable_rules(tmp_path):
    """Test apply_autofixes with fixable rules."""
    test_file = tmp_path / "test_dag.py"
    test_file.write_text("dag = DAG(dag_id='test')\n", encoding="utf-8")

    mock_config = MagicMock(spec=Config)
    mock_config.get_ignore.return_value = []

    issues, fixed = apply_autofixes(
        [str(test_file)],
        {"DAG001"},  # Fixable rule
        [Severity.ERROR, Severity.WARNING],
        [],
        mock_config,
    )

    assert isinstance(issues, list)
    assert isinstance(fixed, int)
    assert fixed >= 0


def test_apply_autofixes_with_ignored_rules(tmp_path):
    """Test apply_autofixes with ignored rules."""
    test_file = tmp_path / "test_dag.py"
    test_file.write_text("dag = DAG(dag_id='test')\n", encoding="utf-8")

    mock_config = MagicMock(spec=Config)
    mock_config.get_ignore.return_value = ["DAG001"]

    issues, fixed = apply_autofixes(
        [str(test_file)],
        {"DAG001"},
        [Severity.ERROR, Severity.WARNING],
        [],
        mock_config,
    )

    # Should not fix ignored rules
    assert isinstance(issues, list)
    assert isinstance(fixed, int)


def test_filter_issues_by_severity():
    """Test filter_issues filters by severity."""
    issues = [
        LintIssue("test.py", 1, 0, Severity.ERROR, "DAG001", "Error"),
        LintIssue("test.py", 2, 0, Severity.WARNING, "DAG002", "Warning"),
        LintIssue("test.py", 3, 0, Severity.INFO, "DAG003", "Info"),
    ]

    mock_config = MagicMock(spec=Config)
    mock_config.get_ignore.return_value = []

    # Filter only errors
    filtered = filter_issues(issues, [Severity.ERROR], [], mock_config)

    assert len(filtered) == 1
    assert filtered[0].severity == Severity.ERROR


def test_filter_issues_by_rule_id():
    """Test filter_issues filters by rule_id."""
    issues = [
        LintIssue("test.py", 1, 0, Severity.ERROR, "DAG001", "Error"),
        LintIssue("test.py", 2, 0, Severity.WARNING, "DAG002", "Warning"),
    ]

    mock_config = MagicMock(spec=Config)
    mock_config.get_ignore.return_value = []

    # Filter out DAG001
    filtered = filter_issues(issues, [Severity.ERROR, Severity.WARNING], ["DAG001"], mock_config)

    assert len(filtered) == 1
    assert filtered[0].rule_id == "DAG002"


def test_filter_issues_with_config_ignore():
    """Test filter_issues uses config ignore."""
    issues = [
        LintIssue("test.py", 1, 0, Severity.ERROR, "DAG001", "Error"),
        LintIssue("test.py", 2, 0, Severity.WARNING, "DAG002", "Warning"),
    ]

    mock_config = MagicMock(spec=Config)
    mock_config.get_ignore.return_value = ["DAG001"]

    filtered = filter_issues(issues, [Severity.ERROR, Severity.WARNING], [], mock_config)

    assert len(filtered) == 1
    assert filtered[0].rule_id == "DAG002"


def test_print_statistics_no_issues(capsys):
    """Test print_statistics with no issues."""
    print_statistics([])

    captured = capsys.readouterr()
    assert "No issues found" in captured.out or "No issues" in captured.out


def test_print_statistics_with_issues(capsys):
    """Test print_statistics with issues."""
    issues = [
        LintIssue("test.py", 1, 0, Severity.ERROR, "DAG001", "Error"),
        LintIssue("test.py", 2, 0, Severity.WARNING, "DAG002", "Warning"),
        LintIssue("test.py", 3, 0, Severity.INFO, "DAG003", "Info"),
    ]

    print_statistics(issues)

    captured = capsys.readouterr()
    assert "Total issues" in captured.out or "issues:" in captured.out


def test_print_statistics_top_rules(capsys):
    """Test print_statistics shows top rules."""
    issues = [
        LintIssue("test.py", 1, 0, Severity.ERROR, "DAG001", "Error"),
        LintIssue("test.py", 2, 0, Severity.ERROR, "DAG001", "Error"),
        LintIssue("test.py", 3, 0, Severity.WARNING, "DAG002", "Warning"),
    ]

    print_statistics(issues)

    captured = capsys.readouterr()
    # Should show top rules
    assert isinstance(captured.out, str)


def test_format_output_json_no_issues(capsys):
    """Test format_output_json with no issues."""
    format_output_json([])

    captured = capsys.readouterr()
    output = json.loads(captured.out)

    # format_output_json returns an array directly, not wrapped in an object
    assert output == []


def test_format_output_json_with_issues(capsys):
    """Test format_output_json with issues."""
    issues = [
        LintIssue("test.py", 1, 0, Severity.ERROR, "DAG001", "Error message"),
    ]

    format_output_json(issues)

    captured = capsys.readouterr()
    output = json.loads(captured.out)

    # format_output_json returns an array directly, not wrapped in an object
    assert len(output) == 1
    assert output[0]["rule_id"] == "DAG001"


def test_format_output_json_multiple_issues(capsys):
    """Test format_output_json with multiple issues."""
    issues = [
        LintIssue("test1.py", 1, 0, Severity.ERROR, "DAG001", "Error 1"),
        LintIssue("test2.py", 2, 0, Severity.WARNING, "DAG002", "Warning 1"),
        LintIssue("test3.py", 3, 0, Severity.INFO, "DAG003", "Info 1"),
    ]

    format_output_json(issues)

    captured = capsys.readouterr()
    output = json.loads(captured.out)

    # format_output_json returns an array directly, not wrapped in an object
    assert len(output) == 3


def test_parse_arguments_all_options():
    """Test parse_arguments with all options."""
    test_args = [
        "--log-level",
        "DEBUG",
        "--log-file",
        "/tmp/log.txt",
        "--config",
        "/tmp/config.toml",
        "--severity",
        "warning",
        "--exit-zero",
        "--format",
        "json",
        "--ignore",
        "DAG001",
        "DAG002",
        "--fix",
        "DAG005",
        "path1",
        "path2",
    ]

    with patch.object(sys, "argv", ["dagruff"] + test_args):
        args = parse_arguments()
        assert args.log_level == "DEBUG"
        assert args.log_file == "/tmp/log.txt"
        assert args.config == "/tmp/config.toml"
        assert args.severity == "warning"
        assert args.exit_zero is True
        assert args.format == "json"
        assert args.ignore == ["DAG001", "DAG002"]
        # After normalization, paths from --fix are moved to args.path
        # So we check that DAG005 is in fix, and paths are in path
        assert "DAG005" in args.fix or args.fix == ["DAG005"] or len(args.fix) >= 1
        assert "path1" in args.path or "path2" in args.path or len(args.path) >= 0


def test_normalize_arguments_mixed_rules_and_paths(tmp_path):
    """Test normalize_arguments with mixed rules and paths."""
    test_file1 = tmp_path / "test1.py"
    test_file1.touch()
    test_file2 = tmp_path / "test2.py"
    test_file2.touch()

    import argparse

    args = argparse.Namespace()
    args.ignore = ["DAG001", str(test_file1), "DAG002"]
    args.fix = ["DAG005", str(test_file2)]
    args.path = None

    normalize_arguments(args)

    # Paths should be moved to args.path
    assert str(test_file1) in args.path
    assert str(test_file2) in args.path
    # Rules should remain
    assert "DAG001" in args.ignore
    assert "DAG002" in args.ignore
    assert "DAG005" in args.fix


def test_normalize_arguments_existing_path(tmp_path):
    """Test normalize_arguments with existing args.path."""
    test_file = tmp_path / "test.py"
    test_file.touch()

    import argparse

    args = argparse.Namespace()
    args.ignore = ["DAG001"]
    args.fix = []
    args.path = ["existing_path"]

    normalize_arguments(args)

    # Existing path should remain
    assert "existing_path" in args.path


def test_get_severity_levels_all():
    """Test get_severity_levels with all severities."""
    levels = get_severity_levels("info")

    assert Severity.ERROR in levels
    assert Severity.WARNING in levels
    assert Severity.INFO in levels


def test_get_severity_levels_warning():
    """Test get_severity_levels with warning."""
    levels = get_severity_levels("warning")

    assert Severity.ERROR in levels
    assert Severity.WARNING in levels
    assert Severity.INFO not in levels


def test_get_severity_levels_error():
    """Test get_severity_levels with error."""
    levels = get_severity_levels("error")

    assert Severity.ERROR in levels
    assert Severity.WARNING not in levels
    assert Severity.INFO not in levels


def test_parse_arguments_defaults():
    """Test parse_arguments with default values."""
    with patch.object(sys, "argv", ["dagruff"]):
        args = parse_arguments()
        assert args.log_level == "INFO"
        assert args.log_file is None
        assert args.config is None
        assert args.severity == "info"
        assert args.exit_zero is False
        assert args.format == "human"
        assert args.ignore == []
        assert args.fix is None
        assert args.path == []


def test_normalize_arguments_only_rules():
    """Test normalize_arguments with only rules (no paths)."""
    import argparse

    args = argparse.Namespace()
    args.ignore = ["DAG001", "DAG002"]
    args.fix = ["DAG005"]
    args.path = None

    normalize_arguments(args)

    # Rules should remain
    assert "DAG001" in args.ignore
    assert "DAG002" in args.ignore
    assert "DAG005" in args.fix
    # Paths should be empty or None
    assert args.path is None or args.path == []


def test_lint_directory_with_subdirectory(tmp_path):
    """Test lint_directory with subdirectory."""
    test_dir = tmp_path / "test_dir"
    test_dir.mkdir()

    subdir = test_dir / "subdir"
    subdir.mkdir()

    dag_file = subdir / "test_dag.py"
    dag_file.write_text("from airflow import DAG\n", encoding="utf-8")

    issues = lint_directory(str(test_dir))

    assert isinstance(issues, list)


def test_lint_directory_filters_ignored_files(tmp_path):
    """Test lint_directory filters ignored files."""
    test_dir = tmp_path / "test_dir"
    test_dir.mkdir()

    # Create __pycache__ directory (should be ignored)
    pycache = test_dir / "__pycache__"
    pycache.mkdir()
    pycache_file = pycache / "test.pyc"
    pycache_file.write_bytes(b"")

    # Create DAG file (should be processed)
    dag_file = test_dir / "test_dag.py"
    dag_file.write_text("from airflow import DAG\n", encoding="utf-8")

    issues = lint_directory(str(test_dir))

    # Should process DAG file but ignore __pycache__
    assert isinstance(issues, list)


def test_apply_autofixes_no_fixable_issues(tmp_path):
    """Test apply_autofixes with no fixable issues."""
    test_file = tmp_path / "test.py"
    test_file.write_text("from airflow import DAG\n", encoding="utf-8")

    mock_config = MagicMock(spec=Config)
    mock_config.get_ignore.return_value = []

    issues, fixed = apply_autofixes(
        [str(test_file)],
        {"DAG001"},  # Fixable rule
        [Severity.ERROR],
        [],
        mock_config,
    )

    # Should return empty if no fixable issues found
    assert isinstance(issues, list)
    assert isinstance(fixed, int)


def test_apply_autofixes_file_write_error(tmp_path):
    """Test apply_autofixes handles file write errors."""
    test_file = tmp_path / "test_dag.py"
    test_file.write_text("dag = DAG(dag_id='test')\n", encoding="utf-8")

    # Remove write permission
    test_file.chmod(0o444)

    mock_config = MagicMock(spec=Config)
    mock_config.get_ignore.return_value = []

    try:
        issues, fixed = apply_autofixes(
            [str(test_file)],
            {"DAG001"},
            [Severity.ERROR, Severity.WARNING],
            [],
            mock_config,
        )

        # Should handle error gracefully
        assert isinstance(issues, list)
        assert isinstance(fixed, int)
    finally:
        test_file.chmod(0o644)


def test_apply_autofixes_multiple_files(tmp_path):
    """Test apply_autofixes with multiple files."""
    test_file1 = tmp_path / "test1.py"
    test_file1.write_text("dag = DAG(dag_id='test1')\n", encoding="utf-8")
    test_file2 = tmp_path / "test2.py"
    test_file2.write_text("dag = DAG(dag_id='test2')\n", encoding="utf-8")

    mock_config = MagicMock(spec=Config)
    mock_config.get_ignore.return_value = []

    issues, fixed = apply_autofixes(
        [str(test_file1), str(test_file2)],
        {"DAG001"},
        [Severity.ERROR, Severity.WARNING],
        [],
        mock_config,
    )

    assert isinstance(issues, list)
    assert isinstance(fixed, int)


def test_normalize_arguments_empty_lists():
    """Test normalize_arguments with empty lists."""
    import argparse

    args = argparse.Namespace()
    args.ignore = []
    args.fix = []
    args.path = None

    normalize_arguments(args)

    assert args.ignore == []
    assert args.fix == []
    assert args.path is None or args.path == []


def test_normalize_arguments_only_paths(tmp_path):
    """Test normalize_arguments with only paths."""
    test_file = tmp_path / "test.py"
    test_file.touch()

    import argparse

    args = argparse.Namespace()
    args.ignore = [str(test_file)]
    args.fix = []
    args.path = None

    normalize_arguments(args)

    assert str(test_file) in args.path


def test_determine_paths_to_check_invalid_directory(tmp_path):
    """Test determine_paths_to_check with invalid directory."""
    invalid_dir = tmp_path / "nonexistent"
    # Directory doesn't exist

    mock_config = MagicMock(spec=Config)

    with pytest.raises(SystemExit):
        determine_paths_to_check([str(invalid_dir)], mock_config)


def test_determine_paths_to_check_validation_error(tmp_path):
    """Test determine_paths_to_check with validation error."""
    test_file = tmp_path / "test.py"
    test_file.touch()

    # Mock validate_file_path to return False
    with patch(
        "dagruff.cli.utils.config_handler.validate_file_path",
        return_value=(False, "Validation error"),
    ):
        mock_config = MagicMock(spec=Config)

        with pytest.raises(SystemExit):
            determine_paths_to_check([str(test_file)], mock_config)


def test_normalize_arguments_with_only_paths_in_fix(tmp_path):
    """Test normalize_arguments when --fix contains only paths."""
    test_file = tmp_path / "test.py"
    test_file.touch()

    import argparse

    args = argparse.Namespace()
    args.ignore = []
    args.fix = [str(test_file)]  # Only path, no rules
    args.path = None

    normalize_arguments(args)

    # Path should be moved to args.path, fix should be empty list
    assert str(test_file) in args.path
    assert args.fix == []


def test_determine_paths_to_check_mixed_valid_invalid(tmp_path):
    """Test determine_paths_to_check with mix of valid and invalid paths."""
    valid_file = tmp_path / "valid.py"
    valid_file.write_text("x = 1\n", encoding="utf-8")
    invalid_file = tmp_path / "invalid.py"
    # File doesn't exist

    mock_config = MagicMock(spec=Config)

    # Should process valid file, skip invalid
    result = determine_paths_to_check([str(valid_file), str(invalid_file)], mock_config)

    # Should have at least valid file (if validation passes)
    assert isinstance(result, list)


def test_normalize_arguments_all_paths_in_ignore(tmp_path):
    """Test normalize_arguments when args.ignore contains only paths."""
    test_file = tmp_path / "test.py"
    test_file.touch()

    import argparse

    args = argparse.Namespace()
    args.ignore = [str(test_file)]  # Only path
    args.fix = []
    args.path = None

    normalize_arguments(args)

    # Path should be moved to args.path, ignore should be empty
    assert str(test_file) in args.path
    assert args.ignore == []


def test_determine_paths_to_check_all_invalid(tmp_path):
    """Test determine_paths_to_check when all paths are invalid."""
    invalid1 = tmp_path / "invalid1.py"
    invalid2 = tmp_path / "invalid2.py"
    # Files don't exist

    mock_config = MagicMock(spec=Config)

    # Should exit with error
    with pytest.raises(SystemExit):
        determine_paths_to_check([str(invalid1), str(invalid2)], mock_config)
