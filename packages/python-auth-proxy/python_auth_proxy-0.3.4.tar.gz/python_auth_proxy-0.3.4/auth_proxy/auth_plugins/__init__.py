import importlib.metadata
import logging
import sys
from typing import Any, Dict, Iterable, Type

from auth_proxy.auth_plugins.base import AuthPlugin

logger = logging.getLogger(__name__)

# Registry of available plugin types
PLUGIN_REGISTRY: Dict[str, Type[AuthPlugin]] = {}


def load_plugins_from_entry_points() -> None:
    """
    Discover and load authentication plugins from entry points.

    Looks for entry points in the 'auth_proxy.plugins' group.
    Each entry point should point to a class that inherits from AuthPlugin.
    """
    try:
        # Get entry points for our plugin group
        entry_points: Iterable[Any] = []

        try:
            entry_points = importlib.metadata.entry_points(group="auth_proxy.plugins")  # type: ignore
        except Exception as e:
            logger.error(f"Error getting entry points: {e}")

        # Process each entry point
        for entry_point in entry_points:
            try:
                # Get plugin information
                plugin_name: str
                plugin_class: Any

                # Modern EntryPoint object
                if hasattr(entry_point, "name") and hasattr(entry_point, "load"):
                    plugin_name = entry_point.name
                    plugin_class = entry_point.load()
                    plugin_value = getattr(entry_point, "value", str(entry_point))
                # Legacy EntryPoint format (unlikely, but just in case)
                elif isinstance(entry_point, tuple) and len(entry_point) >= 2:
                    plugin_name = str(entry_point[0])
                    plugin_value = str(entry_point[1])
                    # This is a bit of a hack, but should work for legacy formats
                    if hasattr(entry_point, "load"):
                        plugin_class = entry_point.load()
                    else:
                        logger.error(
                            f"Cannot load plugin from entry point: {entry_point}"
                        )
                        continue
                else:
                    logger.error(f"Unknown entry point format: {entry_point}")
                    continue

                # Ensure the plugin is a subclass of AuthPlugin
                if not isinstance(plugin_class, type) or not issubclass(
                    plugin_class, AuthPlugin
                ):
                    logger.warning(
                        f"Plugin '{plugin_name}' from '{plugin_value}' "
                        f"is not a subclass of AuthPlugin. Skipping."
                    )
                    continue

                # Register the plugin
                PLUGIN_REGISTRY[plugin_name] = plugin_class
                logger.info(f"Loaded authentication plugin: {plugin_name}")
            except Exception as e:
                logger.error(f"Error loading plugin: {e}")
    except Exception as e:
        logger.error(f"Error discovering plugins: {e}")


def create_plugin_instance(name: str, config: Dict[str, Any]) -> AuthPlugin:
    """
    Create an instance of an authentication plugin.

    Args:
        name: The name of the plugin instance
        config: Configuration for the plugin instance

    Returns:
        An instance of the requested plugin

    Raises:
        ValueError: If the plugin type is not found
    """
    # Get the plugin type - either explicitly specified or same as name
    plugin_type = config.get("type", name)

    # Pass the name to the plugin config
    config["_name"] = name

    if plugin_type not in PLUGIN_REGISTRY:
        raise ValueError(f"Authentication plugin type '{plugin_type}' not found")

    plugin_class = PLUGIN_REGISTRY[plugin_type]
    return plugin_class(config)


# Load plugins when this module is imported
load_plugins_from_entry_points()
