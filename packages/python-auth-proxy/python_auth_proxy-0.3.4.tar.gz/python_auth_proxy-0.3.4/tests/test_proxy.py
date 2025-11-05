from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from tests.conftest import MockAuthPlugin


class StreamWriterMock(MagicMock):
    """Mock for StreamWriter that doesn't return coroutines."""

    def write(self, data):
        return None

    async def drain(self):
        return None

    def close(self):
        return None

    async def wait_closed(self):
        return None


@pytest.mark.asyncio
async def test_authenticate_request_success(auth_proxy):
    """Test successful authentication of a request."""
    headers = {"X-Test": "value"}
    path = "/api/resource"
    path_rule = {"authenticate": True, "plugins": ["mock"]}

    authenticated, auth_headers, redirect_info = await auth_proxy._authenticate_request(
        headers, path, path_rule
    )

    assert authenticated is True
    assert auth_headers == {"X-Auth-User": "test-user"}
    assert redirect_info is None


@pytest.mark.asyncio
async def test_authenticate_request_failure(auth_proxy):
    """Test failed authentication of a request."""
    # Update the mock plugin to fail authentication
    auth_proxy.auth_plugins["mock"].should_authenticate = False

    headers = {"X-Test": "value"}
    path = "/api/resource"
    path_rule = {"authenticate": True, "plugins": ["mock"]}

    authenticated, auth_headers, redirect_info = await auth_proxy._authenticate_request(
        headers, path, path_rule
    )

    assert authenticated is False
    assert auth_headers == {}
    assert redirect_info is None


@pytest.mark.asyncio
async def test_authenticate_request_no_auth_required(auth_proxy):
    """Test request that doesn't require authentication."""
    headers = {"X-Test": "value"}
    path = "/public/resource"
    path_rule = {"authenticate": False}

    authenticated, auth_headers, redirect_info = await auth_proxy._authenticate_request(
        headers, path, path_rule
    )

    assert authenticated is True
    assert auth_headers == {}
    assert redirect_info is None


@pytest.mark.asyncio
async def test_authenticate_request_with_redirect(auth_proxy):
    """Test authentication with redirect."""
    # Update the mock plugin to redirect
    auth_proxy.auth_plugins["mock"].should_redirect = True
    auth_proxy.auth_plugins["mock"].redirect_url = "/login"

    headers = {"X-Test": "value"}
    path = "/api/resource"
    path_rule = {"authenticate": True, "plugins": ["mock"]}

    authenticated, auth_headers, redirect_info = await auth_proxy._authenticate_request(
        headers, path, path_rule
    )

    assert authenticated is False
    assert auth_headers == {}
    assert redirect_info == (302, "/login")


@pytest.mark.asyncio
async def test_authenticate_request_multiple_plugins_any_mode(auth_proxy):
    """Test authentication with multiple plugins in 'any' mode."""
    # Add another mock plugin that fails
    auth_proxy.auth_plugins["mock-fail"] = MockAuthPlugin(
        {"should_authenticate": False}
    )

    headers = {"X-Test": "value"}
    path = "/api/resource"
    path_rule = {"authenticate": True, "plugins": ["mock", "mock-fail"], "mode": "any"}

    authenticated, auth_headers, redirect_info = await auth_proxy._authenticate_request(
        headers, path, path_rule
    )

    # Should succeed because at least one plugin succeeds
    assert authenticated is True
    assert auth_headers == {"X-Auth-User": "test-user"}
    assert redirect_info is None


@pytest.mark.asyncio
async def test_authenticate_request_multiple_plugins_all_mode(auth_proxy):
    """Test authentication with multiple plugins in 'all' mode."""
    # Add another mock plugin that fails
    auth_proxy.auth_plugins["mock-fail"] = MockAuthPlugin(
        {"should_authenticate": False}
    )

    headers = {"X-Test": "value"}
    path = "/api/resource"
    path_rule = {"authenticate": True, "plugins": ["mock", "mock-fail"], "mode": "all"}

    authenticated, auth_headers, redirect_info = await auth_proxy._authenticate_request(
        headers, path, path_rule
    )

    # Should fail because not all plugins succeed
    assert authenticated is False
    assert auth_headers == {}
    assert redirect_info is None


