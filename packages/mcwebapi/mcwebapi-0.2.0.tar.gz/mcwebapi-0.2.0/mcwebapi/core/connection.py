import logging

import websocket
import json
import base64
import threading
from typing import Optional, Callable


class ConnectionManager:
    """
    Manages WebSocket connection and message handling.

    Handles low-level WebSocket communication, message encoding/decoding,
    and connection state management.
    """

    def __init__(self, host: str = "localhost", port: int = 8765):
        self.host = host
        self.port = port
        self.ws: Optional[websocket.WebSocket] = None
        self._connected = False
        self._receiver_thread: Optional[threading.Thread] = None
        self._message_handler: Optional[Callable] = None

    def connect(self) -> None:
        """Establish WebSocket connection."""
        ws_url = f"ws://{self.host}:{self.port}/"
        logging.info(f"Connecting to {ws_url}")

        self.ws = websocket.WebSocket()
        self.ws.connect(ws_url)
        self._connected = True

    def disconnect(self) -> None:
        """Close WebSocket connection."""
        self._connected = False
        if self.ws:
            self.ws.close()
        if self._receiver_thread:
            self._receiver_thread.join(timeout=1)

    def is_connected(self) -> bool:
        """Check if connected to server."""
        return self._connected

    def send_message(self, message: dict) -> None:
        """Send encoded message through WebSocket."""
        if not self._connected or not self.ws:
            raise ConnectionError("Not connected to server")

        encoded_message = self._encode_message(message)
        self.ws.send(encoded_message)

    def start_receiver(self, message_handler: Callable) -> None:
        """Start message receiver thread."""
        self._message_handler = message_handler
        self._receiver_thread = threading.Thread(target=self._receiver_loop, daemon=False)
        self._receiver_thread.start()

    def _receiver_loop(self) -> None:
        """Main receiver loop for incoming messages."""
        while self._connected and self.ws:
            try:
                message = self.ws.recv()
                if self._message_handler:
                    self._message_handler(message)
            except Exception as e:
                if self._connected:
                    logging.error(f"Receiver error: {e}")
                break

    def _encode_message(self, message: dict) -> str:
        """Encode message to base64 string."""
        json_str = json.dumps(message, default=str)
        return base64.b64encode(json_str.encode()).decode()

    def _decode_message(self, message: str) -> dict:
        """Decode base64 string to message dict."""
        decoded = base64.b64decode(message).decode()
        return json.loads(decoded)