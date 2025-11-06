"""Tests for validation module."""

from pathlib import Path

import pytest

from dagruff.validation import (
    MAX_FILE_SIZE_BYTES,
    MAX_FILE_SIZE_MB,
    sanitize_path,
    validate_directory_path,
    validate_encoding,
    validate_file_path,
)


def test_validate_file_path_exists(tmp_path):
    """Test validation of existing file."""
    test_file = tmp_path / "test.py"
    test_file.write_text("print('test')")

    is_valid, error_msg = validate_file_path(str(test_file))
    assert is_valid is True
    assert error_msg is None


def test_validate_file_path_not_exists():
    """Test validation of non-existent file."""
    is_valid, error_msg = validate_file_path("/nonexistent/file.py")
    assert is_valid is False
    assert "does not exist" in error_msg


def test_validate_file_path_is_directory(tmp_path):
    """Test validation when path is directory, not file."""
    is_valid, error_msg = validate_file_path(str(tmp_path))
    assert is_valid is False
    assert "not a file" in error_msg


def test_validate_file_path_too_large(tmp_path):
    """Test validation of file exceeding size limit."""
    test_file = tmp_path / "large.py"
    # Create file larger than MAX_FILE_SIZE_MB
    large_content = "x" * (MAX_FILE_SIZE_BYTES + 1)
    test_file.write_text(large_content)

    is_valid, error_msg = validate_file_path(str(test_file))
    assert is_valid is False
    assert "too large" in error_msg
    assert str(MAX_FILE_SIZE_MB) in error_msg


def test_validate_file_path_no_permission(tmp_path):
    """Test validation of file without read permission."""
    test_file = tmp_path / "test.py"
    test_file.write_text("print('test')")

    # Remove read permission
    test_file.chmod(0o000)
    try:
        is_valid, error_msg = validate_file_path(str(test_file))
        assert is_valid is False
        assert "read permission" in error_msg.lower()
    finally:
        # Restore permission
        test_file.chmod(0o644)


def test_validate_directory_path_exists(tmp_path):
    """Test validation of existing directory."""
    is_valid, error_msg = validate_directory_path(str(tmp_path))
    assert is_valid is True
    assert error_msg is None


def test_validate_directory_path_not_exists():
    """Test validation of non-existent directory."""
    is_valid, error_msg = validate_directory_path("/nonexistent/directory")
    assert is_valid is False
    assert "does not exist" in error_msg


def test_validate_directory_path_is_file(tmp_path):
    """Test validation when path is file, not directory."""
    test_file = tmp_path / "test.py"
    test_file.write_text("print('test')")

    is_valid, error_msg = validate_directory_path(str(test_file))
    assert is_valid is False
    assert "not a directory" in error_msg


def test_validate_directory_path_no_permission(tmp_path):
    """Test validation of directory without read permission."""
    test_dir = tmp_path / "test_dir"
    test_dir.mkdir()

    # Remove read permission
    test_dir.chmod(0o000)
    try:
        is_valid, error_msg = validate_directory_path(str(test_dir))
        assert is_valid is False
        assert "read permission" in error_msg.lower()
    finally:
        # Restore permission
        test_dir.chmod(0o755)


def test_sanitize_path_valid(tmp_path):
    """Test sanitization of valid path."""
    test_file = tmp_path / "test.py"
    test_file.write_text("print('test')")

    sanitized = sanitize_path(str(test_file))
    assert sanitized == str(test_file.resolve())


def test_sanitize_path_relative():
    """Test sanitization of relative path."""
    # Test with current directory
    Path.cwd()
    sanitized = sanitize_path("test.py")
    # Should resolve to absolute path
    assert Path(sanitized).is_absolute()


def test_sanitize_path_dangerous_component():
    """Test sanitization with dangerous path components."""
    with pytest.raises(ValueError, match="dangerous component"):
        sanitize_path("/path/../dangerous/file.py")

    with pytest.raises(ValueError, match="dangerous component"):
        sanitize_path("~/file.py")


def test_validate_encoding_valid(tmp_path):
    """Test encoding validation for valid UTF-8 file."""
    test_file = tmp_path / "test.py"
    test_file.write_text("# -*- coding: utf-8 -*-\nprint('test')", encoding="utf-8")

    is_valid, error_msg = validate_encoding(str(test_file))
    assert is_valid is True
    assert error_msg is None


def test_validate_encoding_invalid(tmp_path):
    """Test encoding validation for file with invalid encoding."""
    test_file = tmp_path / "test.py"
    # Write binary data that's not valid UTF-8
    test_file.write_bytes(b"\xff\xfe\x00\x00")

    is_valid, error_msg = validate_encoding(str(test_file))
    assert is_valid is False
    assert "encoding" in error_msg.lower()


def test_validate_encoding_file_not_exists():
    """Test encoding validation for non-existent file."""
    is_valid, error_msg = validate_encoding("/nonexistent/file.py")
    assert is_valid is False
    assert error_msg is not None
