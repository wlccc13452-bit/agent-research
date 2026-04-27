"""
Dependency Injection Setup for Feishu Bot

This module configures all dependencies between SDK and application layers.
Run this at application startup to inject all business dependencies into SDK services.
"""
import logging
from typing import Optional

from feishu_sdk.core.card_service import FeishuCardService
from feishu_sdk.core.long_connection_service import FeishuLongConnectionService
from feishu_sdk.core.bot_service import FeishuBotService
from feishu_sdk.message.card_action_handler import CardActionHandler
from feishu_sdk.connection.websocket_service import WebSocketConnectionService

from services.feishu_bot.business.stock_business_service import BusinessLogicService
from services.feishu_bot.feishu_bot_card_service import CardService
from services.feishu_bot.cards import (
    StockCardBuilder,
    HoldingsCardBuilder,
    WatchlistCardBuilder,
    PriceAlertCardBuilder,
    MenuCardBuilder,
)
from services.feishu_bot.handlers.bot_handlers import (
    save_chat_message,
    save_chat_message_async,
    MessageHandler,
)
from services.feishu_bot.feishu_bot_commands import COMMAND_MAPPING, MENU_COMMANDS

logger = logging.getLogger(__name__)


class FeishuDependencyInjector:
    """Configures all dependencies between SDK and application layers"""
    
    def __init__(self):
        # SDK layer services
        self._sdk_card_service: Optional[FeishuCardService] = None
        self._long_connection_service: Optional[FeishuLongConnectionService] = None
        
        # Application layer services
        self._card_service: Optional[CardService] = None
        self._business_service: Optional[BusinessLogicService] = None
        self._card_action_handler: Optional[CardActionHandler] = None
    
    def setup_all_dependencies(self) -> None:
        """Setup all service dependencies in correct order"""
        logger.info("Setting up Feishu service dependencies...")
        
        # 1. Create services
        self._create_services()
        
        # 2. Inject dependencies
        self._inject_dependencies()
        
        # 3. Validate setup
        self._validate_setup()
        
        logger.info("[OK] All dependencies configured successfully")
    
    def _create_services(self) -> None:
        """Create all service instances"""
        # SDK layer services
        self._sdk_card_service = FeishuCardService()
        self._long_connection_service = FeishuLongConnectionService(
            command_mapping=COMMAND_MAPPING,
            menu_commands=MENU_COMMANDS,
        )
        
        # Application layer services
        self._card_service = CardService()
        self._business_service = BusinessLogicService()
        self._card_action_handler = CardActionHandler()
    
    def _inject_dependencies(self) -> None:
        """Inject dependencies between services"""
        
        # 1. Inject SDK card service into application card service
        self._card_service.set_sdk_card_service(self._sdk_card_service)
        
        # 2. Inject business service into card action handler
        self._card_action_handler.set_business_service(self._business_service)
        
        # 3. Inject card service into business service
        self._business_service.set_card_service(self._card_service)
        
        # 4. Inject card service into card action handler
        self._card_action_handler.set_card_service(self._card_service)
        
        # 5. Inject card service into long connection service
        self._long_connection_service.set_card_service(self._card_service)
        
        # 5.1. Inject long connection service into SDK card service (for client access)
        self._sdk_card_service.set_long_connection_service(self._long_connection_service)
        
        # 6. Inject business service into long connection service
        self._long_connection_service.set_business_service(self._business_service)
        
        # 7. Set card builders in SDK card service
        self._sdk_card_service.set_card_builders({
            'stock': StockCardBuilder(),
            'holdings': HoldingsCardBuilder(),
            'watchlist': WatchlistCardBuilder(),
            'price_alert': PriceAlertCardBuilder(),
            'menu': MenuCardBuilder(),
        })
        
        # 8. Set message handler (use MessageHandler instance, not function)
        message_handler = MessageHandler()
        self._long_connection_service.set_message_handler(message_handler)
        
        logger.info("All dependencies injected successfully")
    
    def _validate_setup(self) -> None:
        """Validate that all required dependencies are configured"""
        # Validate all services are created
        assert self._sdk_card_service is not None, "SDK card service not initialized"
        assert self._card_service is not None, "Application card service not initialized"
        assert self._business_service is not None, "Business service not initialized"
        assert self._long_connection_service is not None, "Long connection service not initialized"
        assert self._card_action_handler is not None, "Card action handler not initialized"
        
        # Validate dependencies are injected
        assert hasattr(self._card_service, '_sdk_card_service'), "Application card service missing SDK service"
        assert hasattr(self._business_service, '_card_service'), "Business service missing card service"
        assert hasattr(self._card_action_handler, '_business_service'), "Card action handler missing business service"
        
        logger.info("All dependencies validated successfully")
    
    @property
    def card_service(self) -> CardService:
        """Get configured application layer card service"""
        if not self._card_service:
            raise RuntimeError("Dependencies not setup. Call setup_all_dependencies() first.")
        return self._card_service
    
    @property
    def sdk_card_service(self) -> FeishuCardService:
        """Get configured SDK layer card service"""
        if not self._sdk_card_service:
            raise RuntimeError("Dependencies not setup. Call setup_all_dependencies() first.")
        return self._sdk_card_service
    
    @property
    def long_connection_service(self) -> FeishuLongConnectionService:
        """Get configured long connection service"""
        if not self._long_connection_service:
            raise RuntimeError("Dependencies not setup. Call setup_all_dependencies() first.")
        return self._long_connection_service
    
    @property
    def business_service(self) -> BusinessLogicService:
        """Get configured business service"""
        if not self._business_service:
            raise RuntimeError("Dependencies not setup. Call setup_all_dependencies() first.")
        return self._business_service


# Global injector instance
_injector: Optional[FeishuDependencyInjector] = None


def get_injector() -> FeishuDependencyInjector:
    """Get or create global injector instance"""
    global _injector
    if _injector is None:
        _injector = FeishuDependencyInjector()
        _injector.setup_all_dependencies()
    return _injector


def setup_feishu_dependencies() -> FeishuDependencyInjector:
    """Setup all Feishu dependencies (call at application startup)"""
    return get_injector()


__all__ = [
    'FeishuDependencyInjector',
    'get_injector',
    'setup_feishu_dependencies',
]
