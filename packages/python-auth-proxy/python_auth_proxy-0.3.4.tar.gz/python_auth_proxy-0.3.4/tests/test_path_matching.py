import re

from auth_proxy.proxy import AuthProxy


def test_simple_path_matching(auth_proxy):
    """Test simple prefix path matching."""
    # API path should be authenticated
    rule = auth_proxy._get_path_rule("/api/users")
    assert rule["authenticate"] is True
    assert rule["plugins"] == ["mock"]

    # Public path should not be authenticated
    rule = auth_proxy._get_path_rule("/public/index.html")
    assert rule["authenticate"] is False

    # Unmatched path should use default behavior (authenticated)
    rule = auth_proxy._get_path_rule("/other/path")
    assert rule["authenticate"] is True
    assert rule["plugins"] == ["mock"]


def test_regex_path_matching(regex_auth_proxy):
    """Test regex path matching."""
    # Public API path should not be authenticated
    rule = regex_auth_proxy._get_path_rule("/api/v1/public/data")
    assert rule["authenticate"] is False

    # Admin API path should be authenticated with admin plugin
    rule = regex_auth_proxy._get_path_rule("/api/v1/admin/users")
    assert rule["authenticate"] is True
    assert rule["plugins"] == ["mock-admin"]

    # Regular API path should be authenticated with regular plugin
    rule = regex_auth_proxy._get_path_rule("/api/v1/users")
    assert rule["authenticate"] is True
    assert rule["plugins"] == ["mock"]

    # Unmatched path should use default behavior
    rule = regex_auth_proxy._get_path_rule("/other/path")
    assert rule["authenticate"] is True
    assert rule["plugins"] == ["mock"]


def test_path_rule_precedence(regex_auth_proxy):
    """Test that path rules are processed in order."""
    # This matches both the public and general API rules,
    # but the public rule should take precedence since it's first
    rule = regex_auth_proxy._get_path_rule("/api/v1/public/data")
    assert rule["authenticate"] is False

    # This matches both the admin and general API rules,
    # but the admin rule should take precedence
    rule = regex_auth_proxy._get_path_rule("/api/v1/admin/users")
    assert rule["authenticate"] is True
    assert rule["plugins"] == ["mock-admin"]


def test_regex_compilation():
    """Test that regex patterns are compiled correctly."""
    config = {"paths": [{"path": "^/api/.*$", "regex": True, "authenticate": True}]}

    proxy = AuthProxy(config)

    # The pattern should be compiled
    assert "pattern" in proxy.paths[0]
    assert isinstance(proxy.paths[0]["pattern"], re.Pattern)

    # The pattern should match correctly
    assert proxy.paths[0]["pattern"].match("/api/users")
    assert not proxy.paths[0]["pattern"].match("/other/path")


def test_invalid_regex():
    """Test handling of invalid regex patterns."""
    config = {
        "paths": [{"path": "[invalid[regex", "regex": True, "authenticate": True}],
        "backend": {"host": "localhost", "port": 3000},  # Add backend config
    }

    # Should not raise an exception, but log an error
    proxy = AuthProxy(config)

    # The invalid pattern should be skipped, resulting in an empty paths list
    assert len(proxy.paths) == 0

    # Test that the default path rule works
    rule = proxy._get_path_rule("/test")
    assert rule["authenticate"] is True
