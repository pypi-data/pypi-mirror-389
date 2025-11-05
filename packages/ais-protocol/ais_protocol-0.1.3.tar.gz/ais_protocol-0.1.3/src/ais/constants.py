"""
AIS Protocol Constants

Shared constants used throughout the AIS protocol implementation.
"""

from typing import Final

# Protocol version
AIS_VERSION: Final[str] = "0.1"

# Default timeouts (in seconds)
DEFAULT_SESSION_TIMEOUT_MINUTES: Final[int] = 30
DEFAULT_REQUEST_TIMEOUT_SECONDS: Final[int] = 30
DEFAULT_CONNECTION_TIMEOUT_SECONDS: Final[int] = 10

# Rate limiting defaults
DEFAULT_RATE_LIMIT_REQUESTS_PER_MINUTE: Final[int] = 60

# Input validation limits
MAX_STRING_LENGTH: Final[int] = 100_000  # 100KB
MAX_ARRAY_LENGTH: Final[int] = 1_000
MAX_OBJECT_DEPTH: Final[int] = 10
MAX_MESSAGE_SIZE_BYTES: Final[int] = 10_000_000  # 10MB

# Transport defaults
DEFAULT_HTTP_HOST: Final[str] = "0.0.0.0"
DEFAULT_HTTP_PORT: Final[int] = 8000

# Endpoints
AIS_HTTP_ENDPOINT: Final[str] = "/ais/v0.1/message"
AIS_WEBSOCKET_ENDPOINT: Final[str] = "/ais/v0.1/socket"
AIS_HEALTH_ENDPOINT: Final[str] = "/health"

# Authentication
JWT_ALGORITHM: Final[str] = "HS256"
DEFAULT_JWT_EXPIRY_HOURS: Final[int] = 24

# Retry configuration
DEFAULT_MAX_RETRIES: Final[int] = 3
DEFAULT_BASE_DELAY: Final[float] = 1.0
DEFAULT_MAX_DELAY: Final[float] = 30.0
DEFAULT_EXPONENTIAL_BASE: Final[float] = 2.0

# Session cleanup
SESSION_CLEANUP_INTERVAL_SECONDS: Final[int] = 60

# Error codes (from protocol specification)
ERROR_CODE_UNSUPPORTED_VERSION: Final[str] = "unsupported_version"
ERROR_CODE_UNKNOWN_CAPABILITY: Final[str] = "unknown_capability"
ERROR_CODE_INVALID_PARAMETERS: Final[str] = "invalid_parameters"
ERROR_CODE_AUTHENTICATION_FAILED: Final[str] = "authentication_failed"
ERROR_CODE_RATE_LIMITED: Final[str] = "rate_limited"
ERROR_CODE_TIMEOUT: Final[str] = "timeout"
ERROR_CODE_INTERNAL_ERROR: Final[str] = "internal_error"
ERROR_CODE_SESSION_EXPIRED: Final[str] = "session_expired"
ERROR_CODE_CAPABILITY_ERROR: Final[str] = "capability_error"
