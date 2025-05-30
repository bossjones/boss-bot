# Security Guide

Comprehensive security guide for FastMCP servers, covering authentication, authorization, input validation, secret management, and security best practices.

## Security Overview

FastMCP servers can handle sensitive data and provide access to system resources. This guide covers essential security practices to protect your servers and users.

### Security Principles

1. **Defense in Depth**: Multiple layers of security controls
2. **Least Privilege**: Grant minimal necessary permissions
3. **Input Validation**: Validate and sanitize all inputs
4. **Secure Defaults**: Security-first configuration
5. **Regular Updates**: Keep dependencies updated

## Authentication & Authorization

### 1. OAuth2 Authentication

**Secure HTTP transport setup:**
```python
import secrets
import time
from typing import Optional
from mcp.server.auth.provider import (
    OAuthAuthorizationServerProvider,
    AccessToken,
    RefreshToken,
    AuthorizationCode
)
from mcp.server.auth.settings import AuthSettings, ClientRegistrationOptions
from mcp.server.fastmcp import FastMCP

class SecureOAuthProvider(OAuthAuthorizationServerProvider):
    """Production-ready OAuth provider with security best practices."""

    def __init__(self):
        # Use secure storage in production (database with encryption)
        self.clients = {}
        self.access_tokens = {}
        self.refresh_tokens = {}
        self.auth_codes = {}
        self.rate_limits = {}  # Track rate limiting

    async def get_client(self, client_id: str) -> Optional[dict]:
        """Get client with security checks."""
        # Rate limiting check
        if await self._is_rate_limited(client_id):
            raise ValueError("Rate limit exceeded")

        return self.clients.get(client_id)

    async def create_authorization_code(self, params) -> str:
        """Create secure authorization code."""
        # Generate cryptographically secure code
        code = secrets.token_urlsafe(64)

        # Store with expiration (short-lived)
        self.auth_codes[code] = AuthorizationCode(
            code=code,
            scopes=params.scopes or [],
            expires_at=time.time() + 300,  # 5 minutes only
            client_id=params.client_id,
            code_challenge=params.code_challenge,
            redirect_uri=params.redirect_uri,
            redirect_uri_provided_explicitly=params.redirect_uri_provided_explicitly
        )

        return code

    async def exchange_code_for_tokens(self, code: str, client_id: str) -> Optional[dict]:
        """Exchange code for tokens with security validation."""
        auth_code = self.auth_codes.get(code)
        if not auth_code:
            return None

        # Validate code hasn't expired
        if auth_code.expires_at < time.time():
            del self.auth_codes[code]  # Clean up expired code
            return None

        # Validate client_id matches
        if auth_code.client_id != client_id:
            return None

        # Generate secure tokens
        access_token = secrets.token_urlsafe(64)
        refresh_token = secrets.token_urlsafe(64)

        # Store tokens with expiration
        self.access_tokens[access_token] = AccessToken(
            token=access_token,
            client_id=client_id,
            scopes=auth_code.scopes,
            expires_at=int(time.time() + 3600)  # 1 hour
        )

        self.refresh_tokens[refresh_token] = RefreshToken(
            token=refresh_token,
            client_id=client_id,
            scopes=auth_code.scopes,
            expires_at=int(time.time() + 86400 * 30)  # 30 days
        )

        # Clean up used authorization code
        del self.auth_codes[code]

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "Bearer",
            "expires_in": 3600,
            "scope": " ".join(auth_code.scopes)
        }

    async def load_access_token(self, token: str) -> Optional[AccessToken]:
        """Load and validate access token."""
        access_token = self.access_tokens.get(token)
        if not access_token:
            return None

        # Check expiration
        if access_token.expires_at and access_token.expires_at < time.time():
            del self.access_tokens[token]  # Clean up expired token
            return None

        return access_token

    async def _is_rate_limited(self, client_id: str) -> bool:
        """Simple rate limiting implementation."""
        current_time = time.time()
        window = 60  # 1 minute window
        max_requests = 100

        if client_id not in self.rate_limits:
            self.rate_limits[client_id] = []

        # Clean old requests
        self.rate_limits[client_id] = [
            req_time for req_time in self.rate_limits[client_id]
            if current_time - req_time < window
        ]

        # Check limit
        if len(self.rate_limits[client_id]) >= max_requests:
            return True

        # Add current request
        self.rate_limits[client_id].append(current_time)
        return False

# Configure secure authentication
auth_provider = SecureOAuthProvider()
auth_settings = AuthSettings(
    issuer_url="https://your-domain.com",
    required_scopes=["read", "write"],
    client_registration_options=ClientRegistrationOptions(
        enabled=True,
        valid_scopes=["read", "write", "admin"],
        default_scopes=["read"]
    )
)

mcp = FastMCP(
    "Secure Server",
    auth_server_provider=auth_provider,
    auth=auth_settings
)
```

