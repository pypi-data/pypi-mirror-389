"""
AIS Protocol - Authentication and Rate Limiting

Provides JWT and API Key authentication, plus rate limiting for production use.
"""

import asyncio
import hashlib
import hmac
import time
from datetime import datetime, timedelta
from typing import Optional, Dict, Callable, Any, List
from collections import defaultdict
from dataclasses import dataclass

try:
    import jwt
    JWT_AVAILABLE = True
except ImportError:
    JWT_AVAILABLE = False

from .message import AISMessage
from .exceptions import AuthenticationError, RateLimitError


# ============================================================================
# JWT Authentication
# ============================================================================

@dataclass
class JWTConfig:
    """Configuration for JWT authentication."""
    secret_key: str
    algorithm: str = "HS256"
    expiration_minutes: int = 60
    issuer: Optional[str] = None
    audience: Optional[str] = None


class JWTAuth:
    """
    JWT-based authentication for AIS agents.

    Supports token generation, validation, and automatic expiration.
    """

    def __init__(self, config: JWTConfig):
        """
        Initialize JWT authentication.

        Args:
            config: JWT configuration

        Raises:
            ImportError: If PyJWT is not installed
        """
        if not JWT_AVAILABLE:
            raise ImportError("PyJWT is required for JWT authentication. Install with: pip install PyJWT")

        self.config = config

    def generate_token(self, agent_id: str, additional_claims: Optional[Dict[str, Any]] = None) -> str:
        """
        Generate JWT token for an agent.

        Args:
            agent_id: Agent identifier
            additional_claims: Additional JWT claims to include

        Returns:
            JWT token string
        """
        now = datetime.utcnow()
        exp = now + timedelta(minutes=self.config.expiration_minutes)

        payload = {
            "sub": agent_id,
            "iat": now,
            "exp": exp,
        }

        if self.config.issuer:
            payload["iss"] = self.config.issuer

        if self.config.audience:
            payload["aud"] = self.config.audience

        if additional_claims:
            payload.update(additional_claims)

        return jwt.encode(payload, self.config.secret_key, algorithm=self.config.algorithm)

    def validate_token(self, token: str) -> Dict[str, Any]:
        """
        Validate JWT token and extract claims.

        Args:
            token: JWT token string

        Returns:
            Decoded token payload

        Raises:
            AuthenticationError: If token is invalid or expired
        """
        try:
            payload = jwt.decode(
                token,
                self.config.secret_key,
                algorithms=[self.config.algorithm],
                issuer=self.config.issuer,
                audience=self.config.audience
            )
            return payload
        except jwt.ExpiredSignatureError:
            raise AuthenticationError("Token has expired")
        except jwt.InvalidTokenError as e:
            raise AuthenticationError(f"Invalid token: {str(e)}")

    def get_agent_id_from_token(self, token: str) -> str:
        """
        Extract agent ID from JWT token.

        Args:
            token: JWT token string

        Returns:
            Agent ID from token
        """
        payload = self.validate_token(token)
        return payload["sub"]


# ============================================================================
# API Key Authentication
# ============================================================================

@dataclass
class APIKey:
    """API Key with metadata."""
    key_hash: str
    agent_id: str
    name: str
    created_at: datetime
    expires_at: Optional[datetime] = None
    rate_limit: Optional[int] = None  # requests per minute
    scopes: List[str] = None

    def __post_init__(self):
        if self.scopes is None:
            self.scopes = []

    def is_expired(self) -> bool:
        """Check if API key is expired."""
        if self.expires_at is None:
            return False
        return datetime.utcnow() > self.expires_at

    def has_scope(self, scope: str) -> bool:
        """Check if key has required scope."""
        if not self.scopes:  # Empty list means all scopes
            return True
        return scope in self.scopes


