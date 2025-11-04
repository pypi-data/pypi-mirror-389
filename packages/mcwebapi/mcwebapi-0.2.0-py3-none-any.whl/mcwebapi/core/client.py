import logging
import time
from typing import Dict, Optional

from .promise import Promise
from .connection import ConnectionManager


class MinecraftClient:
    """
    Main client for communicating with Minecraft WebSocket API.

    Handles request/response cycle, authentication, and high-level API operations.
    """

    def __init__(
            self,
            host: str = "localhost",
            port: int = 8765,
            auth_key: str = "default-secret-key-change-me",
            timeout: float = 10.0,
    ):
        self.auth_key = auth_key
        self.timeout = timeout

        self.connection = ConnectionManager(host, port)
        self._pending_requests: Dict[str, Promise] = {}
        self._authenticated = False
        self._message_id = 0

    def connect(self) -> None:
        """Establish connection and authenticate with server."""
        try:
            # Establish WebSocket connection
            self.connection.connect()
            self.connection.start_receiver(self._handle_message)

            # Authentication flow
            self._authenticate()

        except Exception as e:
            self.connection.disconnect()
            raise ConnectionError(f"Failed to connect: {e}")

    def disconnect(self) -> None:
        """Close connection and cleanup."""
        self._authenticated = False
        self.connection.disconnect()

    def is_authenticated(self) -> bool:
        """Check authentication status."""
        return self._authenticated

    def is_connected(self) -> bool:
        """Check connection status."""
        return self.connection.is_connected()

    def has_pending_requests(self) -> bool:
        """Check pending requests status."""
        return self._pending_requests != {}

    def send_request(self, module: str, method: str, args: Optional[list] = None) -> Promise:
        """
        Send request to server and return a Promise.

        Args:
            module: API module name (e.g., 'player', 'world')
            method: Method name to call
            args: List of arguments for the method

        Returns:
            Promise that will resolve with the response

        Raises:
            ConnectionError: If not connected or authenticated
        """
        if not self.is_connected():
            raise ConnectionError("Not connected to server")

        if not self._authenticated and module != "auth":
            raise ConnectionError("Not authenticated. Call connect() first.")

        request_id = self._generate_request_id()
        promise = Promise(timeout=self.timeout)
        self._pending_requests[request_id] = promise

        message = {
            "type": "REQUEST",
            "module": module,
            "method": method,
            "args": args or [],
            "requestId": request_id,
            "timestamp": time.time(),
        }

        try:
            logging.info(f"Sending message: {message}")
            self.connection.send_message(message)
        except Exception as e:
            promise.reject(e)
            del self._pending_requests[request_id]

        return promise

    def _authenticate(self) -> None:
        """Perform authentication flow."""
        check_result = self.send_request("auth", "check", []).wait()
        logging.info(f"Auth check (no auth): {check_result}")

        auth_info = self.send_request("auth", "getInfo", []).wait()
        logging.info(f"Auth info: {auth_info}")

        auth_result = self.send_request("auth", "authenticate", [self.auth_key]).wait()
        logging.info(f"Authentication result: {auth_result}")

        if auth_result.get("success"):
            self._authenticated = True
            logging.info("Successfully authenticated!")

            # Verify authentication
            check_result = self.send_request("auth", "check", []).wait()
            logging.info(f"Auth check: {check_result}")
        else:
            raise ConnectionError(f"Authentication failed: {auth_result.get('message')}")

    def _handle_message(self, raw_message: str) -> None:
        """Handle incoming WebSocket messages."""
        try:
            if not raw_message or raw_message.strip() == "":
                return

            message = self.connection._decode_message(raw_message)

            request_id = message.get("requestId")
            if not request_id or request_id not in self._pending_requests:
                return

            promise = self._pending_requests.pop(request_id)
            message_type = message.get("type")

            if message_type == "RESPONSE":
                if message.get("status") == "SUCCESS":
                    promise.resolve(message.get("data"))
                else:
                    error_data = message.get("data", {})
                    error_msg = error_data.get("message", "Unknown error")
                    promise.reject(Exception(f"{error_data.get('code', 'UNKNOWN')}: {error_msg}"))

            elif message_type == "ERROR":
                error_data = message.get("data", {})
                error_msg = error_data.get("message", "Unknown error")
                promise.reject(Exception(f"{error_data.get('code', 'UNKNOWN')}: {error_msg}"))

        except Exception as e:
            logging.error(f"Error handling message: {e}")

    def _generate_request_id(self) -> str:
        """Generate short unique request ID."""
        self._message_id = (self._message_id + 1) % 4096
        return format(self._message_id, "03x")
