import base64

import bcrypt

from auth_proxy.auth_plugins.basic import BasicAuthPlugin


def test_basic_auth_plugin_init():
    """Test initializing the Basic Auth plugin."""
    config = {"users": {"user1": "password1", "user2": "password2"}}

    plugin = BasicAuthPlugin(config)
    assert plugin.users == config["users"]


def test_basic_auth_authenticate_success():
    """Test successful authentication with Basic Auth."""
    config = {"users": {"user1": "password1"}}

    plugin = BasicAuthPlugin(config)

    # Create Basic Auth header
    auth_value = base64.b64encode(b"user1:password1").decode("utf-8")
    headers = {"Authorization": f"Basic {auth_value}"}

    result = plugin.authenticate(headers, "/api/resource")
    assert result.authenticated is True


def test_basic_auth_authenticate_with_hash():
    """Test authentication with hashed password."""
    # Generate a hashed password
    password = "password1"
    hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    config = {"users": {"user1": hashed}}

    plugin = BasicAuthPlugin(config)

    # Create Basic Auth header with plain text password
    auth_value = base64.b64encode(b"user1:password1").decode("utf-8")
    headers = {"Authorization": f"Basic {auth_value}"}

    result = plugin.authenticate(headers, "/api/resource")
    assert result.authenticated is True


def test_basic_auth_mixed_passwords():
    """Test with mixed plain and hashed passwords when hash_passwords is True."""
    # Generate a hashed password for user1
    hashed = bcrypt.hashpw(b"password1", bcrypt.gensalt()).decode("utf-8")

    config = {
        "users": {
            "user1": hashed,
            "user2": "plainpassword",
        }
    }

    plugin = BasicAuthPlugin(config)

    # Test hashed password user
    auth_value = base64.b64encode(b"user1:password1").decode("utf-8")
    headers = {"Authorization": f"Basic {auth_value}"}
    result = plugin.authenticate(headers, "/api/resource")
    assert result.authenticated is True

    # Test plain password user (should still work with warning)
    auth_value = base64.b64encode(b"user2:plainpassword").decode("utf-8")
    headers = {"Authorization": f"Basic {auth_value}"}
    result = plugin.authenticate(headers, "/api/resource")
    assert result.authenticated is True


def test_basic_auth_authenticate_failure():
    """Test failed authentication with Basic Auth."""
    config = {"users": {"user1": "password1"}}

    plugin = BasicAuthPlugin(config)

    # Wrong password
    auth_value = base64.b64encode(b"user1:wrong").decode("utf-8")
    headers = {"Authorization": f"Basic {auth_value}"}
    result = plugin.authenticate(headers, "/api/resource")
    assert result.authenticated is False

    # Wrong username
    auth_value = base64.b64encode(b"wrong:password1").decode("utf-8")
    headers = {"Authorization": f"Basic {auth_value}"}
    result = plugin.authenticate(headers, "/api/resource")
    assert result.authenticated is False

    # No Authorization header
    result = plugin.authenticate({}, "/api/resource")
    assert result.authenticated is False

    # Wrong Authorization type
    headers = {"Authorization": "Bearer token"}
    result = plugin.authenticate(headers, "/api/resource")
    assert result.authenticated is False


def test_basic_auth_get_headers():
    """Test getting auth headers from Basic Auth plugin."""
    config = {"users": {"user1": "password1"}}

    plugin = BasicAuthPlugin(config)

    # Create Basic Auth header
    auth_value = base64.b64encode(b"user1:password1").decode("utf-8")
    headers = {"Authorization": f"Basic {auth_value}"}

    auth_headers = plugin.get_auth_headers(headers, "/api/resource")
    assert auth_headers["X-Auth-User"] == "user1"

    # No Authorization header
    assert plugin.get_auth_headers({}, "/api/resource") == {}

    # Wrong Authorization type
    headers = {"Authorization": "Bearer token"}
    assert plugin.get_auth_headers(headers, "/api/resource") == {}
