"""
AIS Protocol - Client Library

High-level client for interacting with AIS agents.
Includes automatic retry logic, session management, and connection pooling.
"""

import asyncio
import logging
from typing import Optional, Dict, Any, List, Callable
from dataclasses import dataclass
from enum import Enum
import time

from .message import AISMessage, MessageType
from .transport import HTTPTransport, CombinedTransport
from .validation import MessageValidator
from .exceptions import (
    AISException,
    TransportError,
    TimeoutError,
    SessionError,
    AuthenticationError,
    RateLimitError,
)


logger = logging.getLogger(__name__)


# ============================================================================
# Retry Configuration
# ============================================================================

class RetryStrategy(Enum):
    """Retry strategy options."""
    EXPONENTIAL_BACKOFF = "exponential_backoff"
    LINEAR_BACKOFF = "linear_backoff"
    CONSTANT_DELAY = "constant_delay"
    FIBONACCI_BACKOFF = "fibonacci_backoff"


@dataclass
class RetryConfig:
    """
    Configuration for automatic retry logic.

    Attributes:
        max_retries: Maximum number of retry attempts (default: 3)
        strategy: Retry strategy to use (default: exponential backoff)
        initial_delay: Initial delay in seconds (default: 1.0)
        max_delay: Maximum delay between retries in seconds (default: 60.0)
        multiplier: Multiplier for exponential/fibonacci backoff (default: 2.0)
        jitter: Add random jitter to delays (default: True)
        retry_on_timeout: Retry on timeout errors (default: True)
        retry_on_transport_error: Retry on transport errors (default: True)
        retry_on_rate_limit: Retry on rate limit errors (default: True)
    """
    max_retries: int = 3
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL_BACKOFF
    initial_delay: float = 1.0
    max_delay: float = 60.0
    multiplier: float = 2.0
    jitter: bool = True
    retry_on_timeout: bool = True
    retry_on_transport_error: bool = True
    retry_on_rate_limit: bool = True

    def should_retry(self, exception: Exception) -> bool:
        """Determine if an exception should trigger a retry."""
        if isinstance(exception, TimeoutError):
            return self.retry_on_timeout
        elif isinstance(exception, TransportError):
            return self.retry_on_transport_error
        elif isinstance(exception, RateLimitError):
            return self.retry_on_rate_limit
        elif isinstance(exception, (AuthenticationError, SessionError)):
            # Never retry auth or session errors
            return False
        return False

    def get_delay(self, attempt: int) -> float:
        """Calculate delay for given attempt number."""
        import random

        if self.strategy == RetryStrategy.CONSTANT_DELAY:
            delay = self.initial_delay
        elif self.strategy == RetryStrategy.LINEAR_BACKOFF:
            delay = self.initial_delay * attempt
        elif self.strategy == RetryStrategy.EXPONENTIAL_BACKOFF:
            delay = self.initial_delay * (self.multiplier ** (attempt - 1))
        elif self.strategy == RetryStrategy.FIBONACCI_BACKOFF:
            # Fibonacci sequence
            if attempt <= 2:
                delay = self.initial_delay
            else:
                fib_prev, fib_curr = 1, 1
                for _ in range(attempt - 2):
                    fib_prev, fib_curr = fib_curr, fib_prev + fib_curr
                delay = self.initial_delay * fib_curr
        else:
            delay = self.initial_delay

        # Apply max delay cap
        delay = min(delay, self.max_delay)

        # Add jitter
        if self.jitter:
            delay = delay * (0.5 + random.random())

        return delay


# ============================================================================
# AIS Client
# ============================================================================