### 2. Scope-based Authorization

**Implement granular permissions:**
```python
from mcp.server.fastmcp import Context

def require_scope(required_scope: str):
    """Decorator to require specific OAuth scope."""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Find context in arguments
            ctx = None
            for arg in args:
                if isinstance(arg, Context):
                    ctx = arg
                    break

            if not ctx:
                raise ValueError("Context required for authorization")

            # Check if user has required scope
            # This would be implemented based on your auth system
            user_scopes = getattr(ctx, 'user_scopes', [])
            if required_scope not in user_scopes:
                raise PermissionError(f"Scope '{required_scope}' required")

            return await func(*args, **kwargs)
        return wrapper
    return decorator

@mcp.tool()
@require_scope("admin")
async def admin_operation(data: str, ctx: Context) -> str:
    """Operation requiring admin privileges."""
    ctx.info("Admin operation executed")
    return f"Admin processed: {data}"

@mcp.tool()
@require_scope("read")
async def read_operation(ctx: Context) -> str:
    """Operation requiring read privileges."""
    return "Public data"
```

## Input Validation & Sanitization

### 1. Pydantic Validation

**Comprehensive input validation:**
```python
from pydantic import BaseModel, Field, validator, EmailStr
from typing import List, Optional
import re
import html

class SecureUserInput(BaseModel):
    """Secure user input model with validation."""

    name: str = Field(
        min_length=1,
        max_length=100,
        regex=r"^[a-zA-Z0-9\s\-_]+$"  # Only alphanumeric, spaces, hyphens, underscores
    )
    email: EmailStr
    age: int = Field(ge=13, le=120)  # Age restrictions
    phone: Optional[str] = Field(
        None,
        regex=r"^\+?1?\d{9,15}$"  # International phone format
    )
    bio: Optional[str] = Field(None, max_length=500)
    tags: List[str] = Field(default_factory=list, max_items=10)

    @validator('name')
    def validate_name(cls, v):
        """Additional name validation."""
        # Remove any potential HTML/script content
        cleaned = html.escape(v.strip())
        if cleaned != v.strip():
            raise ValueError("Invalid characters in name")
        return cleaned

    @validator('bio')
    def validate_bio(cls, v):
        """Sanitize bio content."""
        if v:
            # Remove HTML tags and escape content
            cleaned = html.escape(v.strip())
            # Check for suspicious patterns
            suspicious_patterns = [
                r'<script', r'javascript:', r'data:', r'vbscript:',
                r'onload=', r'onerror=', r'onclick='
            ]
            v_lower = v.lower()
            for pattern in suspicious_patterns:
                if re.search(pattern, v_lower):
                    raise ValueError("Potentially unsafe content in bio")
            return cleaned
        return v

    @validator('tags')
    def validate_tags(cls, v):
        """Validate tag list."""
        if v:
            for tag in v:
                if not isinstance(tag, str) or len(tag) > 50:
                    raise ValueError("Invalid tag format")
                # Sanitize each tag
                if html.escape(tag) != tag:
                    raise ValueError("Invalid characters in tag")
        return v

@mcp.tool()
async def create_user(user_data: SecureUserInput, ctx: Context) -> str:
    """Create user with validated input."""
    ctx.info(f"Creating user: {user_data.name}")

    # Additional business logic validation
    if user_data.name.lower() in ['admin', 'root', 'system']:
        raise ValueError("Reserved username")

    # Process validated data
    return f"User {user_data.name} created successfully"
```

