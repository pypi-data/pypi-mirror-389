"""Tests for configuration module."""

import pytest

from dagruff.config import Config, validate_ignore, validate_paths


def test_config_load_none():
    """Test loading configuration without file."""
    config = Config.load(None)
    assert config.paths == []
    assert config.ignore == []


def test_config_find_default(tmp_path, monkeypatch):
    """Test finding default config file."""
    # Create temporary config
    config_file = tmp_path / ".dagruff.toml"
    config_file.write_text('[tool.dagruff]\npaths = ["dags/"]\n')

    # Change working directory
    monkeypatch.chdir(tmp_path)

    found = Config.find_default_config()
    assert found is not None
    assert found.name == ".dagruff.toml"


def test_config_load_toml(tmp_path):
    """Test loading configuration from TOML file."""
    config_file = tmp_path / ".dagruff.toml"
    config_content = """[tool.dagruff]
paths = ["dags/", "scripts/"]
ignore = ["DAG001", "DAG002"]
"""
    config_file.write_text(config_content)

    config = Config.load(config_file)
    assert len(config.paths) == 2
    assert "dags/" in config.paths
    assert "scripts/" in config.paths
    assert len(config.ignore) == 2
    assert "DAG001" in config.ignore
    assert "DAG002" in config.ignore


def test_config_load_pyproject(tmp_path):
    """Test loading configuration from pyproject.toml."""
    config_file = tmp_path / "pyproject.toml"
    config_content = """[tool.dagruff]
paths = ["dags/"]
ignore = ["DAG001"]
"""
    config_file.write_text(config_content)

    config = Config.load(config_file)
    assert len(config.paths) == 1
    assert "dags/" in config.paths
    assert "DAG001" in config.ignore


def test_config_load_invalid_format(tmp_path):
    """Test loading configuration with invalid format."""
    config_file = tmp_path / ".dagruff.toml"
    config_content = """invalid toml format {"""
    config_file.write_text(config_content)

    # Should return empty config without raising exception
    config = Config.load(config_file)
    assert config.paths == []
    assert config.ignore == []


def test_config_get_paths():
    """Test getting paths from configuration."""
    config = Config(None)
    config.paths = ["dags/", "scripts/"]

    paths = config.get_paths()
    assert paths == ["dags/", "scripts/"]
    # Should return a copy, not reference
    paths.append("test/")
    assert "test/" not in config.paths


def test_config_get_ignore():
    """Test getting ignore list from configuration."""
    config = Config(None)
    config.ignore = ["DAG001", "DAG002"]

    ignore = config.get_ignore()
    assert ignore == ["DAG001", "DAG002"]
    # Should return a copy, not reference
    ignore.append("DAG003")
    assert "DAG003" not in config.ignore


def test_config_load_pyproject_toml(tmp_path):
    """Test Config.load with pyproject.toml."""
    config_file = tmp_path / "pyproject.toml"
    config_content = """
[tool.dagruff]
paths = ["/path/to/dags"]
ignore = ["DAG001"]
"""
    config_file.write_text(config_content, encoding="utf-8")

    config = Config.load(str(config_file))

    assert config is not None


def test_config_default_config():
    """Test Config with default configuration."""
    config = Config()

    # Should have default values
    assert isinstance(config.get_paths(), list)
    assert isinstance(config.get_ignore(), list)


def test_config_default_init():
    """Test Config default initialization."""
    config = Config(None)

    assert config.paths == []
    assert config.ignore == []


def test_config_get_paths_copy():
    """Test Config.get_paths returns copy."""
    config = Config(None)
    config.paths = ["path1", "path2"]

    paths = config.get_paths()
    paths.append("path3")

    # Original should not be modified
    assert "path3" not in config.paths
    assert len(config.paths) == 2


def test_config_get_ignore_copy():
    """Test Config.get_ignore returns copy."""
    config = Config(None)
    config.ignore = ["DAG001", "DAG002"]

    ignore = config.get_ignore()
    ignore.append("DAG003")

    # Original should not be modified
    assert "DAG003" not in config.ignore
    assert len(config.ignore) == 2


def test_config_load_nonexistent_file(tmp_path):
    """Test Config.load with non-existent file."""
    nonexistent = tmp_path / "nonexistent.toml"

    # Should return default config
    config = Config.load(str(nonexistent))

    assert config is not None
    assert isinstance(config, Config)


def test_config_load_empty_file(tmp_path):
    """Test Config.load with empty file."""
    empty_file = tmp_path / "empty.toml"
    empty_file.write_text("", encoding="utf-8")

    config = Config.load(str(empty_file))

    assert config is not None
    assert isinstance(config, Config)


def test_config_load_malformed_toml(tmp_path):
    """Test Config.load with malformed TOML."""
    malformed_file = tmp_path / "malformed.toml"
    malformed_file.write_text("invalid toml {", encoding="utf-8")

    # Should handle gracefully
    config = Config.load(str(malformed_file))

    assert config is not None
    assert isinstance(config, Config)


def test_config_find_default_config(tmp_path, monkeypatch):
    """Test Config.find_default_config finds config."""
    config_file = tmp_path / ".dagruff.toml"
    config_file.write_text('[tool.dagruff]\npaths = ["dags/"]\n', encoding="utf-8")

    monkeypatch.chdir(tmp_path)

    found = Config.find_default_config()

    assert found is not None
    assert found.name == ".dagruff.toml"


