"""
AIS Protocol Transport Layer

HTTP and WebSocket transport implementation for AIS message exchange.
"""

import asyncio
import logging
from typing import Optional, Callable, Dict, Any
from uuid import uuid4
from aiohttp import web, ClientSession, ClientTimeout, ClientError, WSMsgType
import json

from .message import AISMessage
from .exceptions import TransportError, TimeoutError as AISTimeoutError, ValidationError
from .constants import (
    AIS_HTTP_ENDPOINT as MESSAGE_ENDPOINT,
    AIS_WEBSOCKET_ENDPOINT as WEBSOCKET_ENDPOINT,
    AIS_HEALTH_ENDPOINT as HEALTH_ENDPOINT
)

# Configure logging
logger = logging.getLogger(__name__)


# ============================================================================
# HTTP Transport
# ============================================================================

class HTTPTransport:
    """
    HTTP transport for AIS protocol messages.

    Provides both client (send) and server (receive) functionality
    using aiohttp for async HTTP operations.

    Features:
    - Async message sending with retry logic
    - HTTP server for receiving messages
    - Health check endpoint
    - Configurable timeouts
    - Comprehensive error handling

    Example:
        # Client usage
        transport = HTTPTransport()
        response = await transport.send(message, "http://agent.example.com:8000")

        # Server usage
        transport = HTTPTransport()
        transport.set_message_handler(my_handler)
        await transport.start_server(host="0.0.0.0", port=8000)
    """

    def __init__(self, base_url: Optional[str] = None):
        """
        Initialize HTTP transport.

        Args:
            base_url: Base URL for this agent (used in server mode)
        """
        self.base_url = base_url
        self._message_handler: Optional[Callable[[AISMessage], AISMessage]] = None
        self._app: Optional[web.Application] = None
        self._runner: Optional[web.AppRunner] = None
        self._site: Optional[web.TCPSite] = None
        self._session: Optional[ClientSession] = None

        logger.info(f"HTTPTransport initialized with base_url={base_url}")

    def set_message_handler(self, handler: Callable[[AISMessage], AISMessage]) -> None:
        """
        Set the message handler function for incoming messages.

        Args:
            handler: Async function that takes AISMessage and returns AISMessage
        """
        self._message_handler = handler
        logger.info("Message handler set")

    # ========================================================================
    # Client Methods (Sending Messages)
    # ========================================================================

    async def send(
        self,
        message: AISMessage,
        target_url: str,
        timeout: int = 30
    ) -> AISMessage:
        """
        Send AIS message to target agent via HTTP POST.

        Args:
            message: AISMessage to send
            target_url: Base URL of target agent (e.g., "http://agent.example.com:8000")
            timeout: Request timeout in seconds (default: 30)

        Returns:
            AISMessage response from target agent

        Raises:
            TransportError: If HTTP request fails
            TimeoutError: If request times out
            ValidationError: If response is not valid AIS message
        """
        # Construct full endpoint URL
        if not target_url.startswith(("http://", "https://")):
            raise TransportError(
                f"Invalid target URL (must start with http:// or https://): {target_url}",
                details={"target_url": target_url}
            )

        endpoint_url = target_url.rstrip("/") + MESSAGE_ENDPOINT

        logger.debug(f"Sending {message.message_type} to {endpoint_url}")

        # Create session if needed
        if self._session is None or self._session.closed:
            self._session = ClientSession()

        try:
            # Configure timeout
            client_timeout = ClientTimeout(total=timeout)

            # Send POST request
            async with self._session.post(
                endpoint_url,
                json=message.to_dict(),
                timeout=client_timeout,
                headers={"Content-Type": "application/json"}
            ) as response:
                # Check HTTP status
                if response.status != 200:
                    error_text = await response.text()
                    raise TransportError(
                        f"HTTP {response.status}: {error_text}",
                        details={
                            "status_code": response.status,
                            "target_url": endpoint_url,
                            "response_text": error_text[:500]  # Limit error text
                        }
                    )

                # Parse response
                try:
                    response_data = await response.json()
                except json.JSONDecodeError as e:
                    raise TransportError(
                        f"Invalid JSON response: {e}",
                        details={"target_url": endpoint_url}
                    )

                # Validate response is AIS message
                try:
                    response_message = AISMessage.from_dict(response_data)
                    logger.debug(f"Received {response_message.message_type} from {endpoint_url}")
                    return response_message
                except Exception as e:
                    raise ValidationError(
                        f"Response is not valid AIS message: {e}",
                        details={"response_data": response_data}
                    )

        except asyncio.TimeoutError:
            raise AISTimeoutError(
                f"Request timed out after {timeout}s",
                details={"target_url": endpoint_url, "timeout": timeout}
            )

        except ClientError as e:
            raise TransportError(
                f"HTTP client error: {e}",
                details={"target_url": endpoint_url, "error_type": type(e).__name__}
            )

        except (TransportError, AISTimeoutError, ValidationError):
            # Re-raise AIS exceptions as-is
            raise

        except Exception as e:
            # Wrap unexpected exceptions
            raise TransportError(
                f"Unexpected error sending message: {e}",
                details={"target_url": endpoint_url, "error_type": type(e).__name__}
            )

    # ========================================================================
    # Server Methods (Receiving Messages)
    # ========================================================================

    async def _handle_message(self, request: web.Request) -> web.Response:
        """
        Handle incoming AIS message (HTTP POST handler).

        Args:
            request: aiohttp Request object

        Returns:
            aiohttp Response with AIS message or error
        """
        if not self._message_handler:
            logger.error("No message handler set")
            return web.Response(
                status=500,
                text=json.dumps({
                    "error": "Server not configured",
                    "message": "No message handler set"
                }),
                content_type="application/json"
            )

        try:
            # Parse request body
            try:
                request_data = await request.json()
            except json.JSONDecodeError as e:
                logger.warning(f"Invalid JSON in request: {e}")
                return web.Response(
                    status=400,
                    text=json.dumps({
                        "error": "Invalid JSON",
                        "message": str(e)
                    }),
                    content_type="application/json"
                )

            # Parse AIS message
            try:
                message = AISMessage.from_dict(request_data)
                logger.debug(f"Received {message.message_type} from {message.from_agent}")
            except Exception as e:
                logger.warning(f"Invalid AIS message: {e}")
                return web.Response(
                    status=400,
                    text=json.dumps({
                        "error": "Invalid AIS message",
                        "message": str(e)
                    }),
                    content_type="application/json"
                )

            # Call message handler
            try:
                response_message = await self._message_handler(message)
                logger.debug(f"Sending {response_message.message_type} to {message.from_agent}")

                return web.Response(
                    status=200,
                    text=json.dumps(response_message.to_dict()),
                    content_type="application/json"
                )

            except Exception as e:
                logger.error(f"Error in message handler: {e}", exc_info=True)
                return web.Response(
                    status=500,
                    text=json.dumps({
                        "error": "Internal server error",
                        "message": "Error processing message"
                    }),
                    content_type="application/json"
                )

        except Exception as e:
            logger.error(f"Unexpected error handling message: {e}", exc_info=True)
            return web.Response(
                status=500,
                text=json.dumps({
                    "error": "Internal server error",
                    "message": str(e)
                }),
                content_type="application/json"
            )

    async def _health_check(self, request: web.Request) -> web.Response:
        """
        Health check endpoint.

        Returns 200 OK with status information.
        """
        health_data = {
            "status": "healthy",
            "service": "AIS Protocol Agent",
            "version": "0.1",
            "has_handler": self._message_handler is not None
        }

        return web.Response(
            status=200,
            text=json.dumps(health_data),
            content_type="application/json"
        )

    async def start_server(
        self,
        host: str = "0.0.0.0",
        port: int = 8000
    ) -> None:
        """
        Start HTTP server to receive messages.

        Args:
            host: Host to bind to (default: 0.0.0.0 for all interfaces)
            port: Port to bind to (default: 8000)

        Raises:
            TransportError: If server fails to start
        """
        if self._runner:
            raise TransportError("Server already running")

        if not self._message_handler:
            raise TransportError("Cannot start server without message handler")

        try:
            # Create application
            self._app = web.Application()

            # Add routes
            self._app.router.add_post(MESSAGE_ENDPOINT, self._handle_message)
            self._app.router.add_get(HEALTH_ENDPOINT, self._health_check)

            # Create runner
            self._runner = web.AppRunner(self._app)
            await self._runner.setup()

            # Create site
            self._site = web.TCPSite(self._runner, host, port)
            await self._site.start()

            logger.info(f"HTTP server started on {host}:{port}")
            logger.info(f"Message endpoint: http://{host}:{port}{MESSAGE_ENDPOINT}")
            logger.info(f"Health endpoint: http://{host}:{port}{HEALTH_ENDPOINT}")

        except Exception as e:
            logger.error(f"Failed to start server: {e}", exc_info=True)
            raise TransportError(
                f"Failed to start server: {e}",
                details={"host": host, "port": port}
            )

    async def stop_server(self) -> None:
        """
        Stop HTTP server gracefully.

        Raises:
            TransportError: If server is not running
        """
        if not self._runner:
            raise TransportError("Server not running")

        try:
            logger.info("Stopping HTTP server...")

            # Stop site
            if self._site:
                await self._site.stop()
                self._site = None

            # Cleanup runner
            if self._runner:
                await self._runner.cleanup()
                self._runner = None

            self._app = None

            logger.info("HTTP server stopped")

        except Exception as e:
            logger.error(f"Error stopping server: {e}", exc_info=True)
            raise TransportError(f"Error stopping server: {e}")

    async def close(self) -> None:
        """
        Close transport and cleanup resources.

        Call this when done using the transport to cleanup HTTP sessions.
        """
        # Close client session
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None
            logger.debug("Client session closed")

        # Stop server if running
        if self._runner:
            await self.stop_server()

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()