### 2. File Upload Security

**Secure file handling:**
```python
import os
import mimetypes
from pathlib import Path
import magic  # python-magic for file type detection

class SecureFileHandler:
    """Secure file upload and processing."""

    ALLOWED_TYPES = {
        'image/jpeg', 'image/png', 'image/gif', 'image/webp',
        'text/plain', 'text/csv', 'application/json',
        'application/pdf'
    }

    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    UPLOAD_DIR = Path("/secure/uploads")

    def __init__(self):
        self.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

    def validate_file(self, file_data: bytes, filename: str) -> bool:
        """Comprehensive file validation."""
        # Check file size
        if len(file_data) > self.MAX_FILE_SIZE:
            raise ValueError(f"File too large: {len(file_data)} bytes")

        # Validate filename
        if not self._is_safe_filename(filename):
            raise ValueError("Unsafe filename")

        # Check MIME type by content (not extension)
        detected_type = magic.from_buffer(file_data, mime=True)
        if detected_type not in self.ALLOWED_TYPES:
            raise ValueError(f"File type not allowed: {detected_type}")

        # Additional checks for images
        if detected_type.startswith('image/'):
            return self._validate_image(file_data)

        return True

    def _is_safe_filename(self, filename: str) -> bool:
        """Check filename safety."""
        if not filename or len(filename) > 255:
            return False

        # Check for path traversal
        if '..' in filename or '/' in filename or '\\' in filename:
            return False

        # Check for null bytes or control characters
        if any(ord(c) < 32 for c in filename):
            return False

        # Check for executable extensions
        dangerous_extensions = {
            '.exe', '.bat', '.cmd', '.com', '.scr', '.vbs', '.js',
            '.jar', '.php', '.py', '.sh', '.bash', '.ps1'
        }
        file_ext = Path(filename).suffix.lower()
        if file_ext in dangerous_extensions:
            return False

        return True

    def _validate_image(self, file_data: bytes) -> bool:
        """Additional validation for images."""
        try:
            from PIL import Image
            import io

            # Try to open and verify image
            img = Image.open(io.BytesIO(file_data))
            img.verify()  # Verify it's a valid image

            # Check dimensions (prevent decompression bombs)
            if img.size[0] * img.size[1] > 100_000_000:  # 100MP limit
                raise ValueError("Image too large")

            return True
        except Exception:
            raise ValueError("Invalid image file")

    def save_file(self, file_data: bytes, filename: str) -> str:
        """Securely save file."""
        self.validate_file(file_data, filename)

        # Generate secure filename
        safe_filename = secrets.token_hex(16) + "_" + filename
        file_path = self.UPLOAD_DIR / safe_filename

        # Write file with restricted permissions
        with open(file_path, 'wb') as f:
            f.write(file_data)

        # Set secure permissions
        os.chmod(file_path, 0o644)

        return str(file_path)

file_handler = SecureFileHandler()

@mcp.tool()
async def upload_file(file_data: str, filename: str, ctx: Context) -> str:
    """Secure file upload tool."""
    try:
        # Decode base64 file data
        import base64
        decoded_data = base64.b64decode(file_data)

        # Validate and save file
        file_path = file_handler.save_file(decoded_data, filename)

        ctx.info(f"File uploaded securely: {filename}")
        return f"File saved: {file_path}"

    except Exception as e:
        ctx.error(f"File upload failed: {e}")
        raise ValueError(f"Upload failed: {e}")
```

