"""
Feishu Bot Service - SDK Layer

Generic bot service with NO business logic dependencies.
All business dependencies are injected via setters.
"""
import logging
from datetime import datetime
from typing import Any, Optional, Dict

from feishu_sdk.core.client import FeishuClient
from feishu_sdk.config.config import FeishuConfig
from feishu_sdk.config.protocols import EventHandlerProtocol

logger = logging.getLogger(__name__)


class FeishuBotService:
    """Feishu Bot Service - SDK Layer
    
    Generic bot service with dependency injection.
    NO business logic - all dependencies are injected.
    """
    
    def __init__(self, config: Optional[FeishuConfig] = None):
        """Initialize bot service
        
        Args:
            config: Optional FeishuConfig instance
        """
        self.client = FeishuClient(config) if config else None
        self._event_handler: Optional[EventHandlerProtocol] = None
    
    def set_event_handler(self, handler: EventHandlerProtocol) -> None:
        """Inject event handler
        
        Args:
            handler: Event handler instance
        """
        self._event_handler = handler
    
    async def send_message(
        self,
        receive_id: str,
        content: str,
        receive_id_type: str = "chat_id"
    ) -> Optional[str]:
        """Send a message
        
        Args:
            receive_id: Target ID
            content: Message content
            receive_id_type: ID type
            
        Returns:
            Message ID if successful
        """
        if not self.client:
            logger.error("Client not configured")
            return None
        
        return await self.client.send_message(
            receive_id=receive_id,
            content=content,
            receive_id_type=receive_id_type
        )


__all__ = [
    'FeishuBotService',
]
