"""
AIS Protocol Message Layer

Core message types and builder methods for the AIS protocol.
All communication in AIS happens through structured messages.
"""

from __future__ import annotations

from enum import Enum
from typing import Dict, Any, Optional, List, Union
from datetime import datetime, timezone
from uuid import uuid4
import json

from pydantic import BaseModel, Field, field_validator, ConfigDict

from .constants import AIS_VERSION
from .exceptions import ValidationError


class MessageType(str, Enum):
    """
    AIS Protocol Message Types

    Defines all valid message types in the AIS protocol v0.1.
    """

    HANDSHAKE = "handshake"
    CAPABILITY_DECLARATION = "capability_declaration"
    REQUEST = "request"
    RESPONSE = "response"
    ERROR = "error"
    STREAM_START = "stream_start"
    STREAM_CHUNK = "stream_chunk"
    STREAM_END = "stream_end"
    SESSION_END = "session_end"


class AISMessage(BaseModel):
    """
    Core AIS message structure.

    All messages in the AIS protocol follow this structure, with
    type-specific data contained in the payload field.

    Attributes:
        ais_version: Protocol version (currently "0.1")
        message_type: Type of message (from MessageType enum)
        message_id: Unique identifier for this message (UUID v4)
        session_id: Session identifier (UUID v4)
        timestamp: ISO 8601 timestamp with timezone
        from_agent: Sender agent ID (format: agent://domain/path/name)
        to_agent: Recipient agent ID (format: agent://domain/path/name)
        payload: Message-specific data
    """

    model_config = ConfigDict(
        # Allow arbitrary types for flexibility
        arbitrary_types_allowed=True,
        # Validate on assignment
        validate_assignment=True,
        # Use enum values in dict
        use_enum_values=True,
        # Allow using both field name and alias
        populate_by_name=True,
    )

    ais_version: str = Field(
        default=AIS_VERSION,
        description="AIS protocol version",
        pattern=r"^\d+\.\d+$"
    )
    message_type: MessageType = Field(
        description="Type of message"
    )
    message_id: str = Field(
        default_factory=lambda: str(uuid4()),
        description="Unique message identifier",
        pattern=r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
    )
    session_id: str = Field(
        description="Session identifier",
        pattern=r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
    )
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
        description="ISO 8601 timestamp with timezone"
    )
    from_agent: str = Field(
        alias="from",
        description="Sender agent ID",
        pattern=r"^agent://.+"
    )
    to_agent: str = Field(
        alias="to",
        description="Recipient agent ID",
        pattern=r"^agent://.+"
    )
    payload: Dict[str, Any] = Field(
        description="Message-specific data"
    )

    @field_validator('timestamp')
    @classmethod
    def validate_timestamp(cls, v: str) -> str:
        """Validate timestamp format."""
        try:
            # Ensure it's a valid ISO 8601 timestamp
            if v.endswith('Z'):
                datetime.fromisoformat(v.replace('Z', '+00:00'))
            else:
                datetime.fromisoformat(v)
            return v
        except ValueError as e:
            raise ValidationError(f"Invalid timestamp format: {e}")

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert message to JSON-serializable dictionary.

        Returns:
            Dictionary representation of the message with 'from' and 'to' keys.
        """
        data = self.model_dump(by_alias=True)
        return data

    def to_json(self, indent: int = 2) -> str:
        """
        Serialize message to JSON string.

        Args:
            indent: Number of spaces for indentation (default: 2)

        Returns:
            JSON string representation of the message
        """
        return json.dumps(self.to_dict(), indent=indent)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> AISMessage:
        """
        Parse message from dictionary.

        Args:
            data: Dictionary containing message data

        Returns:
            AISMessage instance

        Raises:
            ValidationError: If data is invalid
        """
        try:
            return cls(**data)
        except Exception as e:
            raise ValidationError(f"Failed to parse message: {e}")

    @classmethod
    def from_json(cls, json_str: str) -> AISMessage:
        """
        Parse message from JSON string.

        Args:
            json_str: JSON string containing message data

        Returns:
            AISMessage instance

        Raises:
            ValidationError: If JSON is invalid
        """
        try:
            data = json.loads(json_str)
            return cls.from_dict(data)
        except json.JSONDecodeError as e:
            raise ValidationError(f"Invalid JSON: {e}")

    # ========================================================================
    # Builder Methods for Each Message Type
    # ========================================================================

    @classmethod
    def create_handshake(
        cls,
        from_agent: str,
        to_agent: str,
        agent_name: str,
        agent_version: str,
        capabilities: List[Union[str, Dict[str, Any]]],
        auth: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None,
        supported_transports: Optional[List[str]] = None
    ) -> AISMessage:
        """
        Create a HANDSHAKE message.

        Sent by a client to establish a session and exchange capabilities.

        Args:
            from_agent: Sender agent ID
            to_agent: Recipient agent ID
            agent_name: Human-readable agent name
            agent_version: Agent version (semver recommended)
            capabilities: List of capabilities (strings or rich objects)
            auth: Optional authentication data
            session_id: Optional session ID (generated if not provided)
            supported_transports: Optional list of supported transports

        Returns:
            AISMessage with type HANDSHAKE
        """
        payload: Dict[str, Any] = {
            "ais_version": AIS_VERSION,
            "agent_name": agent_name,
            "agent_version": agent_version,
            "capabilities": capabilities,
            "supported_transports": supported_transports or ["http", "websocket"]
        }

        if auth:
            payload["auth"] = auth

        return cls(
            message_type=MessageType.HANDSHAKE,
            from_agent=from_agent,
            to_agent=to_agent,
            payload=payload,
            session_id=session_id or str(uuid4())
        )

    @classmethod
    def create_capability_declaration(
        cls,
        from_agent: str,
        to_agent: str,
        agent_name: str,
        agent_version: str,
        capabilities: List[Union[str, Dict[str, Any]]],
        session_id: str,
        session_expires: Optional[str] = None
    ) -> AISMessage:
        """
        Create a CAPABILITY_DECLARATION message.

        Sent by a server in response to a handshake to declare its capabilities.

        Args:
            from_agent: Sender agent ID
            to_agent: Recipient agent ID
            agent_name: Human-readable agent name
            agent_version: Agent version
            capabilities: List of capabilities with schemas
            session_id: Session ID from handshake
            session_expires: Optional session expiration time (ISO 8601)

        Returns:
            AISMessage with type CAPABILITY_DECLARATION
        """
        payload: Dict[str, Any] = {
            "agent_name": agent_name,
            "agent_version": agent_version,
            "capabilities": capabilities
        }

        if session_expires:
            payload["session_expires"] = session_expires

        return cls(
            message_type=MessageType.CAPABILITY_DECLARATION,
            from_agent=from_agent,
            to_agent=to_agent,
            payload=payload,
            session_id=session_id
        )

    @classmethod
    def create_request(
        cls,
        from_agent: str,
        to_agent: str,
        capability: str,
        parameters: Dict[str, Any],
        session_id: str,
        context: Optional[Dict[str, Any]] = None,
        request_id: Optional[str] = None
    ) -> AISMessage:
        """
        Create a REQUEST message.

        Sent to invoke a capability on a remote agent.

        Args:
            from_agent: Sender agent ID
            to_agent: Recipient agent ID
            capability: Name of capability to invoke
            parameters: Capability parameters
            session_id: Active session ID
            context: Optional context data (user_id, priority, etc.)
            request_id: Optional request ID (generated if not provided)

        Returns:
            AISMessage with type REQUEST
        """
        payload: Dict[str, Any] = {
            "request_id": request_id or str(uuid4()),
            "capability": capability,
            "parameters": parameters,
            "context": context or {}
        }

        return cls(
            message_type=MessageType.REQUEST,
            from_agent=from_agent,
            to_agent=to_agent,
            payload=payload,
            session_id=session_id
        )

    @classmethod
    def create_response(
        cls,
        from_agent: str,
        to_agent: str,
        request_id: str,
        result: Any,
        session_id: str,
        execution_time_ms: Optional[int] = None,
        status: str = "success"
    ) -> AISMessage:
        """
        Create a RESPONSE message.

        Sent to return the result of a capability invocation.

        Args:
            from_agent: Sender agent ID
            to_agent: Recipient agent ID
            request_id: ID of the request being responded to
            result: Result data (any JSON-serializable value)
            session_id: Active session ID
            execution_time_ms: Optional execution time in milliseconds
            status: Response status (default: "success")

        Returns:
            AISMessage with type RESPONSE
        """
        payload: Dict[str, Any] = {
            "request_id": request_id,
            "status": status,
            "result": result
        }

        if execution_time_ms is not None:
            payload["execution_time_ms"] = execution_time_ms

        return cls(
            message_type=MessageType.RESPONSE,
            from_agent=from_agent,
            to_agent=to_agent,
            payload=payload,
            session_id=session_id
        )

    @classmethod
    def create_error(
        cls,
        from_agent: str,
        to_agent: str,
        error_code: str,
        error_message: str,
        session_id: str,
        request_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        recoverable: bool = True
    ) -> AISMessage:
        """
        Create an ERROR message.

        Sent to signal a failure or exceptional condition.

        Args:
            from_agent: Sender agent ID
            to_agent: Recipient agent ID
            error_code: Standard error code (see constants.py)
            error_message: Human-readable error message
            session_id: Active session ID
            request_id: Optional ID of failed request
            details: Optional additional error details
            recoverable: Whether the error is recoverable (default: True)

        Returns:
            AISMessage with type ERROR
        """
        payload: Dict[str, Any] = {
            "error_code": error_code,
            "error_message": error_message,
            "recoverable": recoverable
        }

        if request_id:
            payload["request_id"] = request_id
        if details:
            payload["details"] = details

        return cls(
            message_type=MessageType.ERROR,
            from_agent=from_agent,
            to_agent=to_agent,
            payload=payload,
            session_id=session_id
        )

    @classmethod
    def create_stream_start(
        cls,
        from_agent: str,
        to_agent: str,
        request_id: str,
        session_id: str,
        stream_id: Optional[str] = None,
        estimated_chunks: Optional[int] = None,
        content_type: str = "text/plain"
    ) -> AISMessage:
        """
        Create a STREAM_START message.

        Signals the beginning of a streaming response.

        Args:
            from_agent: Sender agent ID
            to_agent: Recipient agent ID
            request_id: ID of the request being responded to
            session_id: Active session ID
            stream_id: Optional stream ID (generated if not provided)
            estimated_chunks: Optional estimate of total chunks
            content_type: MIME type of stream content

        Returns:
            AISMessage with type STREAM_START
        """
        payload: Dict[str, Any] = {
            "request_id": request_id,
            "stream_id": stream_id or str(uuid4()),
            "content_type": content_type
        }

        if estimated_chunks is not None:
            payload["estimated_chunks"] = estimated_chunks

        return cls(
            message_type=MessageType.STREAM_START,
            from_agent=from_agent,
            to_agent=to_agent,
            payload=payload,
            session_id=session_id
        )

    @classmethod
    def create_stream_chunk(
        cls,
        from_agent: str,
        to_agent: str,
        stream_id: str,
        sequence: int,
        data: Any,
        session_id: str,
        final: bool = False
    ) -> AISMessage:
        """
        Create a STREAM_CHUNK message.

        Delivers a chunk of streaming data.

        Args:
            from_agent: Sender agent ID
            to_agent: Recipient agent ID
            stream_id: ID of the stream
            sequence: Sequence number of this chunk (starting from 1)
            data: Chunk data (any JSON-serializable value)
            session_id: Active session ID
            final: Whether this is the final chunk (default: False)

        Returns:
            AISMessage with type STREAM_CHUNK
        """
        payload: Dict[str, Any] = {
            "stream_id": stream_id,
            "sequence": sequence,
            "data": data,
            "final": final
        }

        return cls(
            message_type=MessageType.STREAM_CHUNK,
            from_agent=from_agent,
            to_agent=to_agent,
            payload=payload,
            session_id=session_id
        )

    @classmethod
    def create_stream_end(
        cls,
        from_agent: str,
        to_agent: str,
        stream_id: str,
        session_id: str,
        total_chunks: int,
        status: str = "success",
        error_message: Optional[str] = None
    ) -> AISMessage:
        """
        Create a STREAM_END message.

        Signals the completion of a streaming response.

        Args:
            from_agent: Sender agent ID
            to_agent: Recipient agent ID
            stream_id: ID of the stream
            session_id: Active session ID
            total_chunks: Total number of chunks sent
            status: Stream status ("success" or "error")
            error_message: Optional error message if status is "error"

        Returns:
            AISMessage with type STREAM_END
        """
        payload: Dict[str, Any] = {
            "stream_id": stream_id,
            "total_chunks": total_chunks,
            "status": status
        }

        if error_message:
            payload["error_message"] = error_message

        return cls(
            message_type=MessageType.STREAM_END,
            from_agent=from_agent,
            to_agent=to_agent,
            payload=payload,
            session_id=session_id
        )

    @classmethod
    def create_session_end(
        cls,
        from_agent: str,
        to_agent: str,
        session_id: str,
        reason: str = "task_complete",
        message: Optional[str] = None
    ) -> AISMessage:
        """
        Create a SESSION_END message.

        Sent to gracefully terminate a session.

        Args:
            from_agent: Sender agent ID
            to_agent: Recipient agent ID
            session_id: Session ID to terminate
            reason: Reason for ending session (default: "task_complete")
            message: Optional human-readable message

        Returns:
            AISMessage with type SESSION_END
        """
        payload: Dict[str, Any] = {
            "reason": reason,
            "message": message or ""
        }

        return cls(
            message_type=MessageType.SESSION_END,
            from_agent=from_agent,
            to_agent=to_agent,
            payload=payload,
            session_id=session_id
        )

    def __repr__(self) -> str:
        """String representation for debugging."""
        # Handle both enum and string values (due to use_enum_values config)
        msg_type = self.message_type if isinstance(self.message_type, str) else self.message_type.value
        return (
            f"AISMessage(type={msg_type}, "
            f"from={self.from_agent}, to={self.to_agent}, "
            f"session={self.session_id[:8]}...)"
        )