class AISClient:
    """
    High-level client for interacting with AIS agents.

    Features:
    - Automatic session management
    - Connection pooling
    - Automatic retries with configurable strategies
    - Authentication support (JWT and API Key)
    - Type-safe capability invocation
    - Streaming support

    Example:
        ```python
        client = AISClient(
            agent_id="agent://example.com/client",
            agent_name="MyClient",
            auth_token="Bearer xxx"
        )

        await client.connect("http://localhost:8000")

        result = await client.call(
            capability="search",
            parameters={"query": "AI agents"}
        )

        await client.disconnect()
        ```
    """

    def __init__(
        self,
        agent_id: str,
        agent_name: Optional[str] = None,
        agent_version: str = "1.0.0",
        capabilities: Optional[List[str]] = None,
        auth_token: Optional[str] = None,
        timeout: float = 30.0,
        retry_config: Optional[RetryConfig] = None,
        use_websocket: bool = False,
    ):
        """
        Initialize AIS client.

        Args:
            agent_id: Client agent identifier
            agent_name: Human-readable client name
            agent_version: Client version
            capabilities: List of capabilities this client provides
            auth_token: Authentication token (JWT or API Key)
            timeout: Default timeout for requests in seconds
            retry_config: Retry configuration
            use_websocket: Use WebSocket transport instead of HTTP
        """
        MessageValidator.validate_agent_id(agent_id)

        self.agent_id = agent_id
        self.agent_name = agent_name or agent_id.split("/")[-1]
        self.agent_version = agent_version
        self.capabilities = capabilities or []
        self.auth_token = auth_token
        self.timeout = timeout
        self.retry_config = retry_config or RetryConfig()
        self.use_websocket = use_websocket

        # State
        self._connected = False
        self._server_url: Optional[str] = None
        self._session_id: Optional[str] = None
        self._server_agent_id: Optional[str] = None
        self._server_capabilities: List[str] = []

        # Transport
        self._transport: Optional[HTTPTransport] = None

        # Streaming
        self._stream_handlers: Dict[str, Callable] = {}

    @property
    def connected(self) -> bool:
        """Check if client is connected to a server."""
        return self._connected

    @property
    def session_id(self) -> Optional[str]:
        """Get current session ID."""
        return self._session_id

    @property
    def server_capabilities(self) -> List[str]:
        """Get list of server capabilities."""
        return self._server_capabilities.copy()

    async def connect(
        self,
        server_url: str,
        timeout: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Connect to an AIS agent server.

        Performs handshake and establishes session.

        Args:
            server_url: Server URL (e.g., "http://localhost:8000")
            timeout: Connection timeout in seconds

        Returns:
            Server information from handshake response

        Raises:
            TransportError: If connection fails
            TimeoutError: If connection times out
            AuthenticationError: If authentication fails
        """
        if self._connected:
            raise SessionError("Client already connected. Call disconnect() first.")

        logger.info(f"Connecting to {server_url}")

        # Create transport
        self._transport = HTTPTransport()
        self._server_url = server_url

        # Create handshake message
        auth_data = None
        if self.auth_token:
            if self.auth_token.startswith("Bearer "):
                auth_data = {"type": "jwt", "token": self.auth_token[7:]}
            elif self.auth_token.startswith("ais_"):
                auth_data = {"type": "api_key", "key": self.auth_token}

        handshake = AISMessage.create_handshake(
            from_agent=self.agent_id,
            to_agent=f"agent://{server_url.split('//')[1].split(':')[0]}/server",  # Extract domain
            agent_name=self.agent_name,
            agent_version=self.agent_version,
            capabilities=self.capabilities,
            auth=auth_data,
            session_id=None  # Will be auto-generated
        )

        # Send handshake with timeout
        try:
            response = await asyncio.wait_for(
                self._send_with_auth(handshake),
                timeout=timeout or self.timeout
            )
        except asyncio.TimeoutError:
            raise TimeoutError(
                f"Connection to {server_url} timed out",
                timeout_seconds=timeout or self.timeout,
                operation="connect"
            )

        # Validate response
        if response.message_type == MessageType.ERROR or response.message_type == "error":
            error_msg = response.payload.get("error_message", "Handshake failed")
            raise SessionError(f"Handshake failed: {error_msg}")

        if response.message_type != MessageType.CAPABILITY_DECLARATION and response.message_type != "capability_declaration":
            raise SessionError(f"Expected CAPABILITY_DECLARATION, got {response.message_type}")

        # Extract session info
        self._session_id = response.session_id
        self._server_agent_id = response.from_agent

        # Extract server capabilities from capability declaration
        capabilities = response.payload.get("capabilities", [])
        if isinstance(capabilities, list):
            # Capabilities can be strings or dict objects
            self._server_capabilities = []
            for cap in capabilities:
                if isinstance(cap, str):
                    self._server_capabilities.append(cap)
                elif isinstance(cap, dict):
                    self._server_capabilities.append(cap.get("name", ""))
        else:
            self._server_capabilities = []

        self._connected = True
        logger.info(f"Connected to {server_url}, session: {self._session_id}")

        return {
            "session_id": self._session_id,
            "server_agent_id": self._server_agent_id,
            "server_capabilities": self._server_capabilities,
            "server_name": response.payload.get("agent_name"),
            "server_version": response.payload.get("agent_version")
        }

    async def disconnect(self) -> None:
        """
        Disconnect from server and end session.

        Sends SESSION_END message to gracefully close the session.
        """
        if not self._connected:
            return

        logger.info(f"Disconnecting from {self._server_url}")

        try:
            # Send session end message
            session_end = AISMessage.create_session_end(
                from_agent=self.agent_id,
                to_agent=self._server_agent_id,
                session_id=self._session_id,
                reason="client_disconnect"
            )

            await self._send_with_auth(session_end)
        except Exception as e:
            logger.warning(f"Error sending session end: {e}")
        finally:
            # Clean up
            if self._transport:
                await self._transport.close()

            self._connected = False
            self._session_id = None
            self._server_agent_id = None
            self._server_capabilities = []
            self._transport = None

        logger.info("Disconnected")

    async def call(
        self,
        capability: str,
        parameters: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None,
        timeout: Optional[float] = None,
    ) -> Any:
        """
        Call a capability on the connected server.

        Args:
            capability: Capability name to invoke
            parameters: Parameters for the capability
            context: Additional context for the request
            timeout: Request timeout in seconds

        Returns:
            Result from the capability execution

        Raises:
            SessionError: If not connected
            TimeoutError: If request times out
            AISException: On capability execution errors
        """
        if not self._connected:
            raise SessionError("Not connected. Call connect() first.")

        # Create request message
        request = AISMessage.create_request(
            from_agent=self.agent_id,
            to_agent=self._server_agent_id,
            session_id=self._session_id,
            capability=capability,
            parameters=parameters or {},
            context=context
        )

        # Send request with timeout
        try:
            response = await asyncio.wait_for(
                self._send_with_auth(request),
                timeout=timeout or self.timeout
            )
        except asyncio.TimeoutError:
            raise TimeoutError(
                f"Request to {capability} timed out",
                timeout_seconds=timeout or self.timeout,
                operation="call"
            )

        # Handle response
        if response.message_type == MessageType.RESPONSE:
            if response.payload.get("status") == "success":
                return response.payload.get("result")
            else:
                error = response.payload.get("error", "Unknown error")
                raise AISException(f"Capability call failed: {error}")

        elif response.message_type == MessageType.ERROR:
            error_msg = response.payload.get("error_message", "Unknown error")
            error_code = response.payload.get("error_code", "unknown")
            raise AISException(f"[{error_code}] {error_msg}")

        else:
            raise AISException(f"Unexpected response type: {response.message_type}")

    async def call_with_retry(
        self,
        capability: str,
        parameters: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None,
        timeout: Optional[float] = None,
        retry_config: Optional[RetryConfig] = None,
    ) -> Any:
        """
        Call a capability with automatic retry logic.

        Args:
            capability: Capability name to invoke
            parameters: Parameters for the capability
            context: Additional context for the request
            timeout: Request timeout in seconds
            retry_config: Override default retry configuration

        Returns:
            Result from the capability execution

        Raises:
            SessionError: If not connected
            AISException: On capability execution errors after all retries
        """
        config = retry_config or self.retry_config
        last_exception = None

        for attempt in range(1, config.max_retries + 1):
            try:
                logger.debug(f"Attempt {attempt}/{config.max_retries} for {capability}")

                result = await self.call(
                    capability=capability,
                    parameters=parameters,
                    context=context,
                    timeout=timeout
                )

                if attempt > 1:
                    logger.info(f"Succeeded on attempt {attempt}")

                return result

            except Exception as e:
                last_exception = e

                # Check if we should retry
                if not config.should_retry(e):
                    logger.debug(f"Not retrying {type(e).__name__}")
                    raise

                # Check if we have retries left
                if attempt >= config.max_retries:
                    logger.warning(f"Max retries ({config.max_retries}) reached")
                    raise

                # Calculate delay
                delay = config.get_delay(attempt)

                # Special handling for rate limits
                if isinstance(e, RateLimitError) and e.retry_after:
                    delay = max(delay, e.retry_after)

                logger.info(
                    f"Attempt {attempt} failed with {type(e).__name__}, "
                    f"retrying in {delay:.2f}s"
                )

                await asyncio.sleep(delay)

        # Should never reach here, but just in case
        raise last_exception

    async def _send_with_auth(self, message: AISMessage) -> AISMessage:
        """
        Send message with authentication header.

        Args:
            message: Message to send

        Returns:
            Response message
        """
        if not self._transport or not self._server_url:
            raise SessionError("Transport not initialized")

        # For now, HTTP transport doesn't support auth headers directly
        # This would be extended in a real implementation
        response = await self._transport.send(message, self._server_url)
        return response

    def has_capability(self, capability: str) -> bool:
        """
        Check if server has a specific capability.

        Args:
            capability: Capability name to check

        Returns:
            True if server has the capability
        """
        return capability in self._server_capabilities

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.disconnect()


# ============================================================================
# Connection Pool
# ============================================================================

class ConnectionPool:
    """
    Pool of AIS client connections for load balancing and failover.

    Example:
        ```python
        pool = ConnectionPool(
            agent_id="agent://example.com/client",
            servers=["http://server1:8000", "http://server2:8000"]
        )

        await pool.initialize()

        result = await pool.call("search", {"query": "test"})

        await pool.close()
        ```
    """

    def __init__(
        self,
        agent_id: str,
        servers: List[str],
        agent_name: Optional[str] = None,
        max_clients_per_server: int = 5,
        retry_config: Optional[RetryConfig] = None,
    ):
        """
        Initialize connection pool.

        Args:
            agent_id: Client agent identifier
            servers: List of server URLs
            agent_name: Human-readable client name
            max_clients_per_server: Maximum connections per server
            retry_config: Retry configuration
        """
        self.agent_id = agent_id
        self.servers = servers
        self.agent_name = agent_name
        self.max_clients_per_server = max_clients_per_server
        self.retry_config = retry_config or RetryConfig()

        self._clients: Dict[str, List[AISClient]] = {}
        self._available: Dict[str, asyncio.Queue] = {}
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize connections to all servers."""
        if self._initialized:
            return

        for server_url in self.servers:
            self._clients[server_url] = []
            self._available[server_url] = asyncio.Queue(maxsize=self.max_clients_per_server)

            # Create initial client
            client = AISClient(
                agent_id=self.agent_id,
                agent_name=self.agent_name,
                retry_config=self.retry_config
            )

            try:
                await client.connect(server_url)
                self._clients[server_url].append(client)
                await self._available[server_url].put(client)
            except Exception as e:
                logger.error(f"Failed to connect to {server_url}: {e}")

        self._initialized = True

    async def call(
        self,
        capability: str,
        parameters: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Any:
        """
        Call capability on any available server.

        Args:
            capability: Capability name
            parameters: Parameters for capability
            **kwargs: Additional arguments for call()

        Returns:
            Result from capability execution
        """
        if not self._initialized:
            await self.initialize()

        # Try each server
        last_exception = None
        for server_url in self.servers:
            if server_url not in self._available or self._available[server_url].empty():
                continue

            try:
                client = await self._available[server_url].get()
                try:
                    result = await client.call_with_retry(
                        capability=capability,
                        parameters=parameters,
                        **kwargs
                    )
                    return result
                finally:
                    await self._available[server_url].put(client)
            except Exception as e:
                last_exception = e
                logger.warning(f"Call to {server_url} failed: {e}")
                continue

        raise TransportError(
            f"All servers failed for capability {capability}",
            transport_type="pool"
        )

    async def close(self) -> None:
        """Close all connections."""
        for server_url, clients in self._clients.items():
            for client in clients:
                try:
                    await client.disconnect()
                except Exception as e:
                    logger.warning(f"Error disconnecting from {server_url}: {e}")

        self._clients.clear()
        self._available.clear()
        self._initialized = False
