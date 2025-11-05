from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Set, Tuple, Union


class AuthResult:
    """Result of an authentication attempt."""

    def __init__(
        self,
        authenticated: bool = False,
        headers: Optional[Dict[str, str]] = None,
        redirect_url: Optional[str] = None,
        redirect_status_code: int = 302,
    ):
        """
        Initialize an authentication result.

        Args:
            authenticated: Whether the request is authenticated
            headers: Headers to add to the proxied request if authenticated
            redirect_url: URL to redirect to if authentication requires redirection
            redirect_status_code: HTTP status code to use for redirection (default: 302)
        """
        self.authenticated = authenticated
        self.headers = headers or {}
        self.redirect_url = redirect_url
        self.redirect_status_code = redirect_status_code

    @property
    def requires_redirect(self) -> bool:
        """Whether this result requires a redirect."""
        return self.redirect_url is not None


class PluginPath:
    """A path definition for a plugin."""

    def __init__(
        self,
        path: str,
        regex: bool = False,
        authenticate: bool = False,
        description: str = "",
    ):
        """
        Initialize a plugin path.

        Args:
            path: The path pattern
            regex: Whether the path is a regex pattern
            authenticate: Whether the path requires authentication
            description: Description of the path's purpose
        """
        self.path = path
        self.regex = regex
        self.authenticate = authenticate
        self.description = description


class AuthPlugin(ABC):
    """Base class for authentication plugins."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config

    @abstractmethod
    def authenticate(self, request_headers: Dict[str, str], path: str) -> AuthResult:
        """
        Authenticate a request.

        Args:
            request_headers: Headers from the incoming request
            path: The request path

        Returns:
            AuthResult: The result of the authentication attempt
        """
        pass

    def get_auth_headers(
        self, request_headers: Dict[str, str], path: str
    ) -> Dict[str, str]:
        """
        Get headers to add to the authenticated request.

        This method is called after a successful authentication.
        The default implementation returns an empty dict.

        Args:
            request_headers: Headers from the incoming request
            path: The request path

        Returns:
            Dict[str, str]: Headers to add to the proxied request
        """
        return {}

    def get_plugin_paths(self) -> List[PluginPath]:
        """
        Get paths that this plugin needs to handle.

        Returns:
            List[PluginPath]: List of paths that this plugin needs to handle
        """
        return []

    def handle_plugin_path(
        self, path: str, request_headers: Dict[str, str], request_body: bytes
    ) -> Optional[Tuple[int, Dict[str, str], bytes]]:
        """
        Handle a request to a plugin-specific path.

        This method is called for paths registered by the plugin via get_plugin_paths().
        If this method returns None, the request will be forwarded to the backend.
        If this method returns a tuple, the proxy will respond directly with the provided status, headers, and body.

        Args:
            path: The request path
            request_headers: Headers from the incoming request
            request_body: Body from the incoming request

        Returns:
            Optional[Tuple[int, Dict[str, str], bytes]]:
                If not None, a tuple of (status_code, response_headers, response_body)
        """
        return None
