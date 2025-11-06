"""Plugin system for loading custom linting rules."""

import importlib.metadata

from dagruff.logger import get_logger
from dagruff.rules.base import RuleChecker

logger = get_logger(__name__)

# Entry point group name for dagruff plugins
PLUGIN_ENTRY_POINT_GROUP = "dagruff.rules"


def load_plugins() -> list[tuple[str, RuleChecker]]:
    """Load plugin rules from entry points.

    Scans for plugins registered under the 'dagruff.rules' entry point group
    and returns them as a list of (name, checker) tuples.

    Returns:
        List of tuples containing (plugin_name, RuleChecker) for each plugin

    Example:
        Plugin package should register in pyproject.toml:

        [project.entry-points."dagruff.rules"]
        my_custom_rule = "my_package.plugin:check_all_custom_rules"
    """
    plugins: list[tuple[str, RuleChecker]] = []

    try:
        # Try to load entry points (Python 3.10+)
        if hasattr(importlib.metadata, "entry_points"):
            # Python 3.10+
            try:
                eps = importlib.metadata.entry_points(group=PLUGIN_ENTRY_POINT_GROUP)
            except TypeError:
                # Fallback for older Python versions
                eps = importlib.metadata.entry_points().get(PLUGIN_ENTRY_POINT_GROUP, [])

            for ep in eps:
                try:
                    plugin_name = ep.name
                    checker_func = ep.load()

                    # Validate that loaded function follows RuleChecker protocol
                    if not isinstance(checker_func, RuleChecker):
                        logger.warning(
                            f"Plugin '{plugin_name}' does not implement RuleChecker protocol. "
                            f"Skipping."
                        )
                        continue

                    plugins.append((plugin_name, checker_func))
                    logger.debug(f"Loaded plugin rule: {plugin_name}")
                except Exception as e:
                    logger.warning(
                        f"Failed to load plugin '{ep.name}': {e}. Skipping.", exc_info=True
                    )
        else:
            # Fallback for older Python versions
            try:
                eps = importlib.metadata.entry_points().get(PLUGIN_ENTRY_POINT_GROUP, [])
                for ep in eps:
                    try:
                        plugin_name = ep.name
                        checker_func = ep.load()

                        if not isinstance(checker_func, RuleChecker):
                            logger.warning(
                                f"Plugin '{plugin_name}' does not implement RuleChecker protocol. "
                                f"Skipping."
                            )
                            continue

                        plugins.append((plugin_name, checker_func))
                        logger.debug(f"Loaded plugin rule: {plugin_name}")
                    except Exception as e:
                        logger.warning(
                            f"Failed to load plugin '{ep.name}': {e}. Skipping.", exc_info=True
                        )
            except Exception as e:
                logger.debug(f"Could not load entry points: {e}")
    except Exception as e:
        # Gracefully handle any errors during plugin loading
        logger.debug(f"Error loading plugins: {e}")

    if plugins:
        logger.info(f"Loaded {len(plugins)} plugin rule(s)")
    else:
        logger.debug("No plugin rules found")

    return plugins


def get_available_plugins() -> list[str]:
    """Get list of available plugin names.

    Returns:
        List of plugin names that are registered
    """
    plugin_names = []

    try:
        if hasattr(importlib.metadata, "entry_points"):
            try:
                eps = importlib.metadata.entry_points(group=PLUGIN_ENTRY_POINT_GROUP)
            except TypeError:
                eps = importlib.metadata.entry_points().get(PLUGIN_ENTRY_POINT_GROUP, [])
            plugin_names = [ep.name for ep in eps]
        else:
            try:
                eps = importlib.metadata.entry_points().get(PLUGIN_ENTRY_POINT_GROUP, [])
                plugin_names = [ep.name for ep in eps]
            except Exception:
                pass
    except Exception:
        pass

    return plugin_names
