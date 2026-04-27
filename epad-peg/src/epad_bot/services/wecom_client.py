"""WeCom Bot WebSocket client service."""

import json
import logging
from typing import Any

import websockets
from websockets.asyncio.client import ClientConnection

from epad_bot.config import get_settings

logger = logging.getLogger(__name__)


class WecomBotClient:
    """WebSocket client for WeCom bot communication."""

    def __init__(self) -> None:
        """Initialize the WeCom bot client."""
        self._settings = get_settings()
        self._connection: ClientConnection | None = None

    @property
    def is_connected(self) -> bool:
        """Check if WebSocket connection is active."""
        return self._connection is not None

    async def connect(self) -> None:
        """Establish WebSocket connection to WeCom server."""
        if self._connection is not None:
            logger.warning("Already connected to WeCom server")
            return

        ws_url = self._build_ws_url()
        logger.info(f"Connecting to WeCom WebSocket: {ws_url}")

        try:
            self._connection = await websockets.connect(ws_url)
            logger.info("Successfully connected to WeCom server")
        except Exception as e:
            logger.error(f"Failed to connect to WeCom server: {e}")
            raise

    async def disconnect(self) -> None:
        """Close WebSocket connection."""
        if self._connection is None:
            return

        await self._connection.close()
        self._connection = None
        logger.info("Disconnected from WeCom server")

    async def receive_message(self) -> dict[str, Any] | None:
        """Receive and parse a message from the WebSocket."""
        if self._connection is None:
            logger.error("Not connected to WeCom server")
            return None

        try:
            raw_message = await self._connection.recv()
            message: dict[str, Any] = json.loads(raw_message)
            logger.debug(f"Received message: {message}")
            return message
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse message: {e}")
            return None
        except Exception as e:
            logger.error(f"Error receiving message: {e}")
            return None

    async def send_message(self, message: dict[str, Any]) -> bool:
        """Send a message through the WebSocket."""
        if self._connection is None:
            logger.error("Not connected to WeCom server")
            return False

        try:
            raw_message = json.dumps(message)
            await self._connection.send(raw_message)
            logger.debug(f"Sent message: {message}")
            return True
        except Exception as e:
            logger.error(f"Failed to send message: {e}")
            return False

    def _build_ws_url(self) -> str:
        """Build WebSocket URL with authentication parameters."""
        base_url = self._settings.wecom_bot_ws_url.rstrip("/")
        bot_id = self._settings.wecom_bot_id
        bot_secret = self._settings.wecom_bot_secret
        return f"{base_url}?bot_id={bot_id}&secret={bot_secret}"


# Global client instance
_client: WecomBotClient | None = None


def get_wecom_client() -> WecomBotClient:
    """Get or create the global WeCom bot client instance."""
    global _client
    if _client is None:
        _client = WecomBotClient()
    return _client
