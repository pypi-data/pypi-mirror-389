import pytest

from auth_proxy.auth_plugins.base import AuthPlugin


class MinimalPlugin(AuthPlugin):
    """Minimal implementation of AuthPlugin for testing."""

    def authenticate(self, request_headers, path):
        return True

    def get_auth_headers(self, request_headers, path):
        return {}


def test_plugin_base_class():
    """Test that the base plugin class requires implementation of abstract methods."""
    # Should be able to instantiate a class that implements the abstract methods
    plugin = MinimalPlugin({})
    assert isinstance(plugin, AuthPlugin)

    # Should not be able to instantiate the base class directly
    with pytest.raises(TypeError):
        AuthPlugin({})

    # Should not be able to instantiate a class that doesn't implement the abstract methods
    class IncompletePlugin(AuthPlugin):
        pass

    with pytest.raises(TypeError):
        IncompletePlugin({})


def test_plugin_config_storage():
    """Test that plugins store their configuration."""
    config = {"key": "value"}
    plugin = MinimalPlugin(config)
    assert plugin.config == config
