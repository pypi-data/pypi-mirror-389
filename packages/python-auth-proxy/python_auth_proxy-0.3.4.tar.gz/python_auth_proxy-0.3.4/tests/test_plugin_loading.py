from unittest.mock import MagicMock, patch

from auth_proxy.auth_plugins import PLUGIN_REGISTRY, create_plugin_instance
from auth_proxy.auth_plugins.base import AuthPlugin


class DummyPlugin(AuthPlugin):
    """Test plugin for testing."""

    def __init__(self, config):
        super().__init__(config)
        self.test_value = config.get("test_value", "default")

    def authenticate(self, request_headers, path):
        return True

    def get_auth_headers(self, request_headers, path):
        return {"X-Test": self.test_value}


def test_create_plugin_instance():
    """Test creating a plugin instance."""
    # Register the test plugin
    PLUGIN_REGISTRY["test"] = DummyPlugin

    # Create an instance
    plugin = create_plugin_instance("test", {"test_value": "custom"})

    # Check instance type and configuration
    assert isinstance(plugin, DummyPlugin)
    assert plugin.test_value == "custom"


# Update other tests to use DummyPlugin instead of TestPlugin
def test_create_named_plugin_instance():
    """Test creating a named plugin instance."""
    # Register the test plugin
    PLUGIN_REGISTRY["test"] = DummyPlugin

    # Create a named instance
    plugin = create_plugin_instance(
        "custom-test", {"type": "test", "test_value": "named"}
    )

    # Check instance type and configuration
    assert isinstance(plugin, DummyPlugin)
    assert plugin.test_value == "named"


def test_load_plugins_from_entry_points():
    """Test loading plugins from entry points."""
    from auth_proxy.auth_plugins import load_plugins_from_entry_points

    # Mock entry points
    mock_entry_point = MagicMock()
    mock_entry_point.name = "entry-test"
    mock_entry_point.load.return_value = DummyPlugin

    with patch("importlib.metadata.entry_points", return_value=[mock_entry_point]):
        # Load plugins from entry points
        load_plugins_from_entry_points()

        # Check that the plugin was registered
        assert "entry-test" in PLUGIN_REGISTRY
        assert PLUGIN_REGISTRY["entry-test"] == DummyPlugin