class APIKeyAuth:
    """
    API Key authentication for AIS agents.

    Supports key generation, validation, and scope-based access control.
    """

    def __init__(self):
        """Initialize API key authentication."""
        self.keys: Dict[str, APIKey] = {}

    @staticmethod
    def _hash_key(key: str) -> str:
        """Hash API key for secure storage."""
        return hashlib.sha256(key.encode()).hexdigest()

    @staticmethod
    def _generate_key() -> str:
        """Generate random API key."""
        import secrets
        return f"ais_{secrets.token_urlsafe(32)}"

    def create_key(
        self,
        agent_id: str,
        name: str,
        expiration_days: Optional[int] = None,
        rate_limit: Optional[int] = None,
        scopes: Optional[List[str]] = None
    ) -> str:
        """
        Create new API key for an agent.

        Args:
            agent_id: Agent identifier
            name: Human-readable name for the key
            expiration_days: Days until key expires (None = never)
            rate_limit: Requests per minute allowed
            scopes: List of allowed scopes

        Returns:
            Plain text API key (store this securely!)
        """
        key = self._generate_key()
        key_hash = self._hash_key(key)

        expires_at = None
        if expiration_days:
            expires_at = datetime.utcnow() + timedelta(days=expiration_days)

        api_key = APIKey(
            key_hash=key_hash,
            agent_id=agent_id,
            name=name,
            created_at=datetime.utcnow(),
            expires_at=expires_at,
            rate_limit=rate_limit,
            scopes=scopes or []
        )

        self.keys[key_hash] = api_key
        return key

    def validate_key(self, key: str, required_scope: Optional[str] = None) -> APIKey:
        """
        Validate API key and return key metadata.

        Args:
            key: Plain text API key
            required_scope: Scope required for this operation

        Returns:
            APIKey object if valid

        Raises:
            AuthenticationError: If key is invalid, expired, or lacks scope
        """
        key_hash = self._hash_key(key)

        if key_hash not in self.keys:
            raise AuthenticationError("Invalid API key")

        api_key = self.keys[key_hash]

        if api_key.is_expired():
            raise AuthenticationError("API key has expired")

        if required_scope and not api_key.has_scope(required_scope):
            raise AuthenticationError(f"API key lacks required scope: {required_scope}")

        return api_key

    def revoke_key(self, key: str) -> bool:
        """
        Revoke an API key.

        Args:
            key: Plain text API key to revoke

        Returns:
            True if key was revoked, False if not found
        """
        key_hash = self._hash_key(key)
        if key_hash in self.keys:
            del self.keys[key_hash]
            return True
        return False

    def get_agent_id_from_key(self, key: str) -> str:
        """
        Extract agent ID from API key.

        Args:
            key: Plain text API key

        Returns:
            Agent ID associated with key
        """
        api_key = self.validate_key(key)
        return api_key.agent_id


# ============================================================================
# Rate Limiting
# ============================================================================

@dataclass
class RateLimitRule:
    """Rate limit rule configuration."""
    max_requests: int
    window_seconds: int
    scope: str = "global"  # 'global', 'agent', 'ip'


class RateLimiter:
    """
    Token bucket rate limiter for AIS protocol.

    Supports per-agent, per-IP, and global rate limiting.
    """

    def __init__(self, rules: Optional[List[RateLimitRule]] = None):
        """
        Initialize rate limiter.

        Args:
            rules: List of rate limit rules to apply
        """
        self.rules = rules or []
        self._buckets: Dict[str, Dict[str, Any]] = defaultdict(dict)
        self._cleanup_task: Optional[asyncio.Task] = None

    def add_rule(self, rule: RateLimitRule) -> None:
        """Add a rate limit rule."""
        self.rules.append(rule)

    def _get_bucket_key(self, scope: str, identifier: str) -> str:
        """Generate bucket key for rate limit tracking."""
        return f"{scope}:{identifier}"

    def _get_bucket(self, key: str, max_tokens: int) -> Dict[str, Any]:
        """Get or create token bucket."""
        if key not in self._buckets:
            self._buckets[key] = {
                "tokens": max_tokens,
                "max_tokens": max_tokens,
                "last_update": time.time()
            }
        return self._buckets[key]

    def _refill_bucket(self, bucket: Dict[str, Any], window_seconds: int) -> None:
        """Refill tokens in bucket based on elapsed time."""
        now = time.time()
        elapsed = now - bucket["last_update"]

        # Calculate tokens to add based on elapsed time
        tokens_to_add = (elapsed / window_seconds) * bucket["max_tokens"]
        bucket["tokens"] = min(bucket["max_tokens"], bucket["tokens"] + tokens_to_add)
        bucket["last_update"] = now

    async def check_rate_limit(self, agent_id: Optional[str] = None, ip_address: Optional[str] = None) -> None:
        """
        Check if request is within rate limits.

        Args:
            agent_id: Agent identifier for per-agent limits
            ip_address: IP address for per-IP limits

        Raises:
            RateLimitError: If rate limit exceeded
        """
        for rule in self.rules:
            if rule.scope == "global":
                identifier = "global"
            elif rule.scope == "agent" and agent_id:
                identifier = agent_id
            elif rule.scope == "ip" and ip_address:
                identifier = ip_address
            else:
                continue

            key = self._get_bucket_key(rule.scope, identifier)
            bucket = self._get_bucket(key, rule.max_requests)

            # Refill bucket
            self._refill_bucket(bucket, rule.window_seconds)

            # Check if we have tokens
            if bucket["tokens"] < 1:
                retry_after = rule.window_seconds
                raise RateLimitError(
                    f"Rate limit exceeded for {rule.scope}:{identifier}. "
                    f"Limit: {rule.max_requests} requests per {rule.window_seconds}s",
                    retry_after=retry_after
                )

            # Consume token
            bucket["tokens"] -= 1

    async def _cleanup_old_buckets(self) -> None:
        """Background task to cleanup old rate limit buckets."""
        while True:
            await asyncio.sleep(300)  # Every 5 minutes

            now = time.time()
            keys_to_remove = []

            for key, bucket in self._buckets.items():
                # Remove buckets that haven't been used in 1 hour
                if now - bucket["last_update"] > 3600:
                    keys_to_remove.append(key)

            for key in keys_to_remove:
                del self._buckets[key]

    def start_cleanup(self) -> None:
        """Start background cleanup task."""
        if self._cleanup_task is None:
            self._cleanup_task = asyncio.create_task(self._cleanup_old_buckets())

    def stop_cleanup(self) -> None:
        """Stop background cleanup task."""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            self._cleanup_task = None


