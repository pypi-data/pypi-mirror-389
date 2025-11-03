"""
AIS Protocol Validation

JSON schema validation and input sanitization for AIS messages.
"""

from typing import Dict, Any, List
from jsonschema import validate, ValidationError as JSONValidationError, Draft7Validator
import re

from .message import MessageType
from .exceptions import ValidationError
from .constants import MAX_STRING_LENGTH, MAX_ARRAY_LENGTH, MAX_OBJECT_DEPTH


# ============================================================================
# JSON Schemas for Each Message Type
# ============================================================================

HANDSHAKE_SCHEMA = {
    "type": "object",
    "required": ["ais_version", "agent_name", "agent_version", "capabilities"],
    "properties": {
        "ais_version": {
            "type": "string",
            "pattern": r"^0\.1$"
        },
        "agent_name": {
            "type": "string",
            "minLength": 1,
            "maxLength": 256
        },
        "agent_version": {
            "type": "string",
            "minLength": 1,
            "maxLength": 64
        },
        "capabilities": {
            "type": "array",
            "maxItems": 100,
            "items": {
                "oneOf": [
                    {
                        "type": "string",
                        "minLength": 1,
                        "maxLength": 256
                    },
                    {
                        "type": "object",
                        "required": ["name"],
                        "properties": {
                            "name": {
                                "type": "string",
                                "minLength": 1,
                                "maxLength": 256
                            },
                            "description": {
                                "type": "string",
                                "maxLength": 1024
                            },
                            "parameters": {
                                "type": "object"
                            }
                        },
                        "additionalProperties": False
                    }
                ]
            }
        },
        "supported_transports": {
            "type": "array",
            "items": {
                "type": "string",
                "enum": ["http", "websocket", "grpc"]
            }
        },
        "auth": {
            "type": "object"
        }
    },
    "additionalProperties": False
}

CAPABILITY_DECLARATION_SCHEMA = {
    "type": "object",
    "required": ["agent_name", "agent_version", "capabilities"],
    "properties": {
        "agent_name": {
            "type": "string",
            "minLength": 1,
            "maxLength": 256
        },
        "agent_version": {
            "type": "string",
            "minLength": 1,
            "maxLength": 64
        },
        "capabilities": {
            "type": "array",
            "maxItems": 100,
            "items": {
                "oneOf": [
                    {"type": "string"},
                    {
                        "type": "object",
                        "required": ["name"],
                        "properties": {
                            "name": {"type": "string"},
                            "description": {"type": "string"},
                            "parameters": {"type": "object"}
                        }
                    }
                ]
            }
        },
        "session_expires": {
            "type": "string",
            "format": "date-time"
        }
    },
    "additionalProperties": False
}

REQUEST_SCHEMA = {
    "type": "object",
    "required": ["request_id", "capability", "parameters"],
    "properties": {
        "request_id": {
            "type": "string",
            "pattern": r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
        },
        "capability": {
            "type": "string",
            "minLength": 1,
            "maxLength": 256
        },
        "parameters": {
            "type": "object"
        },
        "context": {
            "type": "object"
        }
    },
    "additionalProperties": False
}

RESPONSE_SCHEMA = {
    "type": "object",
    "required": ["request_id", "status", "result"],
    "properties": {
        "request_id": {
            "type": "string",
            "pattern": r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
        },
        "status": {
            "type": "string",
            "enum": ["success", "partial", "error"]
        },
        "result": {},  # Any type
        "execution_time_ms": {
            "type": "integer",
            "minimum": 0
        }
    },
    "additionalProperties": False
}

ERROR_SCHEMA = {
    "type": "object",
    "required": ["error_code", "error_message", "recoverable"],
    "properties": {
        "request_id": {
            "type": "string",
            "pattern": r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
        },
        "error_code": {
            "type": "string",
            "minLength": 1,
            "maxLength": 128
        },
        "error_message": {
            "type": "string",
            "minLength": 1,
            "maxLength": 4096
        },
        "details": {
            "type": "object"
        },
        "recoverable": {
            "type": "boolean"
        }
    },
    "additionalProperties": False
}

STREAM_START_SCHEMA = {
    "type": "object",
    "required": ["request_id", "stream_id", "content_type"],
    "properties": {
        "request_id": {
            "type": "string",
            "pattern": r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
        },
        "stream_id": {
            "type": "string",
            "pattern": r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
        },
        "estimated_chunks": {
            "type": "integer",
            "minimum": 0
        },
        "content_type": {
            "type": "string",
            "minLength": 1,
            "maxLength": 256
        }
    },
    "additionalProperties": False
}