## Secret Management

### 1. Environment Variables

**Secure secret handling:**
```python
import os
from pydantic import BaseModel, Field, validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class SecuritySettings(BaseSettings):
    """Secure settings management."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

    # Database credentials
    DB_PASSWORD: str = Field(..., description="Database password")
    DB_HOST: str = Field(default="localhost")
    DB_USER: str = Field(default="user")

    # API keys
    OPENAI_API_KEY: Optional[str] = Field(None, description="OpenAI API key")
    STRIPE_SECRET_KEY: Optional[str] = Field(None, description="Stripe secret key")

    # JWT secrets
    JWT_SECRET_KEY: str = Field(..., min_length=32, description="JWT signing key")

    # Encryption keys
    ENCRYPTION_KEY: str = Field(..., min_length=32, description="Data encryption key")

    @validator('JWT_SECRET_KEY', 'ENCRYPTION_KEY')
    def validate_keys(cls, v):
        """Ensure keys are sufficiently random."""
        if len(v) < 32:
            raise ValueError("Key must be at least 32 characters")
        # Check for common weak patterns
        if v in ['password', '123456', 'secret', 'key']:
            raise ValueError("Key is too weak")
        return v

    def get_database_url(self) -> str:
        """Construct database URL securely."""
        return f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}/mydb"

# Load settings with validation
settings = SecuritySettings()

@mcp.tool()
async def secure_api_call(query: str, ctx: Context) -> str:
    """Make API call with secure key management."""
    if not settings.OPENAI_API_KEY:
        raise ValueError("API key not configured")

    # Use the key securely
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.openai.com/v1/completions",
            headers={
                "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
                "Content-Type": "application/json"
            },
            json={"prompt": query, "max_tokens": 100}
        )

    # Don't log the response content (might contain sensitive data)
    ctx.info("API call completed successfully")
    return "Response received"
```

### 2. Encryption at Rest

**Encrypt sensitive data:**
```python
from cryptography.fernet import Fernet
import base64
import json

class DataEncryption:
    """Handle data encryption and decryption."""

    def __init__(self, key: str):
        # Derive key from settings
        key_bytes = key.encode()[:32].ljust(32, b'0')  # Ensure 32 bytes
        self.fernet = Fernet(base64.urlsafe_b64encode(key_bytes))

    def encrypt(self, data: str) -> str:
        """Encrypt sensitive data."""
        encrypted_bytes = self.fernet.encrypt(data.encode())
        return base64.urlsafe_b64encode(encrypted_bytes).decode()

    def decrypt(self, encrypted_data: str) -> str:
        """Decrypt sensitive data."""
        encrypted_bytes = base64.urlsafe_b64decode(encrypted_data.encode())
        decrypted_bytes = self.fernet.decrypt(encrypted_bytes)
        return decrypted_bytes.decode()

encryption = DataEncryption(settings.ENCRYPTION_KEY)

@mcp.tool()
async def store_sensitive_data(user_id: int, sensitive_info: str, ctx: Context) -> str:
    """Store sensitive data with encryption."""
    try:
        # Encrypt before storing
        encrypted_info = encryption.encrypt(sensitive_info)

        # Store in database (encrypted)
        # await db.execute(
        #     "INSERT INTO user_data (user_id, encrypted_data) VALUES ($1, $2)",
        #     user_id, encrypted_info
        # )

        ctx.info(f"Sensitive data stored for user {user_id}")
        return "Data stored securely"

    except Exception as e:
        ctx.error(f"Failed to store data: {e}")
        raise
```

## Network Security

### 1. HTTPS Configuration