@pytest.mark.asyncio
async def test_handle_request_authenticated(auth_proxy):
    """Test handling an authenticated request."""
    # Mock reader and writer
    reader = AsyncMock()
    writer = MagicMock()
    writer.write.return_value = None
    writer.drain = AsyncMock()
    writer.close.return_value = None
    writer.wait_closed = AsyncMock()

    # Mock the request
    reader.readline.side_effect = [
        b"GET /api/resource HTTP/1.1\r\n",  # Request line
        b"Host: localhost\r\n",  # Headers
        b"\r\n",  # End of headers
    ]
    reader.read.return_value = b""  # Empty body

    # Create a proper async context manager mock
    class AsyncContextManagerMock:
        def __init__(self, return_value):
            self.return_value = return_value

        async def __aenter__(self):
            return self.return_value

        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass

    # Create a mock response
    class MockResponse:
        def __init__(self):
            self.status = 200
            self.reason = "OK"
            self.headers = {"Content-Type": "application/json"}
            self.content = self

        async def iter_chunked(self, size):
            yield b'{"result": "success"}'

    # Create a mock session
    class MockSession:
        def request(self, method, url, **kwargs):
            return AsyncContextManagerMock(MockResponse())

    # Patch aiohttp.ClientSession
    with patch(
        "aiohttp.ClientSession", return_value=AsyncContextManagerMock(MockSession())
    ):
        # Call the method under test
        await auth_proxy.handle_request(reader, writer)

    # Get all the write calls
    write_calls = [args[0] for args, _ in writer.write.call_args_list]

    # Debug output to see what was actually written
    print("Write calls:")
    for call in write_calls:
        print(f"  {call}")

    # Check that the expected response was written
    assert b"HTTP/1.1 200 OK" in write_calls
    assert b"Content-Type: application/json" in write_calls
    assert b"\r\n" in write_calls
    assert b'{"result": "success"}' in write_calls

    # Check that the connection was closed
    writer.close.assert_called_once()


@pytest.mark.asyncio
async def test_handle_request_unauthenticated(auth_proxy):
    """Test handling an unauthenticated request."""
    # Update the mock plugin to fail authentication
    auth_proxy.auth_plugins["mock"].should_authenticate = False

    # Mock reader and writer
    reader = AsyncMock()
    writer = MagicMock()
    writer.write.return_value = None
    writer.drain = AsyncMock()
    writer.close.return_value = None
    writer.wait_closed = AsyncMock()

    # Mock the request
    reader.readline.side_effect = [
        b"GET /api/resource HTTP/1.1\r\n",  # Request line
        b"Host: localhost\r\n",  # Headers
        b"\r\n",  # End of headers
    ]
    reader.read.return_value = b""  # Empty body

    await auth_proxy.handle_request(reader, writer)

    # Check that 401 Unauthorized was written
    calls = [args[0] for args, _ in writer.write.call_args_list]
    assert b"HTTP/1.1 401 Unauthorized\r\n" in calls
    assert b"Unauthorized" in calls

    # Check that the connection was closed
    writer.close.assert_called_once()


@pytest.mark.asyncio
async def test_handle_request_with_redirect(auth_proxy):
    """Test handling a request that requires redirection."""
    # Update the mock plugin to redirect
    auth_proxy.auth_plugins["mock"].should_redirect = True
    auth_proxy.auth_plugins["mock"].redirect_url = "/login"

    # Mock reader and writer
    reader = AsyncMock()
    writer = MagicMock()
    writer.write.return_value = None
    writer.drain = AsyncMock()
    writer.close.return_value = None
    writer.wait_closed = AsyncMock()

    # Mock the request
    reader.readline.side_effect = [
        b"GET /api/resource HTTP/1.1\r\n",  # Request line
        b"Host: localhost\r\n",  # Headers
        b"\r\n",  # End of headers
    ]
    reader.read.return_value = b""  # Empty body

    await auth_proxy.handle_request(reader, writer)

    # Check that redirect was written
    calls = [args[0] for args, _ in writer.write.call_args_list]
    assert b"HTTP/1.1 302 Found" in calls
    assert b"Location: /login" in calls

    # Check that the connection was closed
    writer.close.assert_called_once()


@pytest.mark.asyncio
async def test_handle_plugin_path(auth_proxy):
    """Test handling a plugin-specific path."""
    # Mock reader and writer
    reader = AsyncMock()
    writer = MagicMock()
    writer.write.return_value = None
    writer.drain = AsyncMock()
    writer.close.return_value = None
    writer.wait_closed = AsyncMock()

    # Mock the request
    reader.readline.side_effect = [
        b"GET /auth/mock/callback HTTP/1.1\r\n",  # Request line
        b"Host: localhost\r\n",  # Headers
        b"\r\n",  # End of headers
    ]
    reader.read.return_value = b""  # Empty body

    # Register the plugin path
    auth_proxy.plugin_paths["/auth/mock/callback"] = {
        "plugin": "mock",
        "regex": False,
        "authenticate": False,
        "description": "Mock callback endpoint",
    }

    await auth_proxy.handle_request(reader, writer)

    # Check that the plugin's response was written
    calls = [args[0] for args, _ in writer.write.call_args_list]
    assert b"HTTP/1.1 200 OK" in calls
    assert b"Content-Type: application/json" in calls
    assert b'{"status": "success"}' in calls

    # Check that the connection was closed
    writer.close.assert_called_once()
