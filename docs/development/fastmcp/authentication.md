# Authentication

FastMCP supports OAuth2 authentication for HTTP transports (SSE and StreamableHTTP). This enables secure access control for servers exposed over the web.

> **Note**: Authentication is only available for HTTP transports. The stdio transport runs locally and doesn't require authentication.

## Overview

FastMCP authentication provides:

- **OAuth2 Authorization Server**: Built-in OAuth2 server for issuing tokens
- **Scope-based Access Control**: Restrict access to specific capabilities
- **Client Registration**: Dynamic or pre-configured client registration
- **Token Management**: Access tokens, refresh tokens, and revocation

## Basic Setup

### 1. Create OAuth Provider

```python
from mcp.server.auth.provider import OAuthAuthorizationServerProvider
from mcp.server.auth.settings import AuthSettings, ClientRegistrationOptions
from mcp.server.fastmcp import FastMCP

class SimpleOAuthProvider(OAuthAuthorizationServerProvider):
    """Minimal OAuth provider implementation."""

    def __init__(self):
        # In-memory storage (use database in production)
        self.clients = {}
        self.tokens = {}
        self.auth_codes = {}

    async def get_client(self, client_id: str):
        """Get client information."""
        return self.clients.get(client_id)

    async def create_authorization_code(self, params):
        """Create authorization code for OAuth flow."""
        code = "auth_code_" + secrets.token_urlsafe(32)
        self.auth_codes[code] = {
            "client_id": params.client_id,
            "scope": params.scope,
            "expires_at": time.time() + 600  # 10 minutes
        }
        return code

    async def exchange_code_for_tokens(self, code, client_id):
        """Exchange authorization code for access token."""
        if code not in self.auth_codes:
            raise ValueError("Invalid authorization code")

        token = "access_token_" + secrets.token_urlsafe(32)
        self.tokens[token] = {
            "client_id": client_id,
            "scope": self.auth_codes[code]["scope"],
            "expires_at": time.time() + 3600  # 1 hour
        }

        del self.auth_codes[code]  # Code is single-use
        return token

    async def validate_token(self, token):
        """Validate access token."""
        token_data = self.tokens.get(token)
        if not token_data:
            return None

        if time.time() > token_data["expires_at"]:
            del self.tokens[token]  # Clean up expired token
            return None

        return token_data

# Create provider and auth settings
oauth_provider = SimpleOAuthProvider()

auth_settings = AuthSettings(
    issuer_url="https://your-server.com",
    required_scopes=["read", "write"],
    client_registration_options=ClientRegistrationOptions(
        enabled=True,
        valid_scopes=["read", "write", "admin"]
    )
)

# Create authenticated server
mcp = FastMCP(
    "Authenticated Server",
    auth_server_provider=oauth_provider,
    auth=auth_settings
)
```

### 2. Run with Authentication

```python
if __name__ == "__main__":
    # Authentication only works with HTTP transports
    mcp.run("streamable-http")  # or "sse"
```

## Configuration

### Auth Settings

```python
from mcp.server.auth.settings import (
    AuthSettings,
    ClientRegistrationOptions,
    RevocationOptions
)

auth_settings = AuthSettings(
    # Required: Your server's public URL
    issuer_url="https://api.example.com",

    # Optional: Documentation URL for API consumers
    service_documentation_url="https://docs.example.com",

    # Required scopes for all requests
    required_scopes=["read"],

    # Client registration settings
    client_registration_options=ClientRegistrationOptions(
        enabled=True,
        client_secret_expiry_seconds=86400,  # 24 hours
        valid_scopes=["read", "write", "admin"],
        default_scopes=["read"]
    ),

    # Token revocation settings
    revocation_options=RevocationOptions(
        enabled=True
    )
)
```

### Environment Variables

```bash
# FastMCP auth settings
FASTMCP_AUTH__ISSUER_URL=https://api.example.com
FASTMCP_AUTH__REQUIRED_SCOPES=read,write
FASTMCP_AUTH__SERVICE_DOCUMENTATION_URL=https://docs.example.com

# Client registration
FASTMCP_AUTH__CLIENT_REGISTRATION_OPTIONS__ENABLED=true
FASTMCP_AUTH__CLIENT_REGISTRATION_OPTIONS__VALID_SCOPES=read,write,admin
```

## OAuth2 Flows

### Authorization Code Flow

The standard OAuth2 flow for web applications:

```
1. Client redirects user to /auth/authorize
2. User authenticates and grants permission
3. Server redirects back with authorization code
4. Client exchanges code for access token at /auth/token
5. Client uses access token in Authorization header
```

### Client Registration

Dynamic client registration for new applications:

```bash
# Register new client
POST /auth/register
Content-Type: application/json

{
    "client_name": "My App",
    "redirect_uris": ["https://myapp.com/callback"],
    "scope": "read write"
}

# Response
{
    "client_id": "client_123",
    "client_secret": "secret_abc",
    "client_id_issued_at": 1640995200,
    "client_secret_expires_at": 1641081600
}
```

## Complete Example

### GitHub OAuth Integration

```python
import secrets
import time
import httpx
from typing import Any

from mcp.server.auth.provider import OAuthAuthorizationServerProvider
from mcp.server.auth.settings import AuthSettings, ClientRegistrationOptions
from mcp.server.fastmcp import FastMCP

class GitHubOAuthProvider(OAuthAuthorizationServerProvider):
    """OAuth provider that integrates with GitHub."""

    def __init__(self, github_client_id: str, github_client_secret: str):
        self.github_client_id = github_client_id
        self.github_client_secret = github_client_secret
        self.clients = {}
        self.tokens = {}
        self.auth_codes = {}
        self.github_tokens = {}  # Map MCP tokens to GitHub tokens

    async def get_client(self, client_id: str):
        """Get registered client."""
        return self.clients.get(client_id)

    async def register_client(self, registration_data: dict) -> dict:
        """Register a new OAuth client."""
        client_id = f"client_{secrets.token_urlsafe(16)}"
        client_secret = f"secret_{secrets.token_urlsafe(32)}"

        self.clients[client_id] = {
            "client_id": client_id,
            "client_secret": client_secret,
            "client_name": registration_data.get("client_name"),
            "redirect_uris": registration_data.get("redirect_uris", []),
            "scope": registration_data.get("scope", "read"),
            "created_at": time.time()
        }

        return {
            "client_id": client_id,
            "client_secret": client_secret,
            "client_id_issued_at": int(time.time()),
            "client_secret_expires_at": int(time.time() + 86400)  # 24 hours
        }

    async def create_authorization_code(self, params: Any) -> str:
        """Create authorization code that will trigger GitHub OAuth."""
        code = f"auth_{secrets.token_urlsafe(32)}"

        # Store the original request parameters
        self.auth_codes[code] = {
            "client_id": params.client_id,
            "scope": params.scope,
            "redirect_uri": params.redirect_uri,
            "created_at": time.time(),
            "expires_at": time.time() + 600  # 10 minutes
        }

        return code

    async def exchange_code_for_tokens(self, code: str, client_id: str) -> dict:
        """Exchange authorization code for access token."""
        if code not in self.auth_codes:
            raise ValueError("Invalid or expired authorization code")

        auth_data = self.auth_codes[code]
        if time.time() > auth_data["expires_at"]:
            del self.auth_codes[code]
            raise ValueError("Authorization code expired")

        # For this example, we'll create a token without actually going to GitHub
        # In a real implementation, you'd exchange with GitHub here
        access_token = f"mcp_token_{secrets.token_urlsafe(32)}"

        self.tokens[access_token] = {
            "client_id": client_id,
            "scope": auth_data["scope"],
            "token_type": "Bearer",
            "expires_at": time.time() + 3600,  # 1 hour
            "issued_at": time.time()
        }

        # Clean up used code
        del self.auth_codes[code]

        return {
            "access_token": access_token,
            "token_type": "Bearer",
            "expires_in": 3600,
            "scope": auth_data["scope"]
        }

    async def validate_token(self, token: str) -> dict | None:
        """Validate access token."""
        token_data = self.tokens.get(token)
        if not token_data:
            return None

        if time.time() > token_data["expires_at"]:
            del self.tokens[token]
            return None

        return token_data

    async def revoke_token(self, token: str) -> bool:
        """Revoke access token."""
        if token in self.tokens:
            del self.tokens[token]
            return True
        return False

# Configuration
GITHUB_CLIENT_ID = "your_github_app_client_id"
GITHUB_CLIENT_SECRET = "your_github_app_client_secret"

# Create OAuth provider
oauth_provider = GitHubOAuthProvider(GITHUB_CLIENT_ID, GITHUB_CLIENT_SECRET)

# Create auth settings
auth_settings = AuthSettings(
    issuer_url="https://your-server.com",
    service_documentation_url="https://docs.your-server.com",
    required_scopes=["user"],
    client_registration_options=ClientRegistrationOptions(
        enabled=True,
        valid_scopes=["user", "repo", "admin"],
        default_scopes=["user"]
    )
)

# Create authenticated server
mcp = FastMCP(
    "GitHub MCP Server",
    auth_server_provider=oauth_provider,
    auth=auth_settings,
    host="0.0.0.0",
    port=8000
)

# Add protected tools
@mcp.tool()
def get_user_info(ctx) -> dict:
    """Get authenticated user information."""
    # Access token is available in context
    token = ctx.session.get_access_token()  # Example access
    return {"user": "authenticated_user", "token_type": "Bearer"}

if __name__ == "__main__":
    mcp.run("streamable-http")
```