# ============================================================================
# WebSocket Transport
# ============================================================================

class WebSocketTransport:
    """
    WebSocket transport for AIS protocol messages.

    Provides persistent bidirectional connections for real-time agent communication.

    Features:
    - Persistent connections
    - Real-time message exchange
    - Connection management
    - Automatic cleanup

    Example:
        transport = WebSocketTransport()
        transport.set_message_handler(my_handler)
        await transport.start_server(host="0.0.0.0", port=8000)
    """

    def __init__(self):
        """Initialize WebSocket transport."""
        self._message_handler: Optional[Callable[[AISMessage], AISMessage]] = None
        self._connections: Dict[str, web.WebSocketResponse] = {}
        self._app: Optional[web.Application] = None
        self._runner: Optional[web.AppRunner] = None
        self._site: Optional[web.TCPSite] = None

        logger.info("WebSocketTransport initialized")

    def set_message_handler(self, handler: Callable[[AISMessage], AISMessage]) -> None:
        """
        Set the message handler function for incoming messages.

        Args:
            handler: Async function that takes AISMessage and returns AISMessage
        """
        self._message_handler = handler
        logger.info("Message handler set for WebSocket")

    async def _handle_websocket(self, request: web.Request) -> web.WebSocketResponse:
        """
        Handle WebSocket connection.

        Args:
            request: aiohttp Request object

        Returns:
            WebSocketResponse
        """
        ws = web.WebSocketResponse()
        await ws.prepare(request)

        connection_id = str(uuid4())
        self._connections[connection_id] = ws

        logger.info(f"WebSocket connection established: {connection_id}")

        try:
            async for msg in ws:
                if msg.type == WSMsgType.TEXT:
                    try:
                        # Parse incoming message
                        message = AISMessage.from_json(msg.data)
                        logger.debug(f"Received {message.message_type} via WebSocket from {message.from_agent}")

                        # Process message
                        if not self._message_handler:
                            error_response = AISMessage.create_error(
                                from_agent="server",
                                to_agent=message.from_agent,
                                error_code="internal_error",
                                error_message="No message handler configured",
                                session_id=message.session_id
                            )
                            await ws.send_str(error_response.to_json())
                            continue

                        response = await self._message_handler(message)
                        logger.debug(f"Sending {response.message_type} via WebSocket to {message.from_agent}")

                        # Send response
                        await ws.send_str(response.to_json())

                    except Exception as e:
                        logger.exception(f"Error processing WebSocket message: {e}")
                        try:
                            error_msg = {
                                "error": "message_processing_failed",
                                "details": str(e)
                            }
                            await ws.send_json(error_msg)
                        except:
                            pass

                elif msg.type == WSMsgType.ERROR:
                    logger.error(f"WebSocket error: {ws.exception()}")

        except Exception as e:
            logger.exception(f"Error in WebSocket handler: {e}")

        finally:
            # Cleanup connection
            if connection_id in self._connections:
                del self._connections[connection_id]
            logger.info(f"WebSocket connection closed: {connection_id}")

        return ws

    async def start_server(
        self,
        host: str = "0.0.0.0",
        port: int = 8000
    ) -> None:
        """
        Start WebSocket server.

        Args:
            host: Host to bind to (default: 0.0.0.0 for all interfaces)
            port: Port to bind to (default: 8000)

        Raises:
            TransportError: If server fails to start
        """
        if self._runner:
            raise TransportError("Server already running")

        if not self._message_handler:
            raise TransportError("Cannot start server without message handler")

        try:
            # Create application
            self._app = web.Application()

            # Add WebSocket route
            self._app.router.add_get(WEBSOCKET_ENDPOINT, self._handle_websocket)

            # Create runner
            self._runner = web.AppRunner(self._app)
            await self._runner.setup()

            # Create site
            self._site = web.TCPSite(self._runner, host, port)
            await self._site.start()

            logger.info(f"WebSocket server started on {host}:{port}")
            logger.info(f"WebSocket endpoint: ws://{host}:{port}{WEBSOCKET_ENDPOINT}")

        except Exception as e:
            logger.error(f"Failed to start WebSocket server: {e}", exc_info=True)
            raise TransportError(
                f"Failed to start server: {e}",
                details={"host": host, "port": port}
            )

    async def stop_server(self) -> None:
        """
        Stop WebSocket server gracefully.

        Raises:
            TransportError: If server is not running
        """
        if not self._runner:
            raise TransportError("Server not running")

        try:
            logger.info("Stopping WebSocket server...")

            # Close all connections
            for connection_id, ws in list(self._connections.items()):
                try:
                    await ws.close()
                except:
                    pass
            self._connections.clear()

            # Stop site
            if self._site:
                await self._site.stop()
                self._site = None

            # Cleanup runner
            if self._runner:
                await self._runner.cleanup()
                self._runner = None

            self._app = None

            logger.info("WebSocket server stopped")

        except Exception as e:
            logger.error(f"Error stopping WebSocket server: {e}", exc_info=True)
            raise TransportError(f"Error stopping server: {e}")

    def get_connection_count(self) -> int:
        """Get number of active WebSocket connections."""
        return len(self._connections)