# ============================================================================
# Authentication Middleware
# ============================================================================

class AuthMiddleware:
    """
    Authentication middleware for AIS agents.

    Supports multiple authentication methods (JWT, API Key) and integrates
    with rate limiting.
    """

    def __init__(
        self,
        jwt_auth: Optional[JWTAuth] = None,
        api_key_auth: Optional[APIKeyAuth] = None,
        rate_limiter: Optional[RateLimiter] = None,
        require_auth: bool = True
    ):
        """
        Initialize authentication middleware.

        Args:
            jwt_auth: JWT authentication handler
            api_key_auth: API Key authentication handler
            rate_limiter: Rate limiter instance
            require_auth: Whether to require authentication
        """
        self.jwt_auth = jwt_auth
        self.api_key_auth = api_key_auth
        self.rate_limiter = rate_limiter
        self.require_auth = require_auth

    async def authenticate_message(
        self,
        message: AISMessage,
        auth_header: Optional[str] = None,
        ip_address: Optional[str] = None
    ) -> Optional[str]:
        """
        Authenticate incoming message.

        Args:
            message: AIS message to authenticate
            auth_header: Authorization header (Bearer token or API key)
            ip_address: Client IP address for rate limiting

        Returns:
            Authenticated agent ID or None if auth not required

        Raises:
            AuthenticationError: If authentication fails
            RateLimitError: If rate limit exceeded
        """
        agent_id = None

        # Extract agent ID from message
        message_agent_id = message.from_agent

        # Try to authenticate if header provided
        if auth_header:
            if auth_header.startswith("Bearer "):
                # JWT authentication
                token = auth_header[7:]
                if self.jwt_auth:
                    agent_id = self.jwt_auth.get_agent_id_from_token(token)
                else:
                    raise AuthenticationError("JWT authentication not configured")

            elif auth_header.startswith("ais_"):
                # API Key authentication
                if self.api_key_auth:
                    agent_id = self.api_key_auth.get_agent_id_from_key(auth_header)
                else:
                    raise AuthenticationError("API Key authentication not configured")

            else:
                raise AuthenticationError("Invalid authorization header format")

            # Verify agent ID matches message
            if agent_id != message_agent_id:
                raise AuthenticationError(
                    f"Authenticated agent ID ({agent_id}) does not match message sender ({message_agent_id})"
                )

        elif self.require_auth:
            raise AuthenticationError("Authentication required but no credentials provided")

        # Check rate limits
        if self.rate_limiter:
            await self.rate_limiter.check_rate_limit(
                agent_id=agent_id or message_agent_id,
                ip_address=ip_address
            )

        return agent_id

    async def __call__(
        self,
        message: AISMessage,
        auth_header: Optional[str] = None,
        ip_address: Optional[str] = None
    ) -> Optional[str]:
        """Make middleware callable."""
        return await self.authenticate_message(message, auth_header, ip_address)
