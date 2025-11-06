"""Module for linter configuration management."""

import re
import sys
from pathlib import Path
from typing import Optional

from dagruff.logger import get_logger

logger = get_logger(__name__)

# Pattern for valid rule IDs (DAGxxx, AIRxxx, AFxxx, AIRFLINTxxx, BPxxx, etc.)
RULE_ID_PATTERN = re.compile(r"^[A-Z]+\d{3,}$")


def validate_paths(paths: any) -> list[str]:
    """Validate and normalize paths from configuration.

    Args:
        paths: Configuration value for paths (should be list of strings)

    Returns:
        Validated list of path strings

    Raises:
        ValueError: If paths is not a valid list of strings
    """
    if not isinstance(paths, list):
        raise ValueError(f"paths must be a list, got {type(paths).__name__}")

    validated_paths = []
    for i, path in enumerate(paths):
        if not isinstance(path, str):
            raise ValueError(f"paths[{i}] must be a string, got {type(path).__name__}")

        # Strip whitespace
        path = path.strip()

        # Check for empty strings
        if not path:
            logger.warning(f"Empty path at index {i} in configuration, skipping")
            continue

        validated_paths.append(path)

    return validated_paths


def validate_ignore(ignore: any) -> list[str]:
    """Validate and normalize ignore rules from configuration.

    Args:
        ignore: Configuration value for ignore (should be list of rule IDs)

    Returns:
        Validated list of rule ID strings

    Raises:
        ValueError: If ignore is not a valid list of strings
    """
    if not isinstance(ignore, list):
        raise ValueError(f"ignore must be a list, got {type(ignore).__name__}")

    validated_ignore = []
    for i, rule_id in enumerate(ignore):
        if not isinstance(rule_id, str):
            raise ValueError(f"ignore[{i}] must be a string, got {type(rule_id).__name__}")

        # Strip whitespace
        rule_id = rule_id.strip()

        # Check for empty strings
        if not rule_id:
            logger.warning(f"Empty rule ID at index {i} in configuration, skipping")
            continue

        # Warn about invalid rule ID format (but don't fail)
        if not RULE_ID_PATTERN.match(rule_id):
            logger.warning(
                f"Rule ID '{rule_id}' at index {i} does not match expected format "
                "(should be like DAG001, AIR002, etc.), but will be used anyway"
            )

        validated_ignore.append(rule_id)

    return validated_ignore


class Config:
    """Class for reading and working with configuration."""

    DEFAULT_CONFIG_NAME = ".dagruff.toml"
    PYPROJECT_CONFIG_SECTION = "tool.dagruff"

    def __init__(self, config_path: Optional[Path] = None):
        """Initialize configuration."""
        self.config_path = config_path
        self.paths: list[str] = []
        self.ignore: list[str] = []

    @classmethod
    def find_default_config(cls) -> Optional[Path]:
        """Search for default config in current directory and parent directories."""
        current_dir = Path.cwd()

        # Check current directory and all parent directories
        for directory in [current_dir] + list(current_dir.parents):
            # Check .dagruff.toml
            config_file = directory / cls.DEFAULT_CONFIG_NAME
            if config_file.exists() and config_file.is_file():
                return config_file

            # Check pyproject.toml
            pyproject_file = directory / "pyproject.toml"
            if pyproject_file.exists() and pyproject_file.is_file():
                return pyproject_file

        return None

    @classmethod
    def load(cls, config_path: Optional[Path] = None) -> "Config":
        """Load configuration from file."""
        config = cls(config_path)

        # If path not specified, find default config
        if config_path is None:
            config_path = cls.find_default_config()

        if config_path is None:
            # Config not found, return empty configuration
            return config

        config.config_path = config_path

        try:
            # Python 3.11+ uses tomllib, older versions need tomli
            if sys.version_info >= (3, 11):
                import tomllib

                with open(config_path, "rb") as f:
                    data = tomllib.load(f)
            else:
                import tomli

                with open(config_path, "rb") as f:
                    data = tomli.load(f)

            # Read from .dagruff.toml or from pyproject.toml
            if config_path.name == "pyproject.toml":
                # Read from tool.dagruff section
                if "tool" in data and "dagruff" in data["tool"]:
                    dag_config = data["tool"]["dagruff"]
                    if "paths" in dag_config:
                        try:
                            config.paths = validate_paths(dag_config["paths"])
                        except ValueError as e:
                            logger.warning(f"Invalid paths configuration: {e}, using empty list")
                            config.paths = []
                    if "ignore" in dag_config:
                        try:
                            config.ignore = validate_ignore(dag_config["ignore"])
                        except ValueError as e:
                            logger.warning(f"Invalid ignore configuration: {e}, using empty list")
                            config.ignore = []
            else:
                # Read from .dagruff.toml
                # Can be root level or section
                if "tool" in data and "dagruff" in data["tool"]:
                    dag_config = data["tool"]["dagruff"]
                    if "paths" in dag_config:
                        try:
                            config.paths = validate_paths(dag_config["paths"])
                        except ValueError as e:
                            logger.warning(f"Invalid paths configuration: {e}, using empty list")
                            config.paths = []
                    if "ignore" in dag_config:
                        try:
                            config.ignore = validate_ignore(dag_config["ignore"])
                        except ValueError as e:
                            logger.warning(f"Invalid ignore configuration: {e}, using empty list")
                            config.ignore = []
                else:
                    # If no tool section, check root level
                    if "paths" in data:
                        try:
                            config.paths = validate_paths(data["paths"])
                        except ValueError as e:
                            logger.warning(f"Invalid paths configuration: {e}, using empty list")
                            config.paths = []
                    if "ignore" in data:
                        try:
                            config.ignore = validate_ignore(data["ignore"])
                        except ValueError as e:
                            logger.warning(f"Invalid ignore configuration: {e}, using empty list")
                            config.ignore = []

        except FileNotFoundError:
            logger.debug(f"Configuration file not found: {config_path}")
        except ImportError as e:
            logger.debug(f"Module for reading TOML not installed: {e}")
        except (OSError, PermissionError) as e:
            # Configuration file access errors
            logger.warning(
                f"Error accessing configuration file {config_path}: {str(e)}", exc_info=True
            )
            # Return empty configuration to continue working
        except (ValueError, KeyError, TypeError) as e:
            # Configuration parsing or format errors
            logger.warning(f"Configuration format error in {config_path}: {str(e)}", exc_info=True)
            # Return empty configuration to continue working
        except (KeyboardInterrupt, SystemExit):
            # System exceptions should not be caught
            raise
        except Exception as e:
            # Last catch-all only for unexpected errors
            logger.warning(
                f"Unexpected error reading configuration from {config_path}: {str(e)}",
                exc_info=True,
            )
            # Return empty configuration to continue working

        return config

    def get_paths(self) -> list[str]:
        """Get paths for checking from configuration."""
        return self.paths.copy()

    def get_ignore(self) -> list[str]:
        """Get list of rules to ignore from configuration."""
        return self.ignore.copy()