def test_validate_paths_valid():
    """Test validate_paths with valid input."""
    paths = ["dags/", "scripts/", "tests/"]
    validated = validate_paths(paths)

    assert validated == paths
    assert len(validated) == 3


def test_validate_paths_not_list():
    """Test validate_paths with non-list input."""
    with pytest.raises(ValueError, match="paths must be a list"):
        validate_paths("not a list")


def test_validate_paths_non_string_element():
    """Test validate_paths with non-string element."""
    with pytest.raises(ValueError, match="paths\\[0\\] must be a string"):
        validate_paths([123, "valid"])


def test_validate_paths_empty_strings():
    """Test validate_paths with empty strings."""
    paths = ["dags/", "", "  ", "scripts/"]
    validated = validate_paths(paths)

    # Empty and whitespace-only strings should be skipped
    assert len(validated) == 2
    assert "dags/" in validated
    assert "scripts/" in validated


def test_validate_paths_whitespace():
    """Test validate_paths strips whitespace."""
    paths = ["  dags/  ", "  scripts/  "]
    validated = validate_paths(paths)

    assert validated == ["dags/", "scripts/"]


def test_validate_ignore_valid():
    """Test validate_ignore with valid input."""
    ignore = ["DAG001", "DAG002", "AIR003"]
    validated = validate_ignore(ignore)

    assert validated == ignore
    assert len(validated) == 3


def test_validate_ignore_not_list():
    """Test validate_ignore with non-list input."""
    with pytest.raises(ValueError, match="ignore must be a list"):
        validate_ignore("not a list")


def test_validate_ignore_non_string_element():
    """Test validate_ignore with non-string element."""
    with pytest.raises(ValueError, match="ignore\\[0\\] must be a string"):
        validate_ignore([123, "DAG001"])


def test_validate_ignore_empty_strings():
    """Test validate_ignore with empty strings."""
    ignore = ["DAG001", "", "  ", "DAG002"]
    validated = validate_ignore(ignore)

    # Empty and whitespace-only strings should be skipped
    assert len(validated) == 2
    assert "DAG001" in validated
    assert "DAG002" in validated


def test_validate_ignore_whitespace():
    """Test validate_ignore strips whitespace."""
    ignore = ["  DAG001  ", "  DAG002  "]
    validated = validate_ignore(ignore)

    assert validated == ["DAG001", "DAG002"]


def test_validate_ignore_invalid_format():
    """Test validate_ignore with invalid rule ID format."""
    # Should not raise, but log warning
    ignore = ["DAG001", "invalid_rule", "DAG002"]
    validated = validate_ignore(ignore)

    # All should be included (warning logged, but not failed)
    assert len(validated) == 3
    assert "DAG001" in validated
    assert "invalid_rule" in validated
    assert "DAG002" in validated


def test_config_load_invalid_paths_type(tmp_path):
    """Test Config.load with invalid paths type."""
    config_file = tmp_path / ".dagruff.toml"
    config_content = """[tool.dagruff]
paths = "not a list"
ignore = ["DAG001"]
"""
    config_file.write_text(config_content)

    # Should handle gracefully and use empty list
    config = Config.load(config_file)
    assert config.paths == []
    assert config.ignore == ["DAG001"]


def test_config_load_invalid_ignore_type(tmp_path):
    """Test Config.load with invalid ignore type."""
    config_file = tmp_path / ".dagruff.toml"
    config_content = """[tool.dagruff]
paths = ["dags/"]
ignore = "not a list"
"""
    config_file.write_text(config_content)

    # Should handle gracefully and use empty list
    config = Config.load(config_file)
    assert config.paths == ["dags/"]
    assert config.ignore == []


def test_config_load_invalid_paths_element(tmp_path):
    """Test Config.load with invalid paths element type."""
    config_file = tmp_path / ".dagruff.toml"
    config_content = """[tool.dagruff]
paths = ["dags/", 123, "scripts/"]
ignore = ["DAG001"]
"""
    config_file.write_text(config_content)

    # Should handle gracefully and use empty list
    config = Config.load(config_file)
    assert config.paths == []
    assert config.ignore == ["DAG001"]


def test_config_load_invalid_ignore_element(tmp_path):
    """Test Config.load with invalid ignore element type."""
    config_file = tmp_path / ".dagruff.toml"
    config_content = """[tool.dagruff]
paths = ["dags/"]
ignore = ["DAG001", 123, "DAG002"]
"""
    config_file.write_text(config_content)

    # Should handle gracefully and use empty list
    config = Config.load(config_file)
    assert config.paths == ["dags/"]
    assert config.ignore == []


def test_config_load_with_empty_paths(tmp_path):
    """Test Config.load with empty paths."""
    config_file = tmp_path / ".dagruff.toml"
    config_content = """[tool.dagruff]
paths = ["dags/", "", "  "]
ignore = ["DAG001"]
"""
    config_file.write_text(config_content)

    config = Config.load(config_file)
    # Empty strings should be filtered out
    assert len(config.paths) == 1
    assert "dags/" in config.paths
    assert config.ignore == ["DAG001"]
