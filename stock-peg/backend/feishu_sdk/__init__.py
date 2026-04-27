"""
Feishu SDK - Independent Feishu Integration Package

This package provides generic Feishu integration functionality that can be reused across projects.

Package Structure:
- core: Core services (client, card service, bot service, connection service)
- connection: WebSocket connection management
- message: Message handling and dispatching
- monitoring: Health monitoring and self-healing
- state: Card state management
- config: Configuration and interfaces
- plugins: Plugin system
"""

from feishu_sdk.core.client import (
    FeishuClient,
    FeishuClientError,
    ConfigurationError,
    APIError,
)

from feishu_sdk.core.card_service import FeishuCardService
from feishu_sdk.core.bot_service import FeishuBotService
from feishu_sdk.core.long_connection_service import (
    FeishuLongConnectionService,
    LARK_AVAILABLE,
)

__all__ = [
    # Client
    'FeishuClient',
    'FeishuClientError',
    'ConfigurationError',
    'APIError',
    
    # Services
    'FeishuCardService',
    'FeishuBotService',
    'FeishuLongConnectionService',
    'LARK_AVAILABLE',
]
