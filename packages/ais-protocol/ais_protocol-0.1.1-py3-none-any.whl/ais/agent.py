"""
AIS Protocol Agent Core

Core agent implementation with capability registration, session management,
and message routing.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Callable, Union
from datetime import datetime, timedelta
from uuid import uuid4

from .message import AISMessage, MessageType
from .transport import CombinedTransport
from .validation import MessageValidator, InputSanitizer
from .exceptions import SessionError, CapabilityError, ValidationError
from .constants import DEFAULT_SESSION_TIMEOUT_MINUTES, SESSION_CLEANUP_INTERVAL_SECONDS

# Configure logging
logger = logging.getLogger(__name__)


# ============================================================================
# Capability Descriptor
# ============================================================================

class Capability:
    """
    Capability descriptor for agent capabilities.

    A capability represents a function/service that an agent can perform.
    It can be invoked by other agents via the AIS protocol.
    """

    def __init__(
        self,
        name: str,
        handler: Callable,
        description: str = "",
        parameters: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize capability.

        Args:
            name: Capability name (e.g., "search", "summarize")
            handler: Async function to handle requests
            description: Human-readable description
            parameters: JSON schema for parameters (optional)
        """
        self.name = name
        self.handler = handler
        self.description = description
        self.parameters = parameters or {}

        logger.debug(f"Created capability: {name}")

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary for protocol messages.

        Returns:
            Dict with capability metadata
        """
        result = {"name": self.name}
        if self.description:
            result["description"] = self.description
        if self.parameters:
            result["parameters"] = self.parameters
        return result

    def __repr__(self) -> str:
        return f"Capability(name={self.name}, description={self.description[:50] if self.description else ''})"


# ============================================================================
# Session Management
# ============================================================================

class Session:
    """
    Agent session representing a connection with another agent.

    Sessions maintain state between multiple request/response exchanges.
    They automatically expire after a timeout period.
    """

    def __init__(
        self,
        session_id: str,
        peer_agent: str,
        created_at: Optional[datetime] = None,
        timeout_minutes: int = DEFAULT_SESSION_TIMEOUT_MINUTES
    ):
        """
        Initialize session.

        Args:
            session_id: Unique session ID (UUID)
            peer_agent: Agent ID of the peer
            created_at: Creation timestamp (defaults to now)
            timeout_minutes: Session timeout in minutes
        """
        self.session_id = session_id
        self.peer_agent = peer_agent
        self.created_at = created_at or datetime.utcnow()
        self.last_activity = self.created_at
        self.expires_at = self.created_at + timedelta(minutes=timeout_minutes)
        self.peer_capabilities: List[Union[str, Dict[str, Any]]] = []
        self.context: Dict[str, Any] = {}

        logger.debug(f"Created session {session_id} with {peer_agent}, expires {self.expires_at}")

    def is_expired(self) -> bool:
        """
        Check if session has expired.

        Returns:
            True if expired, False otherwise
        """
        return datetime.utcnow() > self.expires_at

    def touch(self) -> None:
        """Update last activity timestamp to keep session alive."""
        self.last_activity = datetime.utcnow()
        logger.debug(f"Session {self.session_id} touched at {self.last_activity}")

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary.

        Returns:
            Dict with session metadata
        """
        return {
            "session_id": self.session_id,
            "peer_agent": self.peer_agent,
            "created_at": self.created_at.isoformat(),
            "last_activity": self.last_activity.isoformat(),
            "expires_at": self.expires_at.isoformat(),
            "peer_capabilities": self.peer_capabilities,
            "context_keys": list(self.context.keys())
        }

    def __repr__(self) -> str:
        expired = "EXPIRED" if self.is_expired() else "ACTIVE"
        return f"Session(id={self.session_id[:8]}..., peer={self.peer_agent}, status={expired})"


# ============================================================================
# AIS Agent Core
# ============================================================================