STREAM_CHUNK_SCHEMA = {
    "type": "object",
    "required": ["stream_id", "sequence", "data", "final"],
    "properties": {
        "stream_id": {
            "type": "string",
            "pattern": r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
        },
        "sequence": {
            "type": "integer",
            "minimum": 1
        },
        "data": {},  # Any type
        "final": {
            "type": "boolean"
        }
    },
    "additionalProperties": False
}

STREAM_END_SCHEMA = {
    "type": "object",
    "required": ["stream_id", "total_chunks", "status"],
    "properties": {
        "stream_id": {
            "type": "string",
            "pattern": r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
        },
        "total_chunks": {
            "type": "integer",
            "minimum": 0
        },
        "status": {
            "type": "string",
            "enum": ["success", "error"]
        },
        "error_message": {
            "type": "string",
            "maxLength": 4096
        }
    },
    "additionalProperties": False
}

SESSION_END_SCHEMA = {
    "type": "object",
    "required": ["reason"],
    "properties": {
        "reason": {
            "type": "string",
            "minLength": 1,
            "maxLength": 256
        },
        "message": {
            "type": "string",
            "maxLength": 4096
        }
    },
    "additionalProperties": False
}


# ============================================================================
# Message Validator
# ============================================================================

class MessageValidator:
    """
    Validates AIS messages against JSON schemas.

    Ensures all messages conform to the AIS protocol specification.
    """

    # Map message types to their schemas
    SCHEMAS: Dict[MessageType, Dict[str, Any]] = {
        MessageType.HANDSHAKE: HANDSHAKE_SCHEMA,
        MessageType.CAPABILITY_DECLARATION: CAPABILITY_DECLARATION_SCHEMA,
        MessageType.REQUEST: REQUEST_SCHEMA,
        MessageType.RESPONSE: RESPONSE_SCHEMA,
        MessageType.ERROR: ERROR_SCHEMA,
        MessageType.STREAM_START: STREAM_START_SCHEMA,
        MessageType.STREAM_CHUNK: STREAM_CHUNK_SCHEMA,
        MessageType.STREAM_END: STREAM_END_SCHEMA,
        MessageType.SESSION_END: SESSION_END_SCHEMA,
    }

    @classmethod
    def validate(cls, message: Any) -> None:
        """
        Validate message payload against its schema.

        Args:
            message: AISMessage instance to validate

        Raises:
            ValidationError: If message payload doesn't match schema
        """
        from .message import AISMessage  # Avoid circular import

        if not isinstance(message, AISMessage):
            raise ValidationError("Message must be an AISMessage instance")

        # Get schema for this message type
        message_type = message.message_type
        if isinstance(message_type, str):
            # Convert string to enum if needed
            message_type = MessageType(message_type)

        schema = cls.SCHEMAS.get(message_type)
        if not schema:
            raise ValidationError(f"No schema defined for message type: {message_type}")

        # Validate payload against schema
        try:
            validate(instance=message.payload, schema=schema)
        except JSONValidationError as e:
            # Extract field path for better error messages
            field_path = ".".join(str(p) for p in e.path) if e.path else "payload"
            raise ValidationError(
                f"Validation failed for {message_type.value}.{field_path}: {e.message}",
                field=field_path
            )

    @classmethod
    def validate_agent_id(cls, agent_id: str) -> None:
        """
        Validate agent ID format.

        Agent IDs must follow the format: agent://domain/path/name

        Args:
            agent_id: Agent ID to validate

        Raises:
            ValidationError: If agent ID format is invalid
        """
        if not isinstance(agent_id, str):
            raise ValidationError("Agent ID must be a string")

        if not agent_id.startswith("agent://"):
            raise ValidationError(
                f"Agent ID must start with 'agent://': {agent_id}",
                field="agent_id"
            )

        # Extract path after agent://
        path = agent_id[8:]  # Skip "agent://"

        if not path:
            raise ValidationError(
                "Agent ID must have domain and name after 'agent://'",
                field="agent_id"
            )

        parts = path.split("/")
        if len(parts) < 2:
            raise ValidationError(
                f"Agent ID must have at least domain and name: {agent_id}",
                field="agent_id",
                details={"format": "agent://domain/path/name"}
            )

        # Validate domain (first part)
        domain = parts[0]
        if not re.match(r'^[a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?(\.[a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?)*$', domain):
            raise ValidationError(
                f"Invalid domain in agent ID: {domain}",
                field="agent_id",
                details={"domain": domain}
            )

        # Validate name parts (rest of parts)
        for i, part in enumerate(parts[1:], start=1):
            if not part:
                raise ValidationError(
                    f"Empty segment in agent ID path at position {i}",
                    field="agent_id"
                )
            if not re.match(r'^[a-z0-9_-]+$', part):
                raise ValidationError(
                    f"Invalid characters in agent ID segment: {part}",
                    field="agent_id",
                    details={"segment": part, "position": i}
                )


