import base64
import logging
from typing import Any, Dict

import bcrypt

from .base import AuthPlugin, AuthResult

logger = logging.getLogger(__name__)


class BasicAuthPlugin(AuthPlugin):
    """Basic HTTP authentication plugin."""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.users = config.get("users", {})
        self.realm = config.get("realm", "Authentication Required")

        for username, password in self.users.items():
            if password and not password.startswith("$2"):  # bcrypt hash
                logger.warning(
                    f"User '{username}' appears to have a plain text password "
                    f"but hash_passwords is enabled. Use 'auth-proxy-hash' to "
                    f"generate a proper hash."
                )

    def authenticate(self, request_headers: Dict[str, str], path: str) -> AuthResult:
        """Authenticate using Basic auth header."""
        auth_header = request_headers.get("Authorization", "")
        if not auth_header.startswith("Basic "):
            logger.debug("No Basic auth header found")
            # Return a challenge to the client
            return AuthResult(
                authenticated=False,
                headers={"WWW-Authenticate": f'Basic realm="{self.realm}"'},
            )

        try:
            encoded = auth_header.split(" ", 1)[1]
            decoded = base64.b64decode(encoded).decode("utf-8")
            username, password = decoded.split(":", 1)

            if username in self.users:
                if self.users[username].startswith("$2"):
                    try:
                        # Verify against the hash
                        if bcrypt.checkpw(
                            password.encode("utf-8"),
                            self.users[username].encode("utf-8"),
                        ):
                            auth_headers = self.get_auth_headers(request_headers, path)
                            return AuthResult(authenticated=True, headers=auth_headers)
                    except Exception as e:
                        logger.error(
                            f"Error verifying password hash for user {username}: {e}"
                        )
                        return AuthResult(
                            authenticated=False,
                            headers={"WWW-Authenticate": f'Basic realm="{self.realm}"'},
                        )
                else:
                    # Fall back to plain text comparison with a warning
                    logger.warning(
                        f"User '{username}' has a plain text password. This is insecure!"
                    )

                    if self.users[username] == password:
                        auth_headers = self.get_auth_headers(request_headers, path)
                        return AuthResult(authenticated=True, headers=auth_headers)

            logger.debug(f"Invalid credentials for user: {username}")
            # Return a challenge to the client
            return AuthResult(
                authenticated=False,
                headers={"WWW-Authenticate": f'Basic realm="{self.realm}"'},
            )
        except Exception as e:
            logger.debug(f"Basic auth parsing error: {e}")
            # Return a challenge to the client
            return AuthResult(
                authenticated=False,
                headers={"WWW-Authenticate": f'Basic realm="{self.realm}"'},
            )

    def get_auth_headers(
        self, request_headers: Dict[str, str], path: str
    ) -> Dict[str, str]:
        """Add username as header after successful authentication."""
        auth_header = request_headers.get("Authorization", "")
        if not auth_header.startswith("Basic "):
            return {}

        try:
            encoded = auth_header.split(" ", 1)[1]
            decoded = base64.b64decode(encoded).decode("utf-8")
            username, _ = decoded.split(":", 1)

            return {"X-Auth-User": username}
        except Exception:
            return {}
