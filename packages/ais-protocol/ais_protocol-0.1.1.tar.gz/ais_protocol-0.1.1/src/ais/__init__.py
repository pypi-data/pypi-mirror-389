"""
AIS Protocol - Agent Interface Standard

A production-ready protocol for AI agent-to-agent communication.
"""

__version__ = "0.1.0"
__author__ = "AIS Protocol Contributors"
__license__ = "MIT"

# Core message types
from .message import AISMessage, MessageType

# Validation
from .validation import MessageValidator, InputSanitizer

# Transport
from .transport import HTTPTransport, WebSocketTransport, CombinedTransport

# Agent
from .agent import AISAgent, Capability, Session

# Authentication
from .auth import (
    JWTAuth,
    JWTConfig,
    APIKeyAuth,
    APIKey,
    RateLimiter,
    RateLimitRule,
    AuthMiddleware,
)

# Client
from .client import (
    AISClient,
    RetryConfig,
    RetryStrategy,
    ConnectionPool,
)

# Observability
from .observability import (
    StructuredFormatter,
    setup_structured_logging,
    Metrics,
    MetricPoint,
    Timer,
)

# Exceptions
from .exceptions import (
    AISException,
    ValidationError,
    AuthenticationError,
    CapabilityError,
    SessionError,
    TransportError,
    TimeoutError,
    ProtocolError,
    RateLimitError,
)

# Constants
from .constants import AIS_VERSION

__all__ = [
    # Version
    "__version__",
    # Messages
    "AISMessage",
    "MessageType",
    # Validation
    "MessageValidator",
    "InputSanitizer",
    # Transport
    "HTTPTransport",
    "WebSocketTransport",
    "CombinedTransport",
    # Agent
    "AISAgent",
    "Capability",
    "Session",
    # Authentication
    "JWTAuth",
    "JWTConfig",
    "APIKeyAuth",
    "APIKey",
    "RateLimiter",
    "RateLimitRule",
    "AuthMiddleware",
    # Client
    "AISClient",
    "RetryConfig",
    "RetryStrategy",
    "ConnectionPool",
    # Observability
    "StructuredFormatter",
    "setup_structured_logging",
    "Metrics",
    "MetricPoint",
    "Timer",
    # Exceptions
    "AISException",
    "ValidationError",
    "AuthenticationError",
    "CapabilityError",
    "SessionError",
    "TransportError",
    "TimeoutError",
    "ProtocolError",
    "RateLimitError",
    # Constants
    "AIS_VERSION",
]