# ============================================================================
# Input Sanitizer
# ============================================================================

class InputSanitizer:
    """
    Sanitize inputs to prevent injection attacks and excessive resource usage.

    Recursively processes dictionaries, lists, and strings to ensure they meet
    size and safety constraints.
    """

    MAX_STRING_LENGTH = MAX_STRING_LENGTH
    MAX_ARRAY_LENGTH = MAX_ARRAY_LENGTH
    MAX_OBJECT_DEPTH = MAX_OBJECT_DEPTH

    @classmethod
    def sanitize_string(cls, s: str) -> str:
        """
        Sanitize string input.

        Args:
            s: String to sanitize

        Returns:
            Sanitized string

        Raises:
            ValidationError: If string exceeds maximum length
        """
        if not isinstance(s, str):
            return s

        if len(s) > cls.MAX_STRING_LENGTH:
            raise ValidationError(
                f"String exceeds maximum length of {cls.MAX_STRING_LENGTH}: {len(s)}",
                field="string_length",
                details={"length": len(s), "max_length": cls.MAX_STRING_LENGTH}
            )

        # Remove null bytes (can cause issues in some contexts)
        s = s.replace('\x00', '')

        # Remove other control characters except newlines and tabs
        s = ''.join(char for char in s if char >= ' ' or char in '\n\r\t')

        return s

    @classmethod
    def sanitize_dict(cls, d: Dict[str, Any], depth: int = 0) -> Dict[str, Any]:
        """
        Recursively sanitize dictionary.

        Args:
            d: Dictionary to sanitize
            depth: Current nesting depth

        Returns:
            Sanitized dictionary

        Raises:
            ValidationError: If nesting exceeds maximum depth
        """
        if not isinstance(d, dict):
            return d

        if depth > cls.MAX_OBJECT_DEPTH:
            raise ValidationError(
                f"Object nesting exceeds maximum depth of {cls.MAX_OBJECT_DEPTH}",
                field="object_depth",
                details={"depth": depth, "max_depth": cls.MAX_OBJECT_DEPTH}
            )

        result: Dict[str, Any] = {}
        for key, value in d.items():
            # Sanitize key
            sanitized_key = cls.sanitize_string(key) if isinstance(key, str) else key

            # Sanitize value based on type
            if isinstance(value, str):
                result[sanitized_key] = cls.sanitize_string(value)
            elif isinstance(value, dict):
                result[sanitized_key] = cls.sanitize_dict(value, depth + 1)
            elif isinstance(value, list):
                result[sanitized_key] = cls.sanitize_list(value, depth + 1)
            else:
                # Other types (int, float, bool, None) pass through
                result[sanitized_key] = value

        return result

    @classmethod
    def sanitize_list(cls, lst: List[Any], depth: int = 0) -> List[Any]:
        """
        Sanitize list input.

        Args:
            lst: List to sanitize
            depth: Current nesting depth

        Returns:
            Sanitized list

        Raises:
            ValidationError: If list exceeds maximum length
        """
        if not isinstance(lst, list):
            return lst

        if len(lst) > cls.MAX_ARRAY_LENGTH:
            raise ValidationError(
                f"Array exceeds maximum length of {cls.MAX_ARRAY_LENGTH}: {len(lst)}",
                field="array_length",
                details={"length": len(lst), "max_length": cls.MAX_ARRAY_LENGTH}
            )

        result: List[Any] = []
        for item in lst:
            if isinstance(item, str):
                result.append(cls.sanitize_string(item))
            elif isinstance(item, dict):
                result.append(cls.sanitize_dict(item, depth))
            elif isinstance(item, list):
                result.append(cls.sanitize_list(item, depth))
            else:
                result.append(item)

        return result

    @classmethod
    def sanitize(cls, value: Any, depth: int = 0) -> Any:
        """
        Sanitize any value (convenience method).

        Args:
            value: Value to sanitize
            depth: Current nesting depth

        Returns:
            Sanitized value
        """
        if isinstance(value, str):
            return cls.sanitize_string(value)
        elif isinstance(value, dict):
            return cls.sanitize_dict(value, depth)
        elif isinstance(value, list):
            return cls.sanitize_list(value, depth)
        else:
            return value