# ============================================================================
# Combined Transport
# ============================================================================

class CombinedTransport:
    """
    Combined HTTP and WebSocket transport on the same port.

    Provides both HTTP (for request/response) and WebSocket (for streaming)
    on a single server instance.

    Features:
    - HTTP POST for request/response
    - WebSocket for streaming and bidirectional communication
    - Single port for both transports
    - Shared message handler

    Example:
        transport = CombinedTransport()
        transport.set_message_handler(my_handler)
        await transport.start(host="0.0.0.0", port=8000)
    """

    def __init__(self):
        """Initialize combined transport."""
        self._message_handler: Optional[Callable[[AISMessage], AISMessage]] = None
        self._app: Optional[web.Application] = None
        self._runner: Optional[web.AppRunner] = None
        self._site: Optional[web.TCPSite] = None
        self._ws_connections: Dict[str, web.WebSocketResponse] = {}
        self._session: Optional[ClientSession] = None

        # Create individual transport components for delegation
        self._http = HTTPTransport()
        self._ws = WebSocketTransport()

        logger.info("CombinedTransport initialized")

    def set_message_handler(self, handler: Callable[[AISMessage], AISMessage]) -> None:
        """
        Set the message handler function for incoming messages.

        Args:
            handler: Async function that takes AISMessage and returns AISMessage
        """
        self._message_handler = handler
        self._http.set_message_handler(handler)
        self._ws.set_message_handler(handler)
        logger.info("Message handler set for combined transport")

    async def start(
        self,
        host: str = "0.0.0.0",
        port: int = 8000
    ) -> None:
        """
        Start combined HTTP and WebSocket server on same port.

        Args:
            host: Host to bind to (default: 0.0.0.0 for all interfaces)
            port: Port to bind to (default: 8000)

        Raises:
            TransportError: If server fails to start
        """
        if self._runner:
            raise TransportError("Server already running")

        if not self._message_handler:
            raise TransportError("Cannot start server without message handler")

        try:
            # Create application
            self._app = web.Application()

            # Add HTTP routes
            self._app.router.add_post(MESSAGE_ENDPOINT, self._http._handle_message)
            self._app.router.add_get(HEALTH_ENDPOINT, self._http._health_check)

            # Add WebSocket route
            self._app.router.add_get(WEBSOCKET_ENDPOINT, self._ws._handle_websocket)

            # Create runner
            self._runner = web.AppRunner(self._app)
            await self._runner.setup()

            # Create site
            self._site = web.TCPSite(self._runner, host, port)
            await self._site.start()

            logger.info(f"AIS Combined Transport started on {host}:{port}")
            logger.info(f"HTTP endpoint: http://{host}:{port}{MESSAGE_ENDPOINT}")
            logger.info(f"WebSocket endpoint: ws://{host}:{port}{WEBSOCKET_ENDPOINT}")
            logger.info(f"Health endpoint: http://{host}:{port}{HEALTH_ENDPOINT}")

        except Exception as e:
            logger.error(f"Failed to start combined transport: {e}", exc_info=True)
            raise TransportError(
                f"Failed to start server: {e}",
                details={"host": host, "port": port}
            )

    async def stop(self) -> None:
        """
        Stop combined transport gracefully.

        Raises:
            TransportError: If server is not running
        """
        if not self._runner:
            raise TransportError("Server not running")

        try:
            logger.info("Stopping combined transport...")

            # Close all WebSocket connections
            for connection_id, ws in list(self._ws._connections.items()):
                try:
                    await ws.close()
                except:
                    pass
            self._ws._connections.clear()

            # Stop site
            if self._site:
                await self._site.stop()
                self._site = None

            # Cleanup runner
            if self._runner:
                await self._runner.cleanup()
                self._runner = None

            self._app = None

            logger.info("Combined transport stopped")

        except Exception as e:
            logger.error(f"Error stopping combined transport: {e}", exc_info=True)
            raise TransportError(f"Error stopping server: {e}")

    async def send(
        self,
        message: AISMessage,
        target_url: str,
        timeout: int = 30
    ) -> AISMessage:
        """
        Send message via HTTP (delegates to HTTPTransport).

        Args:
            message: AISMessage to send
            target_url: Base URL of target agent
            timeout: Request timeout in seconds

        Returns:
            AISMessage response
        """
        return await self._http.send(message, target_url, timeout)

    def get_connection_count(self) -> int:
        """Get number of active WebSocket connections."""
        return len(self._ws._connections)

    async def close(self) -> None:
        """Close transport and cleanup resources."""
        # Close HTTP session
        await self._http.close()

        # Stop server if running
        if self._runner:
            await self.stop()

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
