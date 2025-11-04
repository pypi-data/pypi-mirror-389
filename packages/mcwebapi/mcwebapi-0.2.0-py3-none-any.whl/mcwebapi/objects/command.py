from .base import SocketInstance
from ..api import MinecraftClient


class Command(SocketInstance):
    """Command object for executing server commands"""

    def __init__(self, client: MinecraftClient):
        super().__init__("command", client)