**Secure transport configuration:**
```python
import ssl
from pathlib import Path

def create_ssl_context() -> ssl.SSLContext:
    """Create secure SSL context."""
    context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)

    # Load certificates
    cert_file = Path("/path/to/cert.pem")
    key_file = Path("/path/to/key.pem")

    if cert_file.exists() and key_file.exists():
        context.load_cert_chain(cert_file, key_file)

    # Security settings
    context.minimum_version = ssl.TLSVersion.TLSv1_2
    context.set_ciphers('ECDHE+AESGCM:ECDHE+CHACHA20:DHE+AESGCM:DHE+CHACHA20:!aNULL:!MD5:!DSS')

    return context

# Use with uvicorn in production
"""
uvicorn main:app \\
    --host 0.0.0.0 \\
    --port 443 \\
    --ssl-keyfile /path/to/key.pem \\
    --ssl-certfile /path/to/cert.pem \\
    --ssl-version 3 \\
    --ssl-ciphers TLSv1.2
"""
```

### 2. Request Rate Limiting

**Implement rate limiting:**
```python
import time
from collections import defaultdict, deque
from typing import Dict
import asyncio

class RateLimiter:
    """Token bucket rate limiter."""

    def __init__(self, max_requests: int = 100, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.clients: Dict[str, deque] = defaultdict(deque)
        self.lock = asyncio.Lock()

    async def is_allowed(self, client_id: str) -> bool:
        """Check if request is allowed."""
        async with self.lock:
            current_time = time.time()
            client_requests = self.clients[client_id]

            # Remove old requests outside window
            while client_requests and client_requests[0] < current_time - self.window_seconds:
                client_requests.popleft()

            # Check if under limit
            if len(client_requests) >= self.max_requests:
                return False

            # Add current request
            client_requests.append(current_time)
            return True

rate_limiter = RateLimiter(max_requests=100, window_seconds=60)

def rate_limited(func):
    """Decorator to enforce rate limiting."""
    async def wrapper(*args, **kwargs):
        # Extract client ID from context
        ctx = None
        for arg in args:
            if isinstance(arg, Context):
                ctx = arg
                break

        client_id = ctx.client_id if ctx else "unknown"

        if not await rate_limiter.is_allowed(client_id):
            raise ValueError("Rate limit exceeded")

        return await func(*args, **kwargs)
    return wrapper

@mcp.tool()
@rate_limited
async def rate_limited_operation(data: str, ctx: Context) -> str:
    """Operation with rate limiting."""
    return f"Processed: {data}"
```

## Security Monitoring

### 1. Security Logging

**Comprehensive security logging:**
```python
import logging
import json
from datetime import datetime
from typing import Dict, Any

class SecurityLogger:
    """Security-focused logging."""

    def __init__(self):
        self.logger = logging.getLogger("security")
        self.logger.setLevel(logging.INFO)

        # Create file handler for security logs
        handler = logging.FileHandler("/var/log/fastmcp/security.log")
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)

    def log_auth_attempt(self, client_id: str, success: bool, ip_address: str = None):
        """Log authentication attempts."""
        event = {
            "event_type": "auth_attempt",
            "client_id": client_id,
            "success": success,
            "ip_address": ip_address,
            "timestamp": datetime.utcnow().isoformat()
        }

        level = logging.INFO if success else logging.WARNING
        self.logger.log(level, json.dumps(event))

    def log_permission_denied(self, client_id: str, resource: str, action: str):
        """Log permission denied events."""
        event = {
            "event_type": "permission_denied",
            "client_id": client_id,
            "resource": resource,
            "action": action,
            "timestamp": datetime.utcnow().isoformat()
        }
        self.logger.warning(json.dumps(event))

    def log_suspicious_activity(self, client_id: str, activity: str, details: Dict[str, Any]):
        """Log suspicious activities."""
        event = {
            "event_type": "suspicious_activity",
            "client_id": client_id,
            "activity": activity,
            "details": details,
            "timestamp": datetime.utcnow().isoformat()
        }
        self.logger.error(json.dumps(event))

security_logger = SecurityLogger()

@mcp.tool()
async def monitored_operation(data: str, ctx: Context) -> str:
    """Operation with security monitoring."""
    client_id = ctx.client_id or "unknown"

    # Check for suspicious patterns
    if any(pattern in data.lower() for pattern in ['<script', 'javascript:', 'eval(']):
        security_logger.log_suspicious_activity(
            client_id,
            "potential_xss_attempt",
            {"input_data": data[:100]}  # Log partial data only
        )
        raise ValueError("Suspicious input detected")

    # Log successful operation
    security_logger.log_auth_attempt(client_id, True)

    return f"Safely processed: {html.escape(data)}"
```

