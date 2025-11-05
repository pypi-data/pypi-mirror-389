import pytest
import yaml

from auth_proxy.config import ProxyConfig


def test_load_config(config_file):
    """Test loading a configuration file."""
    config = ProxyConfig(config_file)
    assert config.listen["host"] == "127.0.0.1"
    assert config.listen["port"] == 8000
    assert config.backend["host"] == "localhost"
    assert config.backend["port"] == 3000


def test_config_not_found():
    """Test error when config file not found."""
    with pytest.raises(FileNotFoundError):
        ProxyConfig("nonexistent_file.yaml")


def test_invalid_yaml(temp_config_file):
    """Test error with invalid YAML."""
    with open(temp_config_file, "w") as f:
        f.write("invalid: yaml: :")

    with pytest.raises(yaml.YAMLError):
        ProxyConfig(temp_config_file)


def test_auth_plugins_config(proxy_config):
    """Test accessing auth plugins configuration."""
    auth_plugins = proxy_config.auth_plugins
    assert "mock" in auth_plugins
    assert auth_plugins["mock"]["should_authenticate"] is True


def test_paths_config(proxy_config):
    """Test accessing paths configuration."""
    paths = proxy_config.paths
    assert len(paths) == 2
    assert paths[0]["path"] == "/api/"
    assert paths[0]["authenticate"] is True
    assert paths[1]["path"] == "/public/"
    assert paths[1]["authenticate"] is False


def test_auth_config(proxy_config):
    """Test accessing auth configuration."""
    auth = proxy_config.auth
    assert auth["default_plugins"] == ["mock"]
    assert auth["default_mode"] == "any"
    assert auth["default_behavior"] == "authenticated"
