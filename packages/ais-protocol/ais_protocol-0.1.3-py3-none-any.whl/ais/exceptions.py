"""
AIS Protocol Exceptions

Exception hierarchy for the AIS protocol implementation.
All exceptions inherit from AISException for easy catching.
"""

from typing import Optional, Dict, Any


class AISException(Exception):
    """
    Base exception for AIS protocol.

    All AIS-specific exceptions inherit from this class to allow
    catching all protocol-related errors with a single except clause.
    """

    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details or {}

    def __str__(self) -> str:
        if self.error_code:
            return f"[{self.error_code}] {self.message}"
        return self.message

    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for serialization."""
        result: Dict[str, Any] = {
            "error_message": self.message,
            "error_type": self.__class__.__name__
        }
        if self.error_code:
            result["error_code"] = self.error_code
        if self.details:
            result["details"] = self.details
        return result


class ValidationError(AISException):
    """
    Message validation failed.

    Raised when a message does not conform to the AIS protocol specification,
    such as missing required fields, invalid types, or schema violations.
    """

    def __init__(
        self,
        message: str,
        field: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            error_code="validation_error",
            details=details or {}
        )
        if field:
            self.details["field"] = field


class AuthenticationError(AISException):
    """
    Authentication failed.

    Raised when authentication credentials are invalid, expired,
    or missing when required.
    """

    def __init__(
        self,
        message: str,
        auth_type: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            error_code="authentication_failed",
            details=details or {}
        )
        if auth_type:
            self.details["auth_type"] = auth_type


class CapabilityError(AISException):
    """
    Capability execution failed.

    Raised when a capability handler encounters an error during execution.
    This is different from unknown capabilities (which raise ValidationError).
    """

    def __init__(
        self,
        message: str,
        capability: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            error_code="capability_error",
            details=details or {}
        )
        if capability:
            self.details["capability"] = capability


class SessionError(AISException):
    """
    Session-related error.

    Raised when there are issues with session management, such as
    expired sessions, invalid session IDs, or session state errors.
    """

    def __init__(
        self,
        message: str,
        session_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            error_code="session_error",
            details=details or {}
        )
        if session_id:
            self.details["session_id"] = session_id


class TransportError(AISException):
    """
    Transport layer error.

    Raised when there are network-level issues, such as connection
    failures, timeouts, or HTTP errors.
    """

    def __init__(
        self,
        message: str,
        transport_type: Optional[str] = None,
        status_code: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            error_code="transport_error",
            details=details or {}
        )
        if transport_type:
            self.details["transport_type"] = transport_type
        if status_code:
            self.details["status_code"] = status_code


class TimeoutError(AISException):
    """
    Operation timed out.

    Raised when an operation exceeds its configured timeout period.
    """

    def __init__(
        self,
        message: str,
        timeout_seconds: Optional[float] = None,
        operation: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            error_code="timeout",
            details=details or {}
        )
        if timeout_seconds is not None:
            self.details["timeout_seconds"] = timeout_seconds
        if operation:
            self.details["operation"] = operation


class ProtocolError(AISException):
    """
    Protocol-level error.

    Raised when there are violations of the AIS protocol, such as
    unsupported versions or invalid message sequences.
    """

    def __init__(
        self,
        message: str,
        protocol_version: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            error_code="protocol_error",
            details=details or {}
        )
        if protocol_version:
            self.details["protocol_version"] = protocol_version


class RateLimitError(AISException):
    """
    Rate limit exceeded.

    Raised when an agent exceeds its configured rate limits.
    """

    def __init__(
        self,
        message: str,
        limit: Optional[int] = None,
        retry_after: Optional[float] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            error_code="rate_limited",
            details=details or {}
        )
        self.limit = limit
        self.retry_after = retry_after
        if limit is not None:
            self.details["limit"] = limit
        if retry_after is not None:
            self.details["retry_after"] = retry_after