### 2. Anomaly Detection

**Basic anomaly detection:**
```python
from collections import defaultdict
import statistics

class AnomalyDetector:
    """Detect unusual patterns in requests."""

    def __init__(self):
        self.request_patterns = defaultdict(list)
        self.alert_threshold = 3.0  # Standard deviations

    def record_request(self, client_id: str, endpoint: str, response_time: float):
        """Record request metrics."""
        key = f"{client_id}:{endpoint}"
        self.request_patterns[key].append({
            "response_time": response_time,
            "timestamp": time.time()
        })

        # Keep only recent data (last 1000 requests)
        if len(self.request_patterns[key]) > 1000:
            self.request_patterns[key] = self.request_patterns[key][-1000:]

    def detect_anomalies(self, client_id: str, endpoint: str, response_time: float) -> bool:
        """Detect if current request is anomalous."""
        key = f"{client_id}:{endpoint}"
        pattern = self.request_patterns[key]

        if len(pattern) < 10:  # Need baseline data
            return False

        # Calculate statistics
        times = [r["response_time"] for r in pattern[-100:]]  # Last 100 requests
        mean_time = statistics.mean(times)
        std_dev = statistics.stdev(times) if len(times) > 1 else 0

        # Check if current request is anomalous
        if std_dev > 0:
            z_score = abs(response_time - mean_time) / std_dev
            return z_score > self.alert_threshold

        return False

anomaly_detector = AnomalyDetector()

def monitor_performance(func):
    """Decorator to monitor and detect anomalies."""
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        ctx = None

        # Find context
        for arg in args:
            if isinstance(arg, Context):
                ctx = arg
                break

        try:
            result = await func(*args, **kwargs)
            response_time = time.time() - start_time

            # Record and check for anomalies
            if ctx:
                client_id = ctx.client_id or "unknown"
                endpoint = func.__name__

                anomaly_detector.record_request(client_id, endpoint, response_time)

                if anomaly_detector.detect_anomalies(client_id, endpoint, response_time):
                    security_logger.log_suspicious_activity(
                        client_id,
                        "performance_anomaly",
                        {
                            "endpoint": endpoint,
                            "response_time": response_time,
                            "anomaly_type": "slow_response"
                        }
                    )

            return result

        except Exception as e:
            response_time = time.time() - start_time
            # Log failed requests
            if ctx:
                security_logger.log_suspicious_activity(
                    ctx.client_id or "unknown",
                    "request_failure",
                    {
                        "endpoint": func.__name__,
                        "error": str(e),
                        "response_time": response_time
                    }
                )
            raise

    return wrapper

@mcp.tool()
@monitor_performance
async def monitored_tool(data: str, ctx: Context) -> str:
    """Tool with performance monitoring."""
    await asyncio.sleep(0.1)  # Simulate work
    return f"Processed: {data}"
```

## Security Best Practices

### 1. Secure Coding Practices

