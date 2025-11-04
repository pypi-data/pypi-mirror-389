import time

from .core import MinecraftClient
from .objects import Player, Level, Command, Block


class MinecraftAPI:
    """
    High-level API client for Minecraft WebSocket API.

    Provides easy access to various entities (player, world, command, system)
    with a clean, intuitive interface.
    """

    def __init__(
            self,
            host: str = "localhost",
            port: int = 8765,
            auth_key: str = "default-secret-key-change-me",
            timeout: float = 10.0,
    ):
        self._client = MinecraftClient(host, port, auth_key, timeout)

        self.timeout = timeout

    def connect(self) -> None:
        """Connect to the Minecraft server."""
        self._client.connect()

    def disconnect(self) -> None:
        """Disconnect from the Minecraft server."""
        self._client.disconnect()

    def is_connected(self) -> bool:
        """Check if connected to server."""
        return self._client.is_connected()

    def is_authenticated(self) -> bool:
        """Check if authenticated with server."""
        return self._client.is_authenticated()

    def wait_for_pending(self):
        start_time = time.time()

        while self._client.has_pending_requests() and time.time() - start_time < self.timeout:
            time.sleep(0.1)

    def __enter__(self) -> "MinecraftAPI":
        """Context manager entry."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Wait for all promises to complete before disconnecting"""
        self.wait_for_pending()
        self.disconnect()

    def Player(self, identifier) -> Player:
        return Player(self._client, identifier)

    def Level(self, identifier) -> Level:
        return Level(self._client, identifier)

    def Block(self, *identifiers) -> Block:
        return Block(self._client, *identifiers)
