# Modular Authenticating Reverse Proxy

A flexible, modular reverse proxy with pluggable authentication mechanisms. Designed to sit behind an internet-facing web server like Nginx or Caddy, this proxy authenticates requests before forwarding them to your backend applications.

## Features

- **Modular Authentication**: Pluggable authentication system with support for external plugins
- **Multiple Authentication Methods**: Support for using multiple auth methods per path
- **Flexible Configuration**: Simple YAML-based configuration
- **Path-Based Rules**: Configure which paths require authentication and which don't
- **Regular Expression Matching**: Powerful path matching with regex support
- **Authentication Redirection**: Support for authentication flows that require redirection
- **Plugin-Specific Paths**: Plugins can register their own paths for callbacks and other needs
- **Connection Flexibility**: Support for both TCP and Unix sockets
- **Header Forwarding**: Authentication information is forwarded to the backend via HTTP headers
- **Lightweight**: Focused on authentication, not trying to replace your main web server

## Installation

```bash
# Install from PyPI
pip install python-auth-proxy

# Or install with a specific authentication plugin
pip install python-auth-proxy auth-proxy-jwt
```

## Quick Start

1. Create a configuration file:

```yaml
# config.yaml
listen:
  host: 127.0.0.1
  port: 8000

backend:
  scheme: http
  host: localhost
  port: 3000

auth_plugins:
  basic:
    users:
      admin: password123
      user1: secret456

auth:
  default_plugins: [basic]
  default_behavior: "authenticated"

paths:
  - path: "^/api/.*$"
    regex: true
    authenticate: true
    plugins: [basic]

  - path: "^/public/.*$"
    regex: true
    authenticate: false

  - path: "/health"
    authenticate: false
```

2. Run the proxy:

```bash
auth-proxy -c config.yaml
```

## Configuration Options

### Listener Configuration

```yaml
listen:
  # TCP socket
  host: 127.0.0.1 # Optional, defaults to 127.0.0.1
  port: 8000

  # Or Unix socket
  socket: /tmp/auth_proxy.sock
```

### Backend Configuration

```yaml
backend:
  # TCP socket
  scheme: http # Optional, defaults to http
  host: localhost
  port: 3000

  # Or Unix socket
  socket: /tmp/app.sock
  socket-chmod: 660  # Optional, sets socket permissions (octal format)
```

### Authentication Plugins

You can configure multiple authentication plugins and use them for different paths:

```yaml
# Define all available plugins and their configurations
auth_plugins:
  # Standard plugin instance
  oidc:
    issuer: https://your-oidc-provider.com
    client_id: your-client-id
    client_secret: your-client-secret
    redirect_uri: https://your-app.com/auth/oidc/callback
    callback_path: /auth/oidc/callback

  # Named instances of the basic auth plugin
  user-basic:
    type: basic
    users:
      user1: password123
      user2: secret456

  admin-basic:
    type: basic
    users:
      admin: admin-password
      superuser: super-secret
```

### Global Authentication Settings

```yaml
auth:
  # Default plugins to use if not specified in a path
  default_plugins: [oidc, jwt]

  # Default authentication mode: "any" or "all"
  default_mode: "any"

  # Default behavior for paths not matching any rule: "authenticated" or "unauthenticated"
  default_behavior: "authenticated"
```

### Path Rules and Precedence

Path rules are processed in the order they appear in the configuration. The first matching rule takes precedence:

```yaml
paths:
  # More specific rule first
  - path: "^/api/public/.*$"
    regex: true
    authenticate: false

  # More general rule second
  - path: "^/api/.*$"
    regex: true
    authenticate: true
    plugins: [oidc]
```

In this example, paths starting with `/api/public/` will not require authentication, while all other API paths will require OIDC authentication.

### Regular Expression Path Matching

For more flexible path matching, you can use regular expressions:

```yaml
paths:
  # Match all paths that start with /api/ followed by anything
  - path: "^/api/.*$"
    regex: true
    authenticate: true
    plugins: [jwt]

  # Match specific pattern
  - path: "^/users/[0-9]+/profile$"
    regex: true
    authenticate: true
    plugins: [oidc]
```

When using regex paths, set `regex: true` in the path rule.

### Multiple Authentication Methods Per Path

You can specify multiple authentication plugins for a path:

```yaml
paths:
  # Allow access if either OIDC or JWT authentication succeeds
  - path: "^/api/.*$"
    regex: true
    authenticate: true
    plugins: [oidc, jwt]
    mode: "any" # "any" (default) or "all"

  # Require both OIDC and Basic authentication to succeed
  - path: "^/secure/.*$"
    regex: true
    authenticate: true
    plugins: [oidc, basic]
    mode: "all"
```

The `mode` parameter determines how multiple plugins are evaluated:

- `any`: The request is authenticated if any plugin succeeds (OR logic)
- `all`: The request is authenticated only if all plugins succeed (AND logic)

### Named Plugin Instances

You can create multiple instances of the same plugin type with different configurations:

```yaml
auth_plugins:
  # Simple case - plugin name matches plugin type
  oidc:
    issuer: https://your-oidc-provider.com
    client_id: your-client-id
    client_secret: your-client-secret

  # Named instances must specify their type
  user-basic:
    type: basic
    users:
      user1: password123
      user2: secret456

  admin-basic:
    type: basic
    users:
      admin: admin-password
      superuser: super-secret
```

This allows you to have multiple configurations of the same plugin type for different purposes.

### Default Behavior

You can specify the default behavior for paths that don't match any rule:

```yaml
auth:
  default_behavior: "authenticated" # or "unauthenticated"
```

This setting determines whether paths not matching any rule require authentication by default:

- `authenticated`: Paths not matching any rule will require authentication using the default plugins
- `unauthenticated`: Paths not matching any rule will not require authentication

If not specified, the default is `authenticated`.

## Authentication with Redirection

Some authentication methods like OIDC require redirecting the user to an external login page. The proxy supports this flow:

### OIDC Configuration

```yaml
auth_plugins:
  oidc:
    issuer: https://your-oidc-provider.com
    client_id: your-client-id
    client_secret: your-client-secret
    redirect_uri: https://your-app.com/auth/oidc/callback
    callback_path: /auth/oidc/callback
    scope: openid profile email
```

When a user tries to access a protected resource without authentication, they will be redirected to the identity provider's login page. After successful login, they will be redirected back to your application with an authorization code, which the proxy will exchange for tokens.

## Plugin-Specific Paths

Authentication plugins can register their own paths to handle special endpoints like callbacks. These paths are automatically registered when the plugin is loaded:

### OIDC Plugin Paths

The OIDC plugin registers a callback path to handle the redirect from the identity provider:

```yaml
auth_plugins:
  oidc:
    issuer: https://your-oidc-provider.com
    client_id: your-client-id
    client_secret: your-client-secret
    redirect_uri: https://your-app.com/auth/oidc/callback
    callback_path: /auth/oidc/callback # This path will be handled by the OIDC plugin
```

You don't need to explicitly configure these paths in the `paths` section - they are automatically registered and handled by the plugin.

### Multiple Authentication Plugins

When using multiple authentication plugins, each plugin can register its own paths:

```yaml
auth_plugins:
  google-oidc:
    type: oidc
    issuer: https://accounts.google.com
    client_id: google-client-id
    client_secret: google-client-secret
    redirect_uri: https://your-app.com/auth/google/callback
    callback_path: /auth/google/callback

  github-oidc:
    type: oidc
    issuer: https://github.com
    client_id: github-client-id
    client_secret: github-client-secret
    redirect_uri: https://your-app.com/auth/github/callback
    callback_path: /auth/github/callback
```

In this example, each OIDC plugin registers its own callback path.

## Available Authentication Plugins

The proxy currently comes with one built-in authentication plugin:

1. **basic**: HTTP Basic Authentication

Other plugins are available as separate packages:

