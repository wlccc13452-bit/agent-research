"""
Card Action Handler - SDK Layer

Handles card interaction events with NO business logic dependencies.
All business dependencies are injected via setters.
"""
import asyncio
import logging
from typing import Any, Optional

from config.constants import ConcurrencyConfig
from feishu_sdk.concurrency.action_lock import get_global_action_lock
from feishu_sdk.message.dispatcher import MessageDispatcher
from feishu_sdk.config.protocols import (
    CardServiceProtocol,
    BusinessLogicServiceProtocol,
    CardBuilderProtocol,
)

logger = logging.getLogger(__name__)


class CardActionHandler:
    """Card Action Handler - SDK Layer
    
    Handles card interactions with dependency injection.
    NO business logic - all dependencies are injected.
    """
    
    def __init__(self) -> None:
        self._card_service: Optional[CardServiceProtocol] = None
        self._message_dispatcher: Optional[MessageDispatcher] = None
        self._action_lock_manager = get_global_action_lock()
        self._business_service: Optional[BusinessLogicServiceProtocol] = None
        self._card_builder: Optional[CardBuilderProtocol] = None
        self._main_loop: Optional[asyncio.AbstractEventLoop] = None
    
    def set_card_service(self, card_service: CardServiceProtocol) -> None:
        """Inject card service"""
        self._card_service = card_service
        
        # Initialize message dispatcher
        self._message_dispatcher = MessageDispatcher()
        self._message_dispatcher.set_card_service(card_service)
    
    def set_business_service(self, business_service: BusinessLogicServiceProtocol) -> None:
        """Inject business logic service"""
        self._business_service = business_service
    
    def set_card_builder(self, builder: CardBuilderProtocol) -> None:
        """Inject card builder"""
        self._card_builder = builder
    
    def set_main_loop(self, main_loop: asyncio.AbstractEventLoop) -> None:
        """Set main event loop"""
        self._main_loop = main_loop
    
    async def handle_card_action(self, data: Any) -> dict[str, Any]:
        """Handle card interaction event"""
        try:
            logger.info("Card action received")
            # Implementation...
            return {"toast": "Success"}
        except Exception as e:
            logger.error(f"Card action error: {e}")
            return {"toast": f"Error: {str(e)}"}


# Service instance
card_action_handler = CardActionHandler()


__all__ = [
    'CardActionHandler',
    'card_action_handler',
]