## Using Authentication

### Client Side

```python
import httpx

# 1. Register client (if needed)
registration = httpx.post("https://server.com/auth/register", json={
    "client_name": "My Client App",
    "redirect_uris": ["https://myapp.com/callback"]
})
client_data = registration.json()

# 2. Start OAuth flow
auth_url = (
    f"https://server.com/auth/authorize"
    f"?client_id={client_data['client_id']}"
    f"&redirect_uri=https://myapp.com/callback"
    f"&scope=read write"
    f"&response_type=code"
)

# 3. User visits auth_url, grants permission, gets redirected with code

# 4. Exchange code for token
token_response = httpx.post("https://server.com/auth/token", data={
    "grant_type": "authorization_code",
    "code": "received_auth_code",
    "client_id": client_data["client_id"],
    "client_secret": client_data["client_secret"]
})
tokens = token_response.json()

# 5. Use access token
headers = {"Authorization": f"Bearer {tokens['access_token']}"}
response = httpx.post(
    "https://server.com/mcp",
    headers=headers,
    json={"method": "tools/call", "params": {"name": "my_tool"}}
)
```

### Custom Authentication

```python
from starlette.requests import Request
from starlette.responses import JSONResponse

@mcp.custom_route("/auth/callback", methods=["GET"])
async def auth_callback(request: Request) -> JSONResponse:
    """Handle OAuth callback."""
    code = request.query_params.get("code")
    if not code:
        return JSONResponse({"error": "No authorization code"}, status_code=400)

    # Process the authorization code
    # This would typically exchange with external OAuth provider

    return JSONResponse({"message": "Authentication successful"})

@mcp.custom_route("/auth/status", methods=["GET"])
async def auth_status(request: Request) -> JSONResponse:
    """Check authentication status."""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return JSONResponse({"authenticated": False}, status_code=401)

    token = auth_header.split(" ")[1]
    token_data = await oauth_provider.validate_token(token)

    return JSONResponse({
        "authenticated": token_data is not None,
        "scopes": token_data.get("scope", "").split() if token_data else []
    })
```

## Security Best Practices

### 1. Use HTTPS in Production

```python
auth_settings = AuthSettings(
    issuer_url="https://api.example.com",  # Always HTTPS in production
    # ... other settings
)
```

### 2. Validate Redirect URIs

```python
async def register_client(self, registration_data: dict) -> dict:
    """Register client with redirect URI validation."""
    redirect_uris = registration_data.get("redirect_uris", [])

    # Validate redirect URIs
    for uri in redirect_uris:
        if not uri.startswith("https://"):
            raise ValueError("Redirect URIs must use HTTPS")
        if "localhost" in uri and not uri.startswith("http://localhost"):
            raise ValueError("localhost URIs must use HTTP")

    # ... rest of registration
```

### 3. Implement Token Expiration

```python
async def validate_token(self, token: str) -> dict | None:
    """Validate token with proper expiration handling."""
    token_data = self.tokens.get(token)
    if not token_data:
        return None

    # Check expiration
    if time.time() > token_data.get("expires_at", 0):
        # Clean up expired token
        del self.tokens[token]
        return None

    return token_data
```

### 4. Scope Validation

```python
@mcp.tool()
def admin_tool(ctx) -> str:
    """Tool that requires admin scope."""
    # Check if user has required scope
    token_data = ctx.session.get_token_data()  # Hypothetical method
    scopes = token_data.get("scope", "").split()

    if "admin" not in scopes:
        raise PermissionError("Admin scope required")

    return "Admin operation completed"
```

## Troubleshooting

### Common Issues

1. **Authentication only works with HTTP transports**
   ```python
   # Won't work - stdio doesn't support auth
   mcp.run("stdio")

   # Works - HTTP transports support auth
   mcp.run("streamable-http")
   mcp.run("sse")
   ```

2. **Missing issuer_url configuration**
   ```python
   # Must provide issuer_url
   auth_settings = AuthSettings(
       issuer_url="https://your-server.com"  # Required
   )
   ```

3. **Provider and settings must be paired**
   ```python
   # Both auth_server_provider AND auth must be provided
   mcp = FastMCP(
       "Server",
       auth_server_provider=oauth_provider,  # Required if using auth
       auth=auth_settings                    # Required if using auth
   )
   ```

### Debug Authentication

```python
mcp = FastMCP(
    "Debug Server",
    debug=True,           # Enable debug logging
    log_level="DEBUG",    # Verbose auth logs
    auth_server_provider=oauth_provider,
    auth=auth_settings
)
```