class AISAgent:
    """
    Core AIS Agent implementation.

    An agent is a service that exposes capabilities to other agents via the AIS protocol.
    It handles:
    - Capability registration and discovery
    - Session management
    - Message routing
    - Request handling
    - Automatic session cleanup

    Example:
        agent = AISAgent(
            agent_id="agent://example.com/my-agent",
            agent_name="MyAgent",
            agent_version="1.0.0"
        )

        @agent.capability("search", description="Search for information")
        async def search(parameters, context, session):
            query = parameters.get("query")
            return {"results": [f"Result for {query}"]}

        agent.start_sync(host="0.0.0.0", port=8000)
    """

    def __init__(
        self,
        agent_id: str,
        agent_name: Optional[str] = None,
        agent_version: str = "1.0.0",
        session_timeout_minutes: int = DEFAULT_SESSION_TIMEOUT_MINUTES,
        use_combined_transport: bool = True
    ):
        """
        Initialize AIS agent.

        Args:
            agent_id: Unique agent ID (format: agent://domain/path/name)
            agent_name: Human-readable name (defaults to last part of agent_id)
            agent_version: Agent version string
            session_timeout_minutes: Session timeout in minutes
            use_combined_transport: Use combined HTTP+WebSocket (default True)

        Raises:
            ValidationError: If agent_id is invalid
        """
        # Validate agent ID
        MessageValidator.validate_agent_id(agent_id)

        self.agent_id = agent_id
        self.agent_name = agent_name or agent_id.split("/")[-1]
        self.agent_version = agent_version
        self.session_timeout_minutes = session_timeout_minutes

        # Capability registry (private - use get_capabilities() for read-only access)
        self._capabilities: Dict[str, Capability] = {}

        # Active sessions (private - use get_active_sessions() for read-only access)
        self._sessions: Dict[str, Session] = {}

        # Transport layer
        if use_combined_transport:
            self.transport = CombinedTransport()
        else:
            from .transport import HTTPTransport
            self.transport = HTTPTransport()

        # Set up message handler
        self.transport.set_message_handler(self._handle_message)

        # Background tasks
        self._cleanup_task: Optional[asyncio.Task] = None
        self._running = False

        logger.info(f"Initialized agent: {self.agent_id} (name={self.agent_name}, version={self.agent_version})")

    # ========================================================================
    # Capability Registration
    # ========================================================================

    def register_capability(
        self,
        name: str,
        handler: Callable,
        description: str = "",
        parameters: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Register a capability handler.

        Args:
            name: Capability name
            handler: Async function to handle requests
            description: Human-readable description
            parameters: JSON schema for parameters

        Example:
            async def my_capability(parameters, context, session):
                return {"result": "success"}

            agent.register_capability("my_capability", my_capability)
        """
        cap = Capability(
            name=name,
            handler=handler,
            description=description,
            parameters=parameters
        )
        self._capabilities[name] = cap
        logger.info(f"Registered capability: {name}")

    def capability(
        self,
        name: str,
        description: str = "",
        parameters: Optional[Dict[str, Any]] = None
    ) -> Callable:
        """
        Decorator for registering capabilities.

        Args:
            name: Capability name
            description: Human-readable description
            parameters: JSON schema for parameters

        Returns:
            Decorator function

        Example:
            @agent.capability("search", description="Search for information")
            async def search(parameters, context, session):
                query = parameters.get("query")
                return {"results": [f"Result for {query}"]}
        """
        def decorator(func: Callable) -> Callable:
            self.register_capability(name, func, description, parameters)
            return func
        return decorator

    # ========================================================================
    # Message Routing
    # ========================================================================

    async def _handle_message(self, message: AISMessage) -> AISMessage:
        """
        Main message router.

        Routes incoming messages to appropriate handlers based on message type.

        Args:
            message: Incoming AIS message

        Returns:
            Response AIS message
        """
        try:
            # Validate message
            MessageValidator.validate(message)

            # Sanitize inputs
            message.payload = InputSanitizer.sanitize_dict(message.payload)

            # Log incoming message
            msg_type = message.message_type if isinstance(message.message_type, str) else message.message_type.value
            logger.debug(f"Handling {msg_type} from {message.from_agent}")

            # Route by message type
            if message.message_type == MessageType.HANDSHAKE or message.message_type == "handshake":
                return await self._handle_handshake(message)

            elif message.message_type == MessageType.REQUEST or message.message_type == "request":
                return await self._handle_request(message)

            elif message.message_type == MessageType.SESSION_END or message.message_type == "session_end":
                return await self._handle_session_end(message)

            else:
                # Unsupported message type
                return AISMessage.create_error(
                    from_agent=self.agent_id,
                    to_agent=message.from_agent,
                    error_code="unsupported_message_type",
                    error_message=f"Message type {message.message_type} not supported by this agent",
                    session_id=message.session_id,
                    recoverable=False
                )

        except ValidationError as e:
            logger.warning(f"Validation error: {e}")
            return AISMessage.create_error(
                from_agent=self.agent_id,
                to_agent=message.from_agent,
                error_code="validation_error",
                error_message=str(e),
                session_id=message.session_id,
                recoverable=True
            )

        except Exception as e:
            logger.exception(f"Error handling message: {e}")
            return AISMessage.create_error(
                from_agent=self.agent_id,
                to_agent=message.from_agent,
                error_code="internal_error",
                error_message=f"Internal error: {str(e)}",
                session_id=message.session_id,
                recoverable=False
            )

    # ========================================================================
    # Handshake Handling
    # ========================================================================

    async def _handle_handshake(self, message: AISMessage) -> AISMessage:
        """
        Handle handshake message and create session.

        Args:
            message: Handshake message

        Returns:
            Capability declaration message
        """
        payload = message.payload

        # Check version compatibility
        client_version = payload.get("ais_version", "0.1")
        if client_version != "0.1":
            logger.warning(f"Unsupported AIS version: {client_version}")
            return AISMessage.create_error(
                from_agent=self.agent_id,
                to_agent=message.from_agent,
                error_code="unsupported_version",
                error_message=f"AIS version {client_version} not supported. Supported: 0.1",
                session_id=message.session_id,
                details={"supported_versions": ["0.1"], "client_version": client_version},
                recoverable=False
            )

        # Create new session
        session = Session(
            session_id=message.session_id,
            peer_agent=message.from_agent,
            created_at=datetime.utcnow(),
            timeout_minutes=self.session_timeout_minutes
        )

        # Store peer capabilities
        session.peer_capabilities = payload.get("capabilities", [])

        # Register session
        self._sessions[session.session_id] = session

        logger.info(f"Handshake successful: session {session.session_id} with {message.from_agent}")
        logger.debug(f"Peer capabilities: {session.peer_capabilities}")

        # Return capability declaration
        return AISMessage.create_capability_declaration(
            from_agent=self.agent_id,
            to_agent=message.from_agent,
            agent_name=self.agent_name,
            agent_version=self.agent_version,
            capabilities=[cap.to_dict() for cap in self._capabilities.values()],
            session_id=session.session_id
        )

    # ========================================================================
    # Request Handling
    # ========================================================================

    async def _handle_request(self, message: AISMessage) -> AISMessage:
        """
        Handle capability request.

        Args:
            message: Request message

        Returns:
            Response or error message
        """
        payload = message.payload
        request_id = payload.get("request_id")
        capability_name = payload.get("capability")
        parameters = payload.get("parameters", {})
        context = payload.get("context", {})

        # Check session exists
        session = self._sessions.get(message.session_id)
        if not session:
            logger.warning(f"Request for unknown session: {message.session_id}")
            return AISMessage.create_error(
                from_agent=self.agent_id,
                to_agent=message.from_agent,
                error_code="session_expired",
                error_message="Session not found or expired. Please handshake first.",
                session_id=message.session_id,
                request_id=request_id,
                recoverable=True
            )

        # Check session not expired
        if session.is_expired():
            logger.warning(f"Request for expired session: {message.session_id}")
            del self._sessions[message.session_id]
            return AISMessage.create_error(
                from_agent=self.agent_id,
                to_agent=message.from_agent,
                error_code="session_expired",
                error_message="Session has expired",
                session_id=message.session_id,
                request_id=request_id,
                recoverable=True
            )

        # Touch session to keep alive
        session.touch()

        # Check capability exists
        capability = self._capabilities.get(capability_name)
        if not capability:
            logger.warning(f"Unknown capability requested: {capability_name}")
            return AISMessage.create_error(
                from_agent=self.agent_id,
                to_agent=message.from_agent,
                error_code="unknown_capability",
                error_message=f"Capability '{capability_name}' not found",
                session_id=message.session_id,
                request_id=request_id,
                details={"available_capabilities": list(self._capabilities.keys())},
                recoverable=True
            )

        # Execute capability
        try:
            logger.info(f"Executing capability '{capability_name}' for request {request_id}")
            start_time = datetime.utcnow()

            # Call handler (async or sync)
            if asyncio.iscoroutinefunction(capability.handler):
                result = await capability.handler(
                    parameters=parameters,
                    context=context,
                    session=session
                )
            else:
                result = capability.handler(
                    parameters=parameters,
                    context=context,
                    session=session
                )

            # Calculate execution time
            execution_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)

            logger.info(f"Capability '{capability_name}' completed in {execution_time}ms")

            # Return success response
            return AISMessage.create_response(
                from_agent=self.agent_id,
                to_agent=message.from_agent,
                request_id=request_id,
                result=result,
                session_id=message.session_id,
                execution_time_ms=execution_time
            )

        except Exception as e:
            logger.exception(f"Error executing capability '{capability_name}': {e}")
            return AISMessage.create_error(
                from_agent=self.agent_id,
                to_agent=message.from_agent,
                error_code="capability_error",
                error_message=f"Capability execution failed: {str(e)}",
                session_id=message.session_id,
                request_id=request_id,
                details={"capability": capability_name, "error_type": type(e).__name__},
                recoverable=False
            )

    # ========================================================================
    # Session End Handling
    # ========================================================================

    async def _handle_session_end(self, message: AISMessage) -> AISMessage:
        """
        Handle session termination.

        Args:
            message: Session end message

        Returns:
            Acknowledgment message
        """
        session_id = message.session_id

        if session_id in self._sessions:
            session = self._sessions[session_id]
            del self._sessions[session_id]
            logger.info(f"Session ended: {session_id} with {session.peer_agent}")
        else:
            logger.warning(f"Session end for unknown session: {session_id}")

        # Return acknowledgment
        return AISMessage.create_response(
            from_agent=self.agent_id,
            to_agent=message.from_agent,
            request_id="session_end_ack",
            result={"status": "session_ended", "session_id": session_id},
            session_id=session_id
        )

    # ========================================================================
    # Session Cleanup
    # ========================================================================

    async def _cleanup_sessions(self) -> None:
        """
        Background task to clean up expired sessions.

        Runs periodically while agent is running.
        """
        logger.info("Session cleanup task started")

        while self._running:
            try:
                await asyncio.sleep(SESSION_CLEANUP_INTERVAL_SECONDS)

                # Find expired sessions
                expired = [
                    sid for sid, session in self._sessions.items()
                    if session.is_expired()
                ]

                # Remove expired sessions
                for sid in expired:
                    session = self._sessions[sid]
                    del self._sessions[sid]
                    logger.info(f"Cleaned up expired session: {sid} (peer: {session.peer_agent})")

                if expired:
                    logger.info(f"Cleaned up {len(expired)} expired session(s)")

            except asyncio.CancelledError:
                logger.info("Session cleanup task cancelled")
                break

            except Exception as e:
                logger.exception(f"Error in session cleanup: {e}")

        logger.info("Session cleanup task stopped")

    # ========================================================================
    # Agent Lifecycle
    # ========================================================================

    async def start(
        self,
        host: str = "0.0.0.0",
        port: int = 8000
    ) -> None:
        """
        Start the agent (async).

        Args:
            host: Host to bind to (default: 0.0.0.0)
            port: Port to bind to (default: 8000)
        """
        logger.info(f"Starting agent '{self.agent_name}' ({self.agent_id})")
        logger.info(f"Registered capabilities: {list(self._capabilities.keys())}")

        self._running = True

        # Start cleanup task
        self._cleanup_task = asyncio.create_task(self._cleanup_sessions())

        # Start transport
        if hasattr(self.transport, 'start'):
            # Combined transport
            await self.transport.start(host=host, port=port)
        else:
            # HTTP transport
            await self.transport.start_server(host=host, port=port)

    def start_sync(
        self,
        host: str = "0.0.0.0",
        port: int = 8000
    ) -> None:
        """
        Start the agent (sync version).

        This is a convenience method that runs the async start() in an event loop.

        Args:
            host: Host to bind to
            port: Port to bind to
        """
        asyncio.run(self.start(host=host, port=port))

    async def stop(self) -> None:
        """Stop the agent gracefully."""
        logger.info(f"Stopping agent '{self.agent_name}'")

        self._running = False

        # Cancel cleanup task
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass

        # Stop transport
        if hasattr(self.transport, 'stop'):
            await self.transport.stop()
        else:
            await self.transport.stop_server()

        logger.info(f"Agent '{self.agent_name}' stopped")

    # ========================================================================
    # Introspection
    # ========================================================================

    def get_session_count(self) -> int:
        """Get number of active sessions."""
        return len(self._sessions)

    def get_capability_count(self) -> int:
        """Get number of registered capabilities."""
        return len(self._capabilities)

    def get_sessions(self) -> List[Dict[str, Any]]:
        """
        Get list of active sessions.

        Returns:
            List of session dictionaries
        """
        return [session.to_dict() for session in self._sessions.values()]

    def get_capabilities(self) -> List[Dict[str, Any]]:
        """
        Get list of registered capabilities.

        Returns:
            List of capability dictionaries
        """
        return [cap.to_dict() for cap in self._capabilities.values()]

    def __repr__(self) -> str:
        return (f"AISAgent(id={self.agent_id}, name={self.agent_name}, "
                f"capabilities={len(self._capabilities)}, sessions={len(self._sessions)})")
