import asyncio
import logging
import os
import re
from typing import Any, Dict, List, Optional, Tuple

import aiohttp

from auth_proxy.auth_plugins import create_plugin_instance
from auth_proxy.auth_plugins.base import AuthPlugin

logger = logging.getLogger(__name__)

WS_GUID = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"  # WebSocket GUID for handshake


class AuthProxy:
    """Authenticating reverse proxy."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config

        # Load all configured plugins
        self.auth_plugins: Dict[str, AuthPlugin] = {}
        self.plugin_paths: Dict[str, Dict[str, Any]] = {}  # Maps paths to plugin names
        plugins_config = config.get("auth_plugins", {})

        for plugin_name, plugin_config in plugins_config.items():
            try:
                plugin = create_plugin_instance(plugin_name, plugin_config)
                self.auth_plugins[plugin_name] = plugin
                logger.info(f"Loaded authentication plugin instance: {plugin_name}")

                # Register plugin paths
                for plugin_path in plugin.get_plugin_paths():
                    path_key = plugin_path.path

                    logger.debug(
                        f"Registering plugin path: {path_key} for plugin {plugin_name}"
                    )

                    if path_key in self.plugin_paths:
                        logger.warning(
                            f"Path '{path_key}' already registered by another plugin. Overriding."
                        )

                    self.plugin_paths[path_key] = {
                        "plugin": plugin_name,
                        "regex": plugin_path.regex,
                        "authenticate": plugin_path.authenticate,
                        "description": plugin_path.description,
                    }
                    logger.info(
                        f"Registered plugin path: {path_key} -> {plugin_name} ({plugin_path.description})"
                    )
            except Exception as e:
                logger.error(f"Failed to load plugin instance {plugin_name}: {e}")

        # Global auth settings
        self.auth_config = config.get("auth", {})
        self.default_plugins = self.auth_config.get("default_plugins", [])
        self.default_mode = self.auth_config.get("default_mode", "any")

        # Backend configuration (with defaults)
        backend = config.get("backend", {})
        self.backend_scheme = backend.get("scheme", "http")
        self.backend_host = backend.get("host", "localhost")
        self.backend_port = backend.get("port", 3000)  # Default port
        self.backend_socket = backend.get("socket")

        # WebSocket configuration
        self.enable_websockets = config.get("enable_websockets", True)

        # Path rules - precompile regex patterns
        self.paths = []
        for path_rule in config.get("paths", []):
            if path_rule.get("regex", False):
                try:
                    pattern = re.compile(path_rule["path"])
                    self.paths.append({**path_rule, "pattern": pattern})
                except re.error as e:
                    logger.error(f"Invalid regex pattern '{path_rule['path']}': {e}")
            else:
                self.paths.append(path_rule)

    def _get_path_rule(self, path: str) -> Dict[str, Any]:
        """
        Find the matching path rule for a given path.

        Args:
            path: The request path

        Returns:
            Dict: The matching path rule, or a default rule if no match
        """
        # Process rules in order (as defined in the config)
        for path_rule in self.paths:
            if "pattern" in path_rule:  # Regex pattern
                if path_rule["pattern"].match(path):
                    return path_rule
            else:  # Simple prefix matching
                pattern = path_rule.get("path", "")
                if path.startswith(pattern):
                    return path_rule

        # No matching rule found, use default behavior
        default_behavior = self.auth_config.get("default_behavior", "authenticated")
        authenticate = default_behavior == "authenticated"

        # Create a default rule
        return {
            "authenticate": authenticate,
            "plugins": self.default_plugins if authenticate else [],
            "mode": self.default_mode,
        }

    async def _authenticate_request(
        self, headers: Dict[str, str], path: str, path_rule: Dict[str, Any]
    ) -> Tuple[bool, Dict[str, str], Optional[Tuple[int, str]]]:
        """
        Authenticate a request using the specified plugins.

        Args:
            headers: The request headers
            path: The request path
            path_rule: The matching path rule

        Returns:
            Tuple[bool, Dict[str, str], Optional[Tuple[int, str]]]:
                (authenticated, auth_headers, redirect_info)
                where redirect_info is a tuple of (status_code, location) if redirection is needed
        """
        # If authentication is not required, return success
        if not path_rule.get("authenticate", True):
            return True, {}, None

        # Get the plugins to use
        plugin_names = path_rule.get("plugins", self.default_plugins)
        if not plugin_names:
            # No plugins specified and no defaults
            logger.warning(
                f"No authentication plugins specified for path '{path}' and no defaults configured"
            )
            return False, {}, None

        # Get the authentication mode
        mode = path_rule.get("mode", self.default_mode)

        # Collect authentication results and headers
        auth_results: List[bool] = []
        all_auth_headers: Dict[str, str] = {}
        redirect_info: Optional[Tuple[int, str]] = None

        for plugin_name in plugin_names:
            auth_plugin = self.auth_plugins.get(plugin_name)
            if not auth_plugin:
                logger.error(
                    f"Authentication plugin '{plugin_name}' specified but not loaded"
                )
                continue

            # Attempt authentication
            result = auth_plugin.authenticate(headers, path)

            # Check for redirection
            if result.requires_redirect:
                redirect_info = (result.redirect_status_code, result.redirect_url or "")
                # If a plugin requires redirection, we'll use that immediately
                return result.authenticated, result.headers, redirect_info

            auth_results.append(result.authenticated)

            # If authenticated, collect headers
            if result.authenticated:
                all_auth_headers.update(result.headers)
            elif not result.authenticated and "WWW-Authenticate" in result.headers:
                # For Basic Auth, we need to return the WWW-Authenticate header
                return False, result.headers, None

        # Determine overall authentication result
        if mode == "all":
            # All plugins must succeed
            authenticated = all(auth_results) if auth_results else False
            # If not authenticated, clear the headers
            if not authenticated:
                all_auth_headers = {}
        else:
            # Any plugin can succeed (default)
            authenticated = any(auth_results) if auth_results else False

        return authenticated, all_auth_headers, redirect_info

    def _status_message(self, status_code: int) -> str:
        """Get the message for an HTTP status code."""
        messages = {
            200: "OK",
            201: "Created",
            204: "No Content",
            301: "Moved Permanently",
            302: "Found",
            303: "See Other",
            304: "Not Modified",
            307: "Temporary Redirect",
            308: "Permanent Redirect",
            400: "Bad Request",
            401: "Unauthorized",
            403: "Forbidden",
            404: "Not Found",
            405: "Method Not Allowed",
            500: "Internal Server Error",
            501: "Not Implemented",
            502: "Bad Gateway",
            503: "Service Unavailable",
        }
        return messages.get(status_code, "Unknown")

    async def _handle_websocket(
        self,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
        request_line: str,
        headers: Dict[str, str],
        authenticated: bool,
        auth_headers: Dict[str, str],
    ) -> None:
        """
        Handle a WebSocket upgrade request.

        Args:
            reader: Stream reader for the client connection
            writer: Stream writer for the client connection
            request_line: The HTTP request line
            headers: The HTTP headers
            authenticated: Whether the request is authenticated
            auth_headers: Authentication headers to forward
        """
        if not authenticated:
            # Send 401 Unauthorized response
            writer.write(b"HTTP/1.1 401 Unauthorized\r\n")
            writer.write(b"Content-Type: text/plain\r\n")
            writer.write(b"Content-Length: 12\r\n")
            writer.write(b"\r\n")
            writer.write(b"Unauthorized")
            await writer.drain()
            return

        # Parse the request line
        method, path, protocol = request_line.split(" ")

        # Verify required WebSocket headers
        if "Upgrade" not in headers or headers["Upgrade"].lower() != "websocket":
            logger.error(
                "Invalid WebSocket upgrade request: missing or invalid Upgrade header"
            )
            writer.write(b"HTTP/1.1 400 Bad Request\r\n\r\n")
            await writer.drain()
            return

        if (
            "Connection" not in headers
            or "upgrade" not in headers["Connection"].lower()
        ):
            logger.error(
                "Invalid WebSocket upgrade request: missing or invalid Connection header"
            )
            writer.write(b"HTTP/1.1 400 Bad Request\r\n\r\n")
            await writer.drain()
            return

        if "Sec-WebSocket-Key" not in headers:
            logger.error(
                "Invalid WebSocket upgrade request: missing Sec-WebSocket-Key header"
            )
            writer.write(b"HTTP/1.1 400 Bad Request\r\n\r\n")
            await writer.drain()
            return

        # Connect to backend
        try:
            if self.backend_socket:
                # Unix socket
                backend_reader, backend_writer = await asyncio.open_unix_connection(
                    path=self.backend_socket
                )
            else:
                # TCP socket
                backend_reader, backend_writer = await asyncio.open_connection(
                    host=self.backend_host, port=self.backend_port
                )

            # Forward the WebSocket upgrade request to the backend
            backend_request = f"{method} {path} {protocol}\r\n"
            for key, value in headers.items():
                backend_request += f"{key}: {value}\r\n"

            # Add authentication headers
            for key, value in auth_headers.items():
                backend_request += f"{key}: {value}\r\n"

            backend_request += "\r\n"
            backend_writer.write(backend_request.encode())
            await backend_writer.drain()

            # Read the backend response
            response_line = await backend_reader.readline()
            if not response_line:
                logger.error("Empty response from backend for WebSocket upgrade")
                writer.write(b"HTTP/1.1 502 Bad Gateway\r\n\r\n")
                await writer.drain()
                return

            # Parse the response status
            response_line_str = response_line.decode("utf-8").strip()
            protocol, status_code, *reason = response_line_str.split(" ", 2)

            if status_code != "101":
                # Backend did not accept the WebSocket upgrade, forward the response as-is
                writer.write(response_line)

                # Forward headers
                while True:
                    header_line = await backend_reader.readline()
                    writer.write(header_line)
                    if header_line == b"\r\n":
                        break

                # Forward body if any
                while True:
                    chunk = await backend_reader.read(4096)
                    if not chunk:
                        break
                    writer.write(chunk)

                await writer.drain()
                return

            # Backend accepted the upgrade, forward the 101 response to the client
            writer.write(response_line)

            # Forward headers from backend
            backend_headers = {}
            while True:
                header_line = await backend_reader.readline()
                if header_line == b"\r\n":
                    writer.write(header_line)
                    break

                writer.write(header_line)

                # Parse header for logging
                try:
                    header_line_str = header_line.decode("utf-8").strip()
                    if ":" in header_line_str:
                        key, value = header_line_str.split(":", 1)
                        backend_headers[key.strip()] = value.strip()
                except Exception:
                    pass

            await writer.drain()

            # Now we have an established WebSocket connection
            # Set up bidirectional forwarding
            logger.info(f"WebSocket connection established for {path}")

            # Create tasks for bidirectional forwarding
            client_to_backend = asyncio.create_task(
                self._forward_websocket_data(
                    reader, backend_writer, "client -> backend"
                )
            )
            backend_to_client = asyncio.create_task(
                self._forward_websocket_data(
                    backend_reader, writer, "backend -> client"
                )
            )

            # Wait for either direction to complete (connection closed)
            done, pending = await asyncio.wait(
                [client_to_backend, backend_to_client],
                return_when=asyncio.FIRST_COMPLETED,
            )

            # Cancel the remaining task
            for task in pending:
                task.cancel()

            logger.info(f"WebSocket connection closed for {path}")

        except Exception as e:
            logger.error(f"Error handling WebSocket connection: {e}")
            try:
                writer.write(b"HTTP/1.1 502 Bad Gateway\r\n\r\n")
                await writer.drain()
            except:
                pass

    async def _forward_websocket_data(
        self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter, direction: str
    ) -> None:
        """
        Forward WebSocket data between client and backend.

        Args:
            reader: Source stream reader
            writer: Destination stream writer
            direction: Direction label for logging
        """
        try:
            while True:
                data = await reader.read(8192)
                if not data:
                    break
                writer.write(data)
                await writer.drain()
        except asyncio.CancelledError:
            # Task was cancelled, this is normal when the other direction completes
            pass
        except Exception as e:
            logger.error(f"Error forwarding WebSocket data ({direction}): {e}")
        finally:
            try:
                writer.close()
                await writer.wait_closed()
            except:
                pass

    async def handle_request(
        self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ) -> None:
        """
        Handle an incoming HTTP request.

        Args:
            reader: Stream reader for the client connection
            writer: Stream writer for the client connection
        """
        try:
            # Parse the HTTP request
            request_line_bytes = await reader.readline()
            if not request_line_bytes:
                return

            request_line = request_line_bytes.decode("utf-8").strip()
            logger.debug(f"Request line: {request_line}")
            method, path, protocol = request_line.split(" ")

            # Read headers
            headers: Dict[str, str] = {}
            while True:
                header_line_bytes = await reader.readline()
                header_line = header_line_bytes.decode("utf-8").strip()
                if not header_line:
                    break

                key, value = header_line.split(":", 1)
                headers[key.strip()] = value.strip()

            logger.debug(f"Request headers: {headers}")

            # Read body if present
            content_length = int(headers.get("Content-Length", "0"))
            body = await reader.read(content_length) if content_length else b""

            # Check if this is a WebSocket upgrade request
            is_websocket = (
                self.enable_websockets
                and headers.get("Upgrade", "").lower() == "websocket"
                and "upgrade" in headers.get("Connection", "").lower()
            )

            # Check if this is a plugin-specific path
            plugin_name = None
            for plugin_path, path_info in self.plugin_paths.items():
                if path_info.get("regex", False):
                    # Regex matching
                    try:
                        pattern = re.compile(plugin_path)
                        if pattern.match(path):
                            plugin_name = path_info["plugin"]
                            break
                    except re.error:
                        logger.error(f"Invalid regex pattern: {plugin_path}")
                else:
                    # Simple prefix matching
                    if path.startswith(plugin_path):
                        plugin_name = path_info["plugin"]
                        break

            # If this is a plugin-specific path, let the plugin handle it
            if plugin_name and plugin_name in self.auth_plugins:
                logger.debug(
                    f"Handling request with plugin '{plugin_name}' for path '{path}'"
                )

                plugin = self.auth_plugins[plugin_name]
                result = plugin.handle_plugin_path(path, headers, body)

                if result is not None:
                    # Plugin handled the request directly
                    status_code, response_headers, response_body = result

                    # Send the response
                    status_line = (
                        f"HTTP/1.1 {status_code} {self._status_message(status_code)}"
                    )
                    writer.write(status_line.encode())
                    writer.write(b"\r\n")

                    # Add Content-Length if not present
                    if response_body and "Content-Length" not in response_headers:
                        response_headers["Content-Length"] = str(len(response_body))

                    # Write response headers
                    for key, value in response_headers.items():
                        header_line = f"{key}: {value}"
                        writer.write(header_line.encode())
                        writer.write(b"\r\n")

                    # End headers
                    writer.write(b"\r\n")

                    # Write response body
                    if response_body:
                        if isinstance(response_body, str):
                            response_body = response_body.encode("utf-8")

                        writer.write(response_body)

                    await writer.drain()
                    return

            # Continue with normal request processing
            # Get the matching path rule
            path_rule = self._get_path_rule(path)
            logger.debug(f"Matching path rule: {path_rule}")

            # Authenticate the request
            authenticated, auth_headers, redirect_info = (
                await self._authenticate_request(headers, path, path_rule)
            )
            logger.debug(
                f"Authentication result: {authenticated}, headers: {auth_headers}, redirect: {redirect_info}"
            )

            # Handle redirection if needed
            if redirect_info:
                status_code, location = redirect_info
                logger.debug(f"Redirecting to {location} with status {status_code}")

                # Send redirect response
                status_line = (
                    f"HTTP/1.1 {status_code} {self._status_message(status_code)}"
                )
                writer.write(status_line.encode())
                writer.write(b"\r\n")
                writer.write(f"Location: {location}".encode())
                writer.write(b"\r\n")
                writer.write(b"Content-Length: 0\r\n")

                # Add any auth headers to the response
                for key, value in auth_headers.items():
                    writer.write(f"{key}: {value}".encode())
                    writer.write(b"\r\n")

                writer.write(b"\r\n")
                await writer.drain()
                return

            # Handle WebSocket upgrade if needed
            if is_websocket:
                await self._handle_websocket(
                    reader, writer, request_line, headers, authenticated, auth_headers
                )
                return

            # Update headers with authentication information
            if authenticated:
                # Convert auth_headers to the same format as headers
                for key, value in auth_headers.items():
                    headers[key] = value
            else:
                # Send 401 Unauthorized response
                logger.debug("Sending 401 Unauthorized response")
                writer.write(b"HTTP/1.1 401 Unauthorized\r\n")

                # Add any auth headers (like WWW-Authenticate for Basic Auth)
                for key, value in auth_headers.items():
                    writer.write(f"{key}: {value}".encode())
                    writer.write(b"\r\n")

                writer.write(b"Content-Type: text/plain\r\n")
                writer.write(b"Content-Length: 12\r\n")
                writer.write(b"\r\n")
                writer.write(b"Unauthorized")
                await writer.drain()
                return

            # Forward the request to the backend
            try:
                logger.debug("Forwarding request to backend")
                async with aiohttp.ClientSession() as session:
                    # Construct backend URL
                    if self.backend_socket:
                        # Unix socket
                        connector = aiohttp.UnixConnector(path=self.backend_socket)
                        backend_url = f"{self.backend_scheme}://localhost{path}"
                        client_kwargs = {"connector": connector}
                    else:
                        # TCP socket
                        backend_url = f"{self.backend_scheme}://{self.backend_host}"
                        if self.backend_port:
                            backend_url += f":{self.backend_port}"
                        backend_url += path
                        client_kwargs = {}

                    logger.debug(f"Backend URL: {backend_url}")

                    # Forward the request
                    async with session.request(
                        method, backend_url, headers=headers, data=body, **client_kwargs
                    ) as response:
                        # Write response status line
                        status_line = f"HTTP/1.1 {response.status} {response.reason}"
                        logger.debug(f"Backend response: {status_line}")
                        writer.write(status_line.encode())
                        writer.write(b"\r\n")

                        # Write response headers
                        for key, value in response.headers.items():
                            header_line = f"{key}: {value}"
                            writer.write(header_line.encode())
                            writer.write(b"\r\n")

                        # End headers
                        writer.write(b"\r\n")

                        # Stream response body
                        async for chunk in response.content.iter_chunked(8192):
                            writer.write(chunk)

                        await writer.drain()
            except Exception as e:
                logger.error(f"Error forwarding request to backend: {e}")
                # Send 502 Bad Gateway
                writer.write(b"HTTP/1.1 502 Bad Gateway\r\n")
                writer.write(b"Content-Type: text/plain\r\n")
                writer.write(b"Content-Length: 11\r\n")
                writer.write(b"\r\n")
                writer.write(b"Bad Gateway")
                await writer.drain()
        except Exception as e:
            logger.error(f"Error handling request: {e}")
            try:
                # Send 500 Internal Server Error
                writer.write(b"HTTP/1.1 500 Internal Server Error\r\n")
                writer.write(b"Content-Type: text/plain\r\n")
                writer.write(b"Content-Length: 21\r\n")
                writer.write(b"\r\n")
                writer.write(b"Internal Server Error")
                await writer.drain()
            except:
                pass
        finally:
            try:
                writer.close()
                await writer.wait_closed()
            except:
                pass

    async def start(self) -> None:
        """Start the proxy server."""
        listen_config = self.config.get("listen", {})
        host = listen_config.get("host", "127.0.0.1")
        port = listen_config.get("port")
        socket_path = listen_config.get("socket")
        socket_mode = (
            int(str(listen_config["socket-chmod"]), 8)
            if "socket-chmod" in listen_config
            else None
        )

        if socket_path:
            # Unix socket server
            server = await asyncio.start_unix_server(
                self.handle_request, path=socket_path
            )

            # Set socket permissions
            if socket_mode:
                try:
                    os.chmod(socket_path, socket_mode)
                except OSError as e:
                    logger.error(f"Error setting socket permissions: {e}")

            logger.info(f"Proxy server listening on Unix socket {socket_path}")
        elif port:
            # TCP server
            server = await asyncio.start_server(
                self.handle_request, host=host, port=port
            )
            logger.info(f"Proxy server listening on {host}:{port}")
        else:
            raise ValueError(
                "Either 'port' or 'socket' must be specified in listen config"
            )

        async with server:
            await server.serve_forever()