```python
# ✅ Good: Input validation and sanitization
@mcp.tool()
async def secure_search(query: str, ctx: Context) -> list[str]:
    """Secure search with input validation."""
    # Validate input
    if not query or len(query) > 1000:
        raise ValueError("Invalid query length")

    # Sanitize input
    safe_query = html.escape(query.strip())

    # Use parameterized queries
    results = await db.fetch(
        "SELECT title FROM articles WHERE title ILIKE $1 LIMIT 10",
        f"%{safe_query}%"
    )

    return [row["title"] for row in results]

# ✅ Good: Proper error handling without information disclosure
@mcp.tool()
async def secure_user_lookup(user_id: int, ctx: Context) -> dict:
    """Secure user lookup."""
    try:
        if user_id <= 0:
            raise ValueError("Invalid user ID")

        user = await db.fetchrow("SELECT id, name FROM users WHERE id = $1", user_id)
        if not user:
            return {"error": "User not found"}  # Generic message

        return {"id": user["id"], "name": user["name"]}

    except Exception as e:
        # Log detailed error for debugging
        ctx.error(f"User lookup failed for ID {user_id}: {e}")
        # Return generic error to client
        return {"error": "Lookup failed"}

# ✅ Good: Secure file operations
@mcp.tool()
async def secure_file_read(filename: str, ctx: Context) -> str:
    """Secure file reading with path validation."""
    # Validate filename
    if not filename or '..' in filename or '/' in filename:
        raise ValueError("Invalid filename")

    # Restrict to safe directory
    safe_dir = Path("/app/data")
    file_path = safe_dir / filename

    # Ensure path is within safe directory
    if not str(file_path.resolve()).startswith(str(safe_dir.resolve())):
        raise ValueError("Path traversal attempt")

    # Check file exists and is readable
    if not file_path.exists() or not file_path.is_file():
        raise ValueError("File not found")

    # Read with size limit
    if file_path.stat().st_size > 1024 * 1024:  # 1MB limit
        raise ValueError("File too large")

    return file_path.read_text(encoding='utf-8')
```

### 2. Security Don'ts

```python
# ❌ Bad: No input validation
@mcp.tool()
async def insecure_search(query: str) -> list[str]:
    # SQL injection vulnerability
    results = await db.fetch(f"SELECT * FROM articles WHERE title LIKE '%{query}%'")
    return [row["title"] for row in results]

# ❌ Bad: Information disclosure in errors
@mcp.tool()
async def insecure_database_operation(user_id: int) -> dict:
    try:
        result = await db.fetchrow("SELECT * FROM sensitive_table WHERE id = $1", user_id)
        return dict(result)
    except Exception as e:
        # Exposes internal information
        return {"error": f"Database error: {e}"}

# ❌ Bad: Hardcoded secrets
@mcp.tool()
async def insecure_api_call() -> str:
    api_key = "sk-1234567890abcdef"  # Never hardcode secrets
    # Use the API key...

# ❌ Bad: No path validation
@mcp.tool()
async def insecure_file_read(filepath: str) -> str:
    # Path traversal vulnerability
    with open(filepath, 'r') as f:
        return f.read()

# ❌ Bad: Logging sensitive data
@mcp.tool()
async def insecure_logging(password: str, ctx: Context) -> str:
    ctx.info(f"User password: {password}")  # Never log secrets
    return "Password updated"
```

## Security Checklist

### Development Phase
- [ ] Input validation on all user inputs
- [ ] Output encoding/escaping
- [ ] Parameterized database queries
- [ ] Secure secret management
- [ ] Error handling without information disclosure
- [ ] Path traversal protection
- [ ] File upload restrictions
- [ ] Rate limiting implementation

### Deployment Phase
- [ ] HTTPS/TLS configuration
- [ ] Security headers configuration
- [ ] OAuth2 authentication setup
- [ ] Database connection encryption
- [ ] Log security configuration
- [ ] Monitoring and alerting setup
- [ ] Regular security updates
- [ ] Backup encryption

### Operations Phase
- [ ] Regular security audits
- [ ] Dependency vulnerability scanning
- [ ] Log monitoring for suspicious activity
- [ ] Access review and cleanup
- [ ] Incident response procedures
- [ ] Security training for team
- [ ] Penetration testing
- [ ] Compliance validation

This security guide provides comprehensive protection strategies for FastMCP servers in production environments.