1. **auth-proxy-jwt**: JSON Web Token (JWT) authentication - [auth-proxy-jwt](https://git.private.coffee/kumi/auth-proxy-jwt)
2. **auth-proxy-oidc**: OpenID Connect (OIDC) authentication - [auth-proxy-oidc](https://git.private.coffee/kumi/auth-proxy-oidc)

To list all installed authentication plugins (including third-party plugins):

```bash
auth-proxy --list-plugins
```

### Basic Authentication

The built-in basic authentication plugin supports both plain text and hashed passwords using bcrypt:

```yaml
auth_plugins:
  basic:
    users:
      # Hashed password (recommended)
      admin: "$2b$12$YourHashedPasswordHere"
      # Plain text password (not recommended, will trigger warning)
      user1: "plaintext123"
```

#### Generating Password Hashes

Use the included utility to generate secure password hashes:

```bash
# Interactive mode (recommended - password not shown in shell history)
auth-proxy-hash

# Direct mode (be careful with shell history)
auth-proxy-hash -p yourpassword

# Verify a password against a hash
auth-proxy-hash --verify '$2b$12$YourHashedPasswordHere'
```

Example output:
```
$ auth-proxy-hash
Enter password to hash: 
Confirm password: 
Hashed password: $2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewKyNiLXCfLhlJ4O

You can use this in your config file like:
    username: "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewKyNiLXCfLhlJ4O"
```

#### Security Best Practices

1. Always use hashed passwords in production
2. Use the `auth-proxy-hash` utility to generate hashes
3. Store your configuration file securely with appropriate permissions

#### Migration from Plain Text

To migrate from plain text to hashed passwords:

1. Generate hashes for all passwords:
   ```bash
   auth-proxy-hash -p oldpassword
   ```

2. Update your configuration:
   ```yaml
   auth_plugins:
     basic:
       users:
         admin: "$2b$12$..."  # Replace with generated hash
   ```

## Path Rule Validation

To help understand which rule would match a given URL path, use the validation tool:

```bash
auth-proxy-validate -c config.yaml /api/v1/users
```

Example output for a regular path:

```
Path: /api/v1/users
Matching rule #3: ^/api/v1/.*$
Authentication required: True
Authentication plugins: oidc, user-basic
Authentication mode: any

Full matching rule:
  path: ^/api/v1/.*$
  regex: True
  authenticate: True
  plugins: ['oidc', 'user-basic']
  mode: any
```

Example output for a plugin path:

```
Path: /auth/oidc/callback
Matching plugin path: /auth/oidc/callback
Plugin: oidc
Description: OIDC callback endpoint for oidc
Authentication required: False

Full plugin path info:
  plugin: oidc
  regex: False
  authenticate: False
  description: OIDC callback endpoint for oidc
```

This tool is useful for:

- Testing your path rules
- Debugging authentication issues
- Understanding rule precedence
- Verifying plugin path configuration

## Creating a Custom Authentication Plugin

You can create your own authentication plugins for auth-proxy:

1. Create a new Python package for your plugin with a `pyproject.toml`:

```toml
# pyproject.toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "auth-proxy-my-plugin"
version = "0.1.0"
description = "My custom authentication plugin for python-auth-proxy"
requires-python = ">=3.8"
dependencies = [
    "python-auth-proxy",
]

[project.entry-points."auth_proxy.plugins"]
my-plugin = "auth_proxy_my_plugin.plugin:MyAuthPlugin"
```

2. Implement your plugin class:

```python
# auth_proxy_my_plugin/plugin.py
from typing import Dict, Any, List, Optional, Tuple
from auth_proxy.auth_plugins.base import AuthPlugin, AuthResult, PluginPath

class MyAuthPlugin(AuthPlugin):
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        # Initialize with your config parameters
        self.some_setting = config.get('some_setting')

    def authenticate(self, request_headers: Dict[str, str], path: str) -> AuthResult:
        # Implement your authentication logic
        # Return an AuthResult object
        return AuthResult(
            authenticated=True,
            headers={'X-Auth-User': 'example-user'}
        )

    def get_plugin_paths(self) -> List[PluginPath]:
        # Register any paths your plugin needs to handle
        return [
            PluginPath(
                path='/auth/my-plugin/callback',
                regex=False,
                authenticate=False,
                description="My plugin callback endpoint"
            )
        ]

    def handle_plugin_path(self, path: str, request_headers: Dict[str, str],
                          request_body: bytes) -> Optional[Tuple[int, Dict[str, str], bytes]]:
        # Handle requests to your plugin's paths
        if path.startswith('/auth/my-plugin/callback'):
            return (
                200,
                {'Content-Type': 'application/json'},
                b'{"status": "success"}'
            )

        return None
```

3. Install your plugin:

```bash
pip install -e .
```

4. Configure the proxy to use your plugin:

```yaml
auth_plugins:
  my-plugin:
    some_setting: some_value

paths:
  - path: "^/api/.*$"
    regex: true
    authenticate: true
    plugins: [my-plugin]
```

## Plugin API

Authentication plugins must implement the `AuthPlugin` base class:

### authenticate(request_headers, path)

Authenticates a request and returns an `AuthResult`.

- **Parameters**:
  - `request_headers` (Dict[str, str]): The HTTP headers from the incoming request
  - `path` (str): The request path
- **Returns**:
  - `AuthResult`: The result of the authentication attempt

### get_auth_headers(request_headers, path)

Returns headers to add to the authenticated request.

- **Parameters**:
  - `request_headers` (Dict[str, str]): The HTTP headers from the incoming request
  - `path` (str): The request path
- **Returns**:
  - `Dict[str, str]`: Headers to add to the proxied request

### get_plugin_paths()

Returns a list of paths that the plugin needs to handle.

- **Returns**:
  - `List[PluginPath]`: List of paths that this plugin needs to handle

### handle_plugin_path(path, request_headers, request_body)

Handles a request to a plugin-specific path.

- **Parameters**:
  - `path` (str): The request path
  - `request_headers` (Dict[str, str]): Headers from the incoming request
  - `request_body` (bytes): Body from the incoming request
- **Returns**:
  - `Optional[Tuple[int, Dict[str, str], bytes]]`: If not None, a tuple of (status_code, response_headers, response_body)

## Full Configuration Example

```yaml
# config.yaml
listen:
  host: 127.0.0.1
  port: 8000

backend:
  scheme: http
  host: localhost
  port: 3000

# Define all available plugins and their configurations
auth_plugins:
  oidc:
    issuer: https://your-oidc-provider.com
    client_id: your-client-id
    client_secret: your-client-secret
    redirect_uri: https://your-app.com/auth/oidc/callback
    callback_path: /auth/oidc/callback

  user-basic:
    type: basic
    users:
      user1: password123
      user2: secret456

  admin-basic:
    type: basic
    users:
      admin: admin-password
      superuser: super-secret

  web-jwt:
    type: jwt
    secret: your-web-secret-key
    algorithm: HS256
    audience: web-app

  mobile-jwt:
    type: jwt
    secret: your-mobile-secret-key
    algorithm: HS256
    audience: mobile-app

# Global authentication settings
auth:
  default_plugins: [oidc]
  default_mode: "any"
  default_behavior: "authenticated"

# Path rules with plugin selection (processed in order)
paths:
  # Specific public API endpoints (must come before general API rule)
  - path: "^/api/v1/public/.*$"
    regex: true
    authenticate: false

  # Admin API endpoints (specific before general)
  - path: "^/api/v1/admin/.*$"
    regex: true
    authenticate: true
    plugins: [admin-basic]

  # General API endpoints (after more specific rules)
  - path: "^/api/v1/.*$"
    regex: true
    authenticate: true
    plugins: [oidc, user-basic]
    mode: "any"

  # Mobile API endpoints
  - path: "^/api/mobile/.*$"
    regex: true
    authenticate: true
    plugins: [mobile-jwt]

  # Admin dashboard
  - path: "^/admin/.*$"
    regex: true
    authenticate: true
    plugins: [admin-basic]

  # Super secure endpoints - require both OIDC and admin basic auth
  - path: "^/secure/.*$"
    regex: true
    authenticate: true
    plugins: [oidc, admin-basic]
    mode: "all"

  # Public resources
  - path: "^/public/.*$"
    regex: true
    authenticate: false

  # Static assets
  - path: "^/assets/.*$"
    regex: true
    authenticate: false

  # Health check
  - path: "/health"
    authenticate: false

  # Metrics endpoint
  - path: "/metrics"
    authenticate: true
    plugins: [admin-basic]
```

## Deployment

### Docker

The proxy can be easily deployed using Docker:

```bash
# Pull the image
docker pull git.private.coffee/kumi/auth-proxy

# Run with a config file
docker run -v $(pwd)/config.yaml:/config/config.yaml -p 8000:8000 git.private.coffee/kumi/auth-proxy
```

Or using Docker Compose:

```yaml
# docker-compose.yml
version: "3"

services:
  auth-proxy:
    image: git.private.coffee/kumi/auth-proxy
    ports:
      - "8000:8000"
    volumes:
      - ./config.yaml:/config/config.yaml
```

### Behind Nginx or Caddy

The auth-proxy is designed to run behind a reverse proxy like Nginx or Caddy.

Example Nginx configuration:

```nginx
server {
    listen 443 ssl;
    server_name example.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Example Caddy configuration:

```
example.com {
    reverse_proxy localhost:8000
}
```

Any "fancy" features like TLS termination, caching, header manipulations, load balancing, etc. should be handled by your front-facing web server. From its point of view, the auth-proxy is just a part of the backend service.

If you use load balancing over multiple instances of the auth-proxy, make sure to configure the instances identically and set up sticky sessions or session affinity if your authentication method requires it.

## Command Line Options

```
usage: auth-proxy [-h] [-c CONFIG] [-v] [--list-plugins]

Modular Authenticating Reverse Proxy

optional arguments:
  -h, --help            show this help message and exit
  -c CONFIG, --config CONFIG
                        Path to config file (default: config.yaml)
  -v, --verbose         Enable verbose logging
  --list-plugins        List available authentication plugins
```

## Security Considerations

- The proxy does not handle TLS termination - use a front-facing web server for this
- Store sensitive configuration (like secrets) securely
- Review the authentication plugins you use for security best practices
- Consider using environment variables for secrets in production
- Always put more specific path rules before more general ones to avoid security bypasses

## Development

### Prerequisites

- Python 3.10 or higher
- pip

### Setting up the development environment

```bash
# Clone the repository
git clone https://git.private.coffee/kumi/auth-proxy.git
cd auth-proxy

# Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode
pip install -e .

# Install development dependencies
pip install -r requirements-dev.txt
```

### Running tests

```bash
pytest
```

### Code formatting and linting

```bash
# Format code
black auth_proxy tests

# Sort imports
isort auth_proxy tests

# Type checking
mypy auth_proxy
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](License) file for details.
