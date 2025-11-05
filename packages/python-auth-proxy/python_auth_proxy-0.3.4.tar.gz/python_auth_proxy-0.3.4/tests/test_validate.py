import io
import sys
from unittest.mock import MagicMock, patch

import pytest

from auth_proxy.validate import find_matching_plugin_path, main, validate_path


def test_find_matching_plugin_path_exact_match():
    """Test finding a matching plugin path with exact match."""
    plugin_paths = {
        "/auth/oidc/callback": {
            "plugin": "oidc",
            "regex": False,
            "authenticate": False,
            "description": "OIDC callback endpoint",
        }
    }

    result = find_matching_plugin_path("/auth/oidc/callback", plugin_paths)
    assert result is not None
    path, info = result
    assert path == "/auth/oidc/callback"
    assert info["plugin"] == "oidc"


def test_find_matching_plugin_path_prefix_match():
    """Test finding a matching plugin path with prefix match."""
    plugin_paths = {
        "/auth/oidc/": {
            "plugin": "oidc",
            "regex": False,
            "authenticate": False,
            "description": "OIDC endpoints",
        }
    }

    result = find_matching_plugin_path("/auth/oidc/callback?code=123", plugin_paths)
    assert result is not None
    path, info = result
    assert path == "/auth/oidc/"
    assert info["plugin"] == "oidc"


def test_find_matching_plugin_path_regex_match():
    """Test finding a matching plugin path with regex match."""
    import re

    plugin_paths = {
        "^/auth/[a-z]+/callback$": {
            "plugin": "oidc",
            "regex": True,
            "authenticate": False,
            "description": "OIDC callback endpoint",
        }
    }

    # Compile the regex pattern for testing
    plugin_paths["^/auth/[a-z]+/callback$"]["pattern"] = re.compile(
        "^/auth/[a-z]+/callback$"
    )

    result = find_matching_plugin_path("/auth/oidc/callback", plugin_paths)
    assert result is not None
    path, info = result
    assert path == "^/auth/[a-z]+/callback$"
    assert info["plugin"] == "oidc"


def test_find_matching_plugin_path_no_match():
    """Test finding a matching plugin path with no match."""
    plugin_paths = {
        "/auth/oidc/callback": {
            "plugin": "oidc",
            "regex": False,
            "authenticate": False,
            "description": "OIDC callback endpoint",
        }
    }

    result = find_matching_plugin_path("/api/resource", plugin_paths)
    assert result is None


def test_validate_path_plugin_path(basic_config):
    """Test validation of a plugin path."""
    # Add a plugin path to the config
    basic_config["auth_plugins"] = {
        "oidc": {
            "issuer": "https://accounts.example.com",
            "client_id": "client123",
            "client_secret": "secret456",
            "callback_path": "/auth/oidc/callback",
        }
    }

    # Patch the print function to capture output
    with patch("builtins.print") as mock_print:
        validate_path(basic_config, "/auth/oidc/callback")

    # Check that the expected output was printed
    mock_print.assert_any_call("Path: /auth/oidc/callback")
    mock_print.assert_any_call("Matching plugin path: /auth/oidc/callback")
    mock_print.assert_any_call("Plugin: oidc")
    mock_print.assert_any_call("Authentication required: False")


def test_validate_path_regular_path_after_checking_plugin_paths(basic_config):
    """Test validation of a regular path after checking plugin paths."""
    # Add a plugin path to the config
    basic_config["auth_plugins"] = {
        "oidc": {
            "issuer": "https://accounts.example.com",
            "client_id": "client123",
            "client_secret": "secret456",
            "callback_path": "/auth/oidc/callback",
        }
    }

    # Patch the print function to capture output
    with patch("builtins.print") as mock_print:
        validate_path(basic_config, "/api/resource")

    # Check that the expected output was printed
    mock_print.assert_any_call("Path: /api/resource")
    mock_print.assert_any_call("Matching rule #1: /api/")
    mock_print.assert_any_call("Authentication required: True")


def test_main_function_with_plugin_path():
    """Test the main function with a plugin path."""
    # Mock command line arguments
    test_args = ["auth-proxy-validate", "-c", "config.yaml", "/auth/oidc/callback"]

    # Mock config file
    mock_config = {
        "auth_plugins": {
            "oidc": {
                "issuer": "https://accounts.example.com",
                "client_id": "client123",
                "client_secret": "secret456",
                "callback_path": "/auth/oidc/callback",
            }
        },
        "paths": [{"path": "/api/", "authenticate": True, "plugins": ["oidc"]}],
    }

    with patch("sys.argv", test_args), patch("builtins.open", MagicMock()), patch(
        "yaml.safe_load", return_value=mock_config
    ), patch("auth_proxy.validate.validate_path") as mock_validate:

        main()

        # Check that validate_path was called with the right arguments
        mock_validate.assert_called_once_with(mock_config, "/auth/oidc/callback")
