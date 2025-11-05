import os
import tempfile
from typing import Any, Dict, List, Optional, Tuple

import pytest
import yaml

from auth_proxy.auth_plugins.base import AuthPlugin, AuthResult, PluginPath
from auth_proxy.config import ProxyConfig
from auth_proxy.proxy import AuthProxy


class MockAuthPlugin(AuthPlugin):
    """Mock authentication plugin for testing."""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.should_authenticate = config.get("should_authenticate", True)
        self.auth_headers = config.get("auth_headers", {"X-Auth-User": "test-user"})
        self.should_redirect = config.get("should_redirect", False)
        self.redirect_url = config.get("redirect_url", "/login")

    def authenticate(self, request_headers: Dict[str, str], path: str) -> AuthResult:
        """Authenticate a request."""
        if self.should_redirect:
            return AuthResult(
                authenticated=False,
                redirect_url=self.redirect_url,
                redirect_status_code=302,
            )

        return AuthResult(
            authenticated=self.should_authenticate,
            headers=self.auth_headers.copy() if self.should_authenticate else {},
        )

    def get_auth_headers(
        self, request_headers: Dict[str, str], path: str
    ) -> Dict[str, str]:
        """Get headers to add to the authenticated request."""
        return self.auth_headers.copy() if self.should_authenticate else {}

    def get_plugin_paths(self) -> List[PluginPath]:
        """Get paths that this plugin needs to handle."""
        return [
            PluginPath(
                path="/auth/mock/callback",
                regex=False,
                authenticate=False,
                description="Mock callback endpoint",
            )
        ]

    def handle_plugin_path(
        self, path: str, request_headers: Dict[str, str], request_body: bytes
    ) -> Optional[Tuple[int, Dict[str, str], bytes]]:
        """Handle a request to a plugin-specific path."""
        if path.startswith("/auth/mock/callback"):
            return (200, {"Content-Type": "application/json"}, b'{"status": "success"}')

        return None


@pytest.fixture
def temp_config_file():
    """Create a temporary config file for testing."""
    with tempfile.NamedTemporaryFile(mode="w+", suffix=".yaml", delete=False) as f:
        yield f.name
    # Clean up after the test
    os.unlink(f.name)


@pytest.fixture
def basic_config():
    """Return a basic configuration dictionary."""
    return {
        "listen": {"host": "127.0.0.1", "port": 8000},
        "backend": {"host": "localhost", "port": 3000},
        "auth_plugins": {
            "mock": {
                "should_authenticate": True,
                "auth_headers": {"X-Auth-User": "test-user"},
            }
        },
        "auth": {
            "default_plugins": ["mock"],
            "default_mode": "any",
            "default_behavior": "authenticated",
        },
        "paths": [
            {"path": "/api/", "authenticate": True, "plugins": ["mock"]},
            {"path": "/public/", "authenticate": False},
        ],
    }


@pytest.fixture
def regex_config():
    """Return a configuration with regex path rules."""
    return {
        "listen": {"host": "127.0.0.1", "port": 8000},
        "backend": {"host": "localhost", "port": 3000},
        "auth_plugins": {
            "mock": {"should_authenticate": True},
            "mock-admin": {
                "type": "mock",
                "should_authenticate": True,
                "auth_headers": {"X-Auth-User": "admin", "X-Auth-Role": "admin"},
            },
        },
        "auth": {
            "default_plugins": ["mock"],
            "default_mode": "any",
            "default_behavior": "authenticated",
        },
        "paths": [
            {"path": "^/api/v1/public/.*$", "regex": True, "authenticate": False},
            {
                "path": "^/api/v1/admin/.*$",
                "regex": True,
                "authenticate": True,
                "plugins": ["mock-admin"],
            },
            {
                "path": "^/api/v1/.*$",
                "regex": True,
                "authenticate": True,
                "plugins": ["mock"],
            },
        ],
    }


@pytest.fixture
def config_file(temp_config_file, basic_config):
    """Create a config file with basic configuration."""
    with open(temp_config_file, "w") as f:
        yaml.dump(basic_config, f)
    return temp_config_file


@pytest.fixture
def regex_config_file(temp_config_file, regex_config):
    """Create a config file with regex configuration."""
    with open(temp_config_file, "w") as f:
        yaml.dump(regex_config, f)
    return temp_config_file


@pytest.fixture
def proxy_config(config_file):
    """Create a ProxyConfig instance."""
    return ProxyConfig(config_file)


@pytest.fixture
def regex_proxy_config(regex_config_file):
    """Create a ProxyConfig instance with regex rules."""
    return ProxyConfig(regex_config_file)


@pytest.fixture
def auth_proxy(basic_config):
    """Create an AuthProxy instance."""
    # Register the mock plugin
    from auth_proxy.auth_plugins import PLUGIN_REGISTRY

    PLUGIN_REGISTRY["mock"] = MockAuthPlugin

    return AuthProxy(basic_config)


@pytest.fixture
def regex_auth_proxy(regex_config):
    """Create an AuthProxy instance with regex rules."""
    # Register the mock plugin
    from auth_proxy.auth_plugins import PLUGIN_REGISTRY

    PLUGIN_REGISTRY["mock"] = MockAuthPlugin

    return AuthProxy(regex_config)
