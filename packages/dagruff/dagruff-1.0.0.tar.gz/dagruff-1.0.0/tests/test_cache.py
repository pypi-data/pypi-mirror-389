"""Tests for cache module."""

import pytest

from dagruff.cache import LinterCache
from dagruff.models import LintIssue, Severity


@pytest.fixture
def temp_file(tmp_path):
    """Create a temporary file for testing."""
    test_file = tmp_path / "test_dag.py"
    test_file.write_text("from airflow import DAG\n", encoding="utf-8")
    return test_file


@pytest.fixture
def cache():
    """Create a cache instance for testing."""
    return LinterCache(enabled=True)


def test_cache_enabled():
    """Test cache is enabled by default."""
    cache = LinterCache(enabled=True)
    assert cache.enabled is True


def test_cache_disabled():
    """Test cache can be disabled."""
    cache = LinterCache(enabled=False)
    assert cache.enabled is False


def test_cache_get_miss(temp_file, cache):
    """Test cache returns None for cache miss."""
    result = cache.get(str(temp_file))
    assert result is None


def test_cache_set_and_get(temp_file, cache):
    """Test cache stores and retrieves issues."""
    issues = [
        LintIssue(
            file_path=str(temp_file),
            line=1,
            column=0,
            severity=Severity.ERROR,
            rule_id="DAG001",
            message="Test issue",
        )
    ]

    # Set cache
    cache.set(str(temp_file), issues)

    # Get from cache
    cached_issues = cache.get(str(temp_file))

    assert cached_issues is not None
    assert len(cached_issues) == 1
    assert cached_issues[0].rule_id == "DAG001"


def test_cache_invalidates_on_file_change(temp_file, cache):
    """Test cache invalidates when file changes."""
    issues = [
        LintIssue(
            file_path=str(temp_file),
            line=1,
            column=0,
            severity=Severity.ERROR,
            rule_id="DAG001",
            message="Test issue",
        )
    ]

    # Set cache
    cache.set(str(temp_file), issues)

    # Verify cache hit
    cached_issues = cache.get(str(temp_file))
    assert cached_issues is not None

    # Modify file
    temp_file.write_text("from airflow import DAG\n# Modified\n", encoding="utf-8")

    # Cache should be invalidated
    cached_issues = cache.get(str(temp_file))
    assert cached_issues is None


def test_cache_disabled_returns_none(temp_file, cache):
    """Test cache returns None when disabled."""
    cache.enabled = False

    issues = [
        LintIssue(
            file_path=str(temp_file),
            line=1,
            column=0,
            severity=Severity.ERROR,
            rule_id="DAG001",
            message="Test issue",
        )
    ]

    # Set cache (should not cache)
    cache.set(str(temp_file), issues)

    # Get from cache (should return None)
    cached_issues = cache.get(str(temp_file))
    assert cached_issues is None


def test_cache_clear_all(temp_file, cache):
    """Test clearing all cache."""
    issues = [
        LintIssue(
            file_path=str(temp_file),
            line=1,
            column=0,
            severity=Severity.ERROR,
            rule_id="DAG001",
            message="Test issue",
        )
    ]

    # Set cache
    cache.set(str(temp_file), issues)

    # Verify cache hit
    assert cache.get(str(temp_file)) is not None

    # Clear all cache
    cache.clear()

    # Verify cache miss
    assert cache.get(str(temp_file)) is None


def test_cache_clear_specific_file(temp_file, cache):
    """Test clearing cache for specific file."""
    test_file2 = temp_file.parent / "test2.py"
    test_file2.write_text("from airflow import DAG\n", encoding="utf-8")

    issues1 = [
        LintIssue(
            file_path=str(temp_file),
            line=1,
            column=0,
            severity=Severity.ERROR,
            rule_id="DAG001",
            message="Test issue 1",
        )
    ]

    issues2 = [
        LintIssue(
            file_path=str(test_file2),
            line=1,
            column=0,
            severity=Severity.ERROR,
            rule_id="DAG002",
            message="Test issue 2",
        )
    ]

    # Set cache for both files
    cache.set(str(temp_file), issues1)
    cache.set(str(test_file2), issues2)

    # Verify both cached
    assert cache.get(str(temp_file)) is not None
    assert cache.get(str(test_file2)) is not None

    # Clear cache for one file
    cache.clear(str(temp_file))

    # Verify only one cleared
    assert cache.get(str(temp_file)) is None
    assert cache.get(str(test_file2)) is not None


def test_cache_get_stats(cache):
    """Test cache statistics."""
    stats = cache.get_stats()

    assert "size" in stats
    assert "enabled" in stats
    assert stats["size"] == 0
    assert stats["enabled"] is True


def test_cache_stats_with_entries(temp_file, cache):
    """Test cache statistics with entries."""
    issues = [
        LintIssue(
            file_path=str(temp_file),
            line=1,
            column=0,
            severity=Severity.ERROR,
            rule_id="DAG001",
            message="Test issue",
        )
    ]

    cache.set(str(temp_file), issues)

    stats = cache.get_stats()
    assert stats["size"] == 1


def test_cache_returns_copy(temp_file, cache):
    """Test cache returns a copy to prevent modification."""
    issues = [
        LintIssue(
            file_path=str(temp_file),
            line=1,
            column=0,
            severity=Severity.ERROR,
            rule_id="DAG001",
            message="Test issue",
        )
    ]

    cache.set(str(temp_file), issues)

    # Get from cache
    cached_issues = cache.get(str(temp_file))
    assert cached_issues is not None

    # Modify cached issues
    cached_issues[0].rule_id = "MODIFIED"

    # Get again - should still have original
    cached_issues2 = cache.get(str(temp_file))
    assert cached_issues2[0].rule_id == "DAG001"


def test_cache_nonexistent_file(cache):
    """Test cache handles nonexistent file."""
    nonexistent = "/nonexistent/file.py"

    # Should not cache
    issues = [
        LintIssue(
            file_path=nonexistent,
            line=1,
            column=0,
            severity=Severity.ERROR,
            rule_id="DAG001",
            message="Test issue",
        )
    ]

    cache.set(nonexistent, issues)

    # Should return None
    result = cache.get(nonexistent)
    assert result is None


def test_cache_invalidate_version(cache, temp_file):
    """Test cache version invalidation."""
    issues = [
        LintIssue(
            file_path=str(temp_file),
            line=1,
            column=0,
            severity=Severity.ERROR,
            rule_id="DAG001",
            message="Test issue",
        )
    ]

    # Set cache
    cache.set(str(temp_file), issues)

    # Verify cache hit
    assert cache.get(str(temp_file)) is not None

    # Invalidate version
    cache.invalidate_version()

    # Cache should be cleared
    assert cache.get(str(temp_file)) is None
