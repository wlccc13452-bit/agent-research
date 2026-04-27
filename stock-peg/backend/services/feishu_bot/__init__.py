"""
Feishu Bot - Stock Project Bot Implementation

Provides:
- Business logic (holdings, watchlist, price alerts)
- Card builders (stock, holdings, watchlist, price alert, menu)
- Event handlers
- Command mappings
- SDK layer imports for convenience
"""

# ===== Application Layer =====
from services.feishu_bot.business.stock_business_service import BusinessLogicService
from services.feishu_bot.cards import (
    BaseCardBuilder,
    StockCardBuilder,
    HoldingsCardBuilder,
    WatchlistCardBuilder,
    PriceAlertCardBuilder,
    MenuCardBuilder,
)
from services.feishu_bot.handlers import (
    save_chat_message,
    save_chat_message_async,
    FeishuBotService,  # 应用层的BotService
)
from services.feishu_bot.feishu_bot_commands import (
    COMMAND_MAPPING,
    MENU_COMMANDS,
    HEARTBEAT_INTERVAL,
    HEARTBEAT_TIMEOUT,
    HEARTBEAT_MONITOR_INTERVAL,
)

# Backward compatibility alias
StockBusinessService = BusinessLogicService

# ===== SDK Layer Imports =====
from feishu_sdk.core.client import (
    FeishuClient,
    FeishuClientError,
    ConfigurationError,
    APIError,
)
from feishu_sdk.core.card_service import FeishuCardService
# from feishu_sdk.core.bot_service import FeishuBotService  # 已在应用层定义
from feishu_sdk.core.long_connection_service import FeishuLongConnectionService
from feishu_sdk.connection.websocket_service import WebSocketConnectionService
from feishu_sdk.message.dispatcher import MessageDispatcher
from feishu_sdk.message.card_action_handler import CardActionHandler
from feishu_sdk.monitoring.heartbeat_monitor import HeartbeatMonitor
from feishu_sdk.monitoring.self_healing import SelfHealingManager
from feishu_sdk.state.card_state_manager import CardStateManager
from feishu_sdk.state.card_utils import (
    ensure_button_names,
    ensure_flat_action_values,
    disable_all_buttons,
    create_simple_status_card,
    create_error_card,
    create_disabled_card,
    create_loading_card,
    prepare_card_for_send,
    save_card_to_log,
)
from feishu_sdk.config.interfaces import (
    FeishuEventHandler,
    MessageContext,
    CardActionContext,
)
from feishu_sdk.config.protocols import (
    CardServiceProtocol,
    BusinessLogicServiceProtocol,
    CardActionServiceProtocol,
)

# ===== Service Instances =====
_card_service_instance = None

def get_card_service() -> FeishuCardService:
    """Get or create card service instance"""
    global _card_service_instance
    if _card_service_instance is None:
        _card_service_instance = FeishuCardService()
    return _card_service_instance

def get_long_connection_service() -> FeishuLongConnectionService:
    """Get long connection service instance"""
    from feishu_sdk.core.long_connection_service import feishu_long_connection_service as sdk_instance
    return sdk_instance

# Service instances
card_service = get_card_service()
feishu_long_connection_service = get_long_connection_service()
card_state_manager = CardStateManager()

# ===== Exports =====
__all__ = [
    # Application Layer
    'BusinessLogicService',
    'StockBusinessService',
    'BaseCardBuilder',
    'StockCardBuilder',
    'HoldingsCardBuilder',
    'WatchlistCardBuilder',
    'PriceAlertCardBuilder',
    'MenuCardBuilder',
    'save_chat_message',
    'save_chat_message_async',
    'COMMAND_MAPPING',
    'MENU_COMMANDS',
    'HEARTBEAT_INTERVAL',
    'HEARTBEAT_TIMEOUT',
    'HEARTBEAT_MONITOR_INTERVAL',
    
    # SDK Layer
    'FeishuClient',
    'FeishuClientError',
    'ConfigurationError',
    'APIError',
    'FeishuCardService',
    'FeishuBotService',
    'FeishuLongConnectionService',
    'WebSocketConnectionService',
    'MessageDispatcher',
    'CardActionHandler',
    'HeartbeatMonitor',
    'SelfHealingManager',
    'CardStateManager',
    'ensure_button_names',
    'ensure_flat_action_values',
    'disable_all_buttons',
    'create_simple_status_card',
    'create_error_card',
    'create_disabled_card',
    'create_loading_card',
    'prepare_card_for_send',
    'save_card_to_log',
    'FeishuEventHandler',
    'MessageContext',
    'CardActionContext',
    'CardServiceProtocol',
    'BusinessLogicServiceProtocol',
    'CardActionServiceProtocol',
    
    # Service Instances
    'card_service',
    'feishu_long_connection_service',
    'card_state_manager',
    'get_card_service',
    'get_long_connection_service',
]
