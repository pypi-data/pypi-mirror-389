import asyncio
import socket
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer

import aiohttp
import pytest

from auth_proxy.proxy import AuthProxy


class MockHTTPRequestHandler(BaseHTTPRequestHandler):
    """Mock HTTP request handler for integration testing."""

    def do_GET(self):
        """Handle GET requests."""
        print(f"Mock server received request: GET {self.path}")
        print(f"Headers: {self.headers}")

        if self.path == "/api/resource":
            # Check for auth header
            if "X-Auth-User" in self.headers:
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                response = (
                    f'{{"result": "success", "user": "{self.headers["X-Auth-User"]}"}}'
                )
                self.send_header("Content-Length", str(len(response)))
                self.end_headers()
                self.wfile.write(response.encode())
            else:
                self.send_response(403)
                self.send_header("Content-Type", "application/json")
                response = '{"error": "Missing auth header"}'
                self.send_header("Content-Length", str(len(response)))
                self.end_headers()
                self.wfile.write(response.encode())
        elif self.path == "/public/resource":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            response = '{"result": "public"}'
            self.send_header("Content-Length", str(len(response)))
            self.end_headers()
            self.wfile.write(response.encode())
        elif self.path == "/health":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            response = '{"status": "up"}'
            self.send_header("Content-Length", str(len(response)))
            self.end_headers()
            self.wfile.write(response.encode())
        else:
            self.send_response(404)
            self.send_header("Content-Type", "application/json")
            response = '{"error": "Path not found"}'
            self.send_header("Content-Length", str(len(response)))
            self.end_headers()
            self.wfile.write(response.encode())

    def log_message(self, format, *args):
        """Override to suppress log messages."""
        pass


class MockServer:
    """Mock HTTP server for integration testing."""

    def __init__(self, host="localhost", port=3000):
        self.host = host
        self.port = port
        self.server = None
        self.thread = None

    def start(self):
        """Start the server in a separate thread."""
        self.server = HTTPServer((self.host, self.port), MockHTTPRequestHandler)
        self.thread = threading.Thread(target=self.server.serve_forever)
        self.thread.daemon = True
        self.thread.start()
        print(f"Mock server started on {self.host}:{self.port}")

        # Wait until the server is actually listening
        for _ in range(10):
            try:
                with socket.create_connection((self.host, self.port), timeout=1):
                    break
            except (ConnectionRefusedError, socket.timeout):
                time.sleep(0.1)

    def stop(self):
        """Stop the server."""
        if self.server:
            self.server.shutdown()
            self.server.server_close()
        if self.thread:
            self.thread.join(timeout=1)
        print(f"Mock server stopped")


class ProxyRunner:
    """Runs the auth proxy in a separate thread."""

    def __init__(self, config, host="127.0.0.1", port=8000):
        self.host = host
        self.port = port
        self.config = config
        self.thread = None
        self.server = None
        self.should_stop = threading.Event()

    async def _run_server(self):
        """Run the auth proxy server."""
        # Register the mock plugin
        from auth_proxy.auth_plugins import PLUGIN_REGISTRY
        from tests.conftest import MockAuthPlugin

        PLUGIN_REGISTRY["mock"] = MockAuthPlugin

        # Create the auth proxy
        proxy = AuthProxy(self.config)

        # Start the server
        self.server = await asyncio.start_server(
            proxy.handle_request, self.host, self.port
        )
        print(f"Auth proxy started on {self.host}:{self.port}")

        # Wait until should_stop is set
        while not self.should_stop.is_set():
            await asyncio.sleep(0.1)

        # Close the server
        self.server.close()
        await self.server.wait_closed()

    def _thread_target(self):
        """Target function for the thread."""
        asyncio.run(self._run_server())

    def start(self):
        """Start the proxy in a separate thread."""
        self.thread = threading.Thread(target=self._thread_target)
        self.thread.daemon = True
        self.thread.start()

        # Wait until the proxy is actually listening
        for _ in range(10):
            try:
                with socket.create_connection((self.host, self.port), timeout=1):
                    break
            except (ConnectionRefusedError, socket.timeout):
                time.sleep(0.1)

    def stop(self):
        """Stop the proxy."""
        self.should_stop.set()
        if self.thread:
            self.thread.join(timeout=1)
        print(f"Auth proxy stopped")


@pytest.fixture
def mock_server():
    """Start and stop a mock backend server."""
    server = MockServer()
    server.start()
    yield server
    server.stop()


@pytest.fixture
def auth_proxy_runner(basic_config):
    """Start and stop the auth proxy."""
    # Make sure the backend config is correct
    basic_config["backend"] = {"host": "localhost", "port": 3000}

    runner = ProxyRunner(basic_config)
    runner.start()
    yield runner
    runner.stop()


@pytest.mark.asyncio
async def test_authenticated_request(mock_server, auth_proxy_runner):
    """Test an authenticated request through the proxy."""
    # Give the servers a moment to start
    await asyncio.sleep(0.5)

    async with aiohttp.ClientSession() as session:
        # Request to authenticated path
        async with session.get("http://127.0.0.1:8000/api/resource") as response:
            # Print response for debugging
            print(f"Status: {response.status}")
            text = await response.text()
            print(f"Response: {text}")

            assert response.status == 200
            data = await response.json()
            assert data["result"] == "success"
            assert data["user"] == "test-user"


@pytest.mark.asyncio
async def test_health_check(mock_server, auth_proxy_runner):
    """Test a health check request."""
    # Give the servers a moment to start
    await asyncio.sleep(0.5)

    async with aiohttp.ClientSession() as session:
        # Request to health check path
        async with session.get("http://127.0.0.1:8000/health") as response:
            # Print response for debugging
            print(f"Status: {response.status}")
            text = await response.text()
            print(f"Response: {text}")

            assert response.status == 200
            data = await response.json()
            assert data["status"] == "up"